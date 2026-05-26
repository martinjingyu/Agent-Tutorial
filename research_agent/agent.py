from __future__ import annotations

import json
import sys
import uuid
from typing import Any

from .context import compact_messages, rough_tokens, tool_result_too_large
from .llm import LLMClient
from .paths import ensure_project_dirs
from .prompts import SELF_REVIEW_PROMPT, build_system_prompt
from .state import new_session_id, save_session
from .tools import load_builtin_tools, registry
from .ui import ConsoleUI


COMPACT_AFTER_FINAL_TOOL_COUNT = 8
"""If the number of tool results after the last final_response exceeds this,
the agent will compact before executing the next batch of tool calls."""


def _reasoning_content(message: Any) -> str | None:
    value = getattr(message, "reasoning_content", None)
    if value:
        return str(value)
    extra = getattr(message, "model_extra", None)
    if isinstance(extra, dict) and extra.get("reasoning_content"):
        return str(extra["reasoning_content"])
    return None


class ResearchAgent:
    def __init__(
        self,
        *,
        model: str | None = None,
        max_iterations: int = 24,
        context_threshold_tokens: int = 90000,
        self_review: bool = True,
        ui: ConsoleUI | None = None,
    ) -> None:
        ensure_project_dirs()
        load_builtin_tools()
        self.llm = LLMClient(model=model)
        self.max_iterations = max_iterations
        self.context_threshold_tokens = context_threshold_tokens
        self.self_review_enabled = self_review
        self.ui = ui or ConsoleUI(enabled=True)
        self.session_id = new_session_id()
        self.task_id = f"task_{uuid.uuid4().hex[:8]}"
        self.ui.session_start(self.session_id, self.task_id)

    def _skills_index(self) -> str:
        result = registry.dispatch("skills_list", {}, {"task_id": self.task_id})
        try:
            data = json.loads(result)
            lines = []
            for skill in data.get("skills", []):
                cat = f"{skill.get('category')}/" if skill.get("category") else ""
                lines.append(f"- {cat}{skill.get('name')}: {skill.get('description')}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _pre_loop_compact_review(
        self,
        messages: list[dict[str, Any]],
        user_message: str,
        system_prompt: str,
    ) -> list[dict[str, Any]] | None:
        """Review conversation history before the agent loop starts.

        Uses the LLM to determine whether the conversation has moved to a new,
        independent task phase. If so, compact the history to keep context focused.

        Returns compacted messages if compaction is needed, None otherwise.

        The LLM is asked to judge whether the upcoming user_message represents
        a shift to a new independent task (vs. continuing the same task).
        """
        # Only review if there is substantial history to consider
        if len(messages) < 6:
            self.ui.event("compact-review", "skipped: too few messages")
            return None

        # Build a compact review prompt for the LLM
        # We send a condensed view of the conversation: the last assistant response
        # (if any) and the new user message, plus a summary of what came before.
        review_prompt = f"""You are a context management assistant. Your job is to decide whether to compact the conversation history.

        ## Current situation
        The agent has an existing conversation history and is about to process a new user message.

        ## Decision criteria
        Compact the history ONLY if the new user message represents a shift to a **new, independent task** at a different level or domain from the previous conversation. Examples:

        - Previous task: "Research Stanford CS program" → New task: "Now research MIT's program" → **COMPACT** (independent tasks)
        - Previous task: "Find candidate A's GitHub" → New task: "Now verify candidate B's LinkedIn" → **COMPACT** (different candidate)
        - Previous task: "Research school programs" → New task: "Diagnose why the agent restarted" → **COMPACT** (different domain)
        - Previous task: "Browse page X" → New task: "Continue browsing page X for more details" → **DO NOT COMPACT** (same task)
        - Previous task: "Save report" → New task: "Fix a typo in the report" → **DO NOT COMPACT** (same task, refinement)
        - Previous task: "Research program A" → New task: "Here are more details about program A" → **DO NOT COMPACT** (same task)

        ## Conversation summary (earlier part)
        {json.dumps(messages[:-4], ensure_ascii=False, default=str)[:8000]}

        ## Recent messages
        {json.dumps(messages[-4:], ensure_ascii=False, default=str)[:4000]}

        ## New user message
        {user_message[:2000]}

        ## Your response
        Answer with a JSON object only, no other text:
        {{"should_compact": true/false, "reason": "brief reason", "focus": "what to preserve in compaction"}}
        """
        try:
            self.ui.event("compact-review", "checking if conversation has moved to a new task")
            result = self.llm.complete_text(review_prompt).strip()
            # Extract JSON from the response
            if "{" in result:
                json_str = result[result.index("{"):]
                if "}" in json_str:
                    json_str = json_str[:json_str.rindex("}") + 1]
                    decision = json.loads(json_str)
                    if decision.get("should_compact"):
                        focus = decision.get("focus", user_message)
                        self.ui.compact(
                            f"pre-loop: {decision.get('reason', 'new independent task')}"
                        )
                        compacted = compact_messages(
                            messages, self.llm, focus=focus
                        )
                        return self._repair_tool_sequences(compacted)
                    else:
                        self.ui.event(
                            "compact-review",
                            f"no compact needed: {decision.get('reason', 'same task')}",
                        )
        except Exception as e:
            # If LLM call fails, fall through silently — no compaction is safe
            self.ui.event("compact-review", f"skipped ({type(e).__name__})")
        return None

    def _pre_action_compact_check(
        self, messages: list[dict[str, Any]], system_prompt: str, user_message: str
    ) -> list[dict[str, Any]] | None:
        """Check whether to compact before executing the next batch of tool calls.

        Returns compacted messages if compaction is needed, None otherwise.

        Compaction is triggered when:
        1. There are more than COMPACT_AFTER_FINAL_TOOL_COUNT tool results
           accumulated after the last final_response (respond_to_user).
        2. The token count is approaching but has not yet exceeded the threshold
           (above 60% of context_threshold_tokens).
        """
        # Count tool results after the most recent final_response
        tool_count = 0
        for msg in reversed(messages):
            if msg.get("role") == "tool":
                tool_count += 1
            elif msg.get("role") == "assistant" and msg.get("content", "").strip():
                # Found a non-empty assistant message — likely a final response
                # or a summary. Stop counting backward.
                break

        if tool_count < COMPACT_AFTER_FINAL_TOOL_COUNT:
            return None

        # Also check token pressure
        token_count = rough_tokens(messages, system_prompt)
        threshold = self.context_threshold_tokens
        if token_count < threshold * 0.6:
            # Token count is still comfortable; let the threshold-based
            # compaction handle it if it grows further.
            return None

        self.ui.compact(
            f"pre-action: {tool_count} tool results after last final_response, "
            f"{token_count}/{threshold} tokens"
        )
        compacted = compact_messages(messages, self.llm, focus=user_message)
        return self._repair_tool_sequences(compacted)

    def run(self, user_message: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        messages = self._repair_tool_sequences(list(history or []))
        system_prompt = build_system_prompt(self._skills_index())

        # ── Pre-loop compact review ──────────────────────────────────────
        # Before adding the new user message and starting the agent loop,
        # review the conversation history to see if we've moved to a new
        # independent task. If so, compact the history.
        if messages:
            compacted = self._pre_loop_compact_review(
                messages, user_message, system_prompt
            )
            if compacted is not None:
                messages = compacted
                system_prompt = build_system_prompt(self._skills_index())
        # ─────────────────────────────────────────────────────────────────

        messages.append({"role": "user", "content": user_message})
        final_text = ""

        for iteration in range(1, self.max_iterations + 1):
            if rough_tokens(messages, system_prompt) > self.context_threshold_tokens:
                self.ui.compact("context threshold exceeded")
                messages = compact_messages(messages, self.llm, focus=user_message)
                messages = self._repair_tool_sequences(messages)
                system_prompt = build_system_prompt(self._skills_index())

            messages = self._repair_tool_sequences(messages)
            api_messages = [{"role": "system", "content": system_prompt}, *messages]
            self.ui.model_start(iteration)
            try:
                response = self.llm.chat(api_messages, registry.definitions())
            except KeyboardInterrupt:
                correction = self._interrupt_correction()
                if correction:
                    messages.append({"role": "user", "content": correction})
                    continue
                final_text = "Interrupted by user. Session state was saved."
                messages.append({"role": "assistant", "content": final_text})
                self.ui.final()
                break
            assistant = response.choices[0].message
            assistant_msg = {"role": "assistant", "content": assistant.content or ""}
            reasoning = _reasoning_content(assistant)
            if reasoning:
                assistant_msg["reasoning_content"] = reasoning

            tool_calls = getattr(assistant, "tool_calls", None) or []
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in tool_calls
                ]
                messages.append(assistant_msg)

                # ── Pre-action compact check ──────────────────────────────
                compacted = self._pre_action_compact_check(
                    messages, system_prompt, user_message
                )
                if compacted is not None:
                    messages = compacted
                    system_prompt = build_system_prompt(self._skills_index())
                # ──────────────────────────────────────────────────────────

                compact_focus = None
                interrupted = False
                for index, tc in enumerate(tool_calls):
                    if final_text:
                        args = {}
                        result = json.dumps(
                            {
                                "success": True,
                                "message": "Skipped because final response was already captured.",
                            },
                            ensure_ascii=False,
                        )
                    else:
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                            if not isinstance(args, dict):
                                args = {}
                        except json.JSONDecodeError:
                            args = {}
                        runtime = {
                            "task_id": self.task_id,
                            "session_id": self.session_id,
                            "user_task": user_message,
                        }
                        self.ui.tool_start(tc.function.name, args)
                        try:
                            result = registry.dispatch(tc.function.name, args, runtime)
                        except KeyboardInterrupt:
                            result = json.dumps(
                                {
                                    "success": False,
                                    "error": "Tool interrupted by user before completion.",
                                },
                                ensure_ascii=False,
                            )
                            interrupted = True
                        if runtime.get("final_response") is not None:
                            final_text = str(runtime.get("final_response") or "")
                        if runtime.get("compact_requested"):
                            compact_focus = str(runtime["compact_requested"])
                        if runtime.get("_pending_restart"):
                            self._pending_restart = runtime["_pending_restart"]
                            self._pending_restart_prompt = runtime.get("_pending_restart_prompt")
                    result = tool_result_too_large(result)
                    self.ui.tool_done(tc.function.name, result)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": result,
                        }
                    )
                    if interrupted:
                        for skipped in tool_calls[index + 1 :]:
                            skipped_result = json.dumps(
                                {
                                    "success": False,
                                    "error": "Tool skipped because the user interrupted this action batch.",
                                },
                                ensure_ascii=False,
                            )
                            self.ui.tool_done(skipped.function.name, skipped_result)
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": skipped.id,
                                    "name": skipped.function.name,
                                    "content": skipped_result,
                                }
                            )
                        correction = self._interrupt_correction()
                        if correction:
                            messages.append({"role": "user", "content": correction})
                        else:
                            final_text = "Interrupted by user. Session state was saved."
                            messages.append({"role": "assistant", "content": final_text})
                            self.ui.final()
                        break
                if interrupted:
                    if final_text:
                        break
                    continue
                if compact_focus:
                    self.ui.compact(compact_focus)
                    messages = compact_messages(messages, self.llm, focus=compact_focus)
                    messages = self._repair_tool_sequences(messages)
                    system_prompt = build_system_prompt(self._skills_index())
                if final_text:
                    self.ui.final()
                    break
                continue

            final_text = assistant.content or ""
            self.ui.final()
            messages.append(assistant_msg)
            break

        if not final_text:
            final_text = self._fallback_final_response(messages, user_message)
            messages.append({"role": "assistant", "content": final_text})
            self.ui.final()

        messages = self._repair_tool_sequences(messages)
        session_path = save_session(self.session_id, messages)
        self.ui.saved(str(session_path))
        if final_text and self.self_review_enabled:
            self._self_review(messages)

        # ── Self-restart check ──────────────────────────────────────────
        # If the agent modified its own source code during this run,
        # it should have set self._pending_restart. If so, signal the
        # Guardian (parent process) to restart us.
        if getattr(self, "_pending_restart", None):
            from .guardian import request_restart

            request_restart(
                changes=self._pending_restart,
                session_id=self.session_id,
                resume_path=str(session_path),
                next_prompt=self._pending_restart_prompt,
            )
            # Flush output so the user sees the final message before exit
            sys.stdout.flush()
            sys.exit(42)  # RESTART_EXIT_CODE
        # ────────────────────────────────────────────────────────────────

        return {
            "session_id": self.session_id,
            "session_path": str(session_path),
            "final": final_text,
            "messages": messages,
        }

    def _interrupt_correction(self) -> str | None:
        self.ui.interrupt()
        try:
            value = input("\nCorrection> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not value or value in {"/stop", "/exit", "/quit"}:
            return None
        return (
            "[USER INTERRUPT CORRECTION]\n"
            "The previous action path looked wrong or should be adjusted. "
            "Follow this correction for the remaining work:\n"
            f"{value}"
        )

    def _fallback_final_response(self, messages: list[dict[str, Any]], user_message: str) -> str:
        prompt = f"""The agent reached its iteration limit without a final response.

Write a concise user-facing status update in the user's language.
Include what was done, any files saved, and what remains. Do not claim completion if no report was saved.

Original user request:
{user_message}

Recent conversation JSON:
{json.dumps(messages[-16:], ensure_ascii=False, default=str)}
"""
        try:
            return self.llm.complete_text(prompt).strip() or "I stopped after reaching the iteration limit before producing a final answer."
        except Exception:
            return "I stopped after reaching the iteration limit before producing a final answer."

    def _repair_tool_sequences(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        repaired: list[dict[str, Any]] = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg.get("role") == "tool":
                repaired.append(
                    {
                        "role": "user",
                        "content": f"[Recovered orphan tool result from {msg.get('name', 'tool')}]: {str(msg.get('content', ''))[:2000]}",
                    }
                )
                i += 1
                continue

            repaired.append(msg)
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                expected = [
                    tc.get("id")
                    for tc in msg.get("tool_calls", [])
                    if isinstance(tc, dict) and tc.get("id")
                ]
                seen: set[str] = set()
                j = i + 1
                while j < len(messages) and messages[j].get("role") == "tool":
                    tool_msg = messages[j]
                    tcid = tool_msg.get("tool_call_id")
                    if tcid in expected and tcid not in seen:
                        repaired.append(tool_msg)
                        seen.add(tcid)
                    else:
                        repaired.append(
                            {
                                "role": "user",
                                "content": f"[Recovered orphan tool result from {tool_msg.get('name', 'tool')}]: {str(tool_msg.get('content', ''))[:2000]}",
                            }
                        )
                    j += 1
                for tcid in expected:
                    if tcid not in seen:
                        tool_name = "missing_tool_result"
                        for tc in msg.get("tool_calls", []):
                            if isinstance(tc, dict) and tc.get("id") == tcid:
                                function = tc.get("function") or {}
                                if isinstance(function, dict) and function.get("name"):
                                    tool_name = str(function["name"])
                                break
                        repaired.append(
                            {
                                "role": "tool",
                                "tool_call_id": tcid,
                                "name": tool_name,
                                "content": json.dumps(
                                    {
                                        "success": False,
                                        "error": "Recovered missing tool result from a previous interrupted run.",
                                    },
                                    ensure_ascii=False,
                                ),
                            }
                        )
                i = j
                continue
            i += 1
        return repaired

    def _self_review(self, completed_messages: list[dict[str, Any]]) -> None:
        self.ui.self_review_start()
        allowed = {"memory", "skills_list", "skill_view", "skill_manage"}
        tools = [tool for tool in registry.definitions() if tool["function"]["name"] in allowed]
        messages = [
            {"role": "system", "content": build_system_prompt(self._skills_index())},
            {
                "role": "user",
                "content": (
                    "Conversation transcript for self-review:\n\n"
                    + self._review_transcript(completed_messages)
                    + "\n\n"
                    + SELF_REVIEW_PROMPT
                ),
            },
        ]
        for _ in range(6):
            response = self.llm.chat(messages, tools)
            assistant = response.choices[0].message
            tool_calls = getattr(assistant, "tool_calls", None) or []
            assistant_msg = {"role": "assistant", "content": assistant.content or ""}
            reasoning = _reasoning_content(assistant)
            if reasoning:
                assistant_msg["reasoning_content"] = reasoning
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
                    }
                    for tc in tool_calls
                ]
                messages.append(assistant_msg)
                for tc in tool_calls:
                    if tc.function.name not in allowed:
                        result = json.dumps({"success": False, "error": "tool not allowed in self-review"})
                    else:
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                        except json.JSONDecodeError:
                            args = {}
                        result = registry.dispatch(tc.function.name, args, {"task_id": self.task_id, "session_id": self.session_id})
                    messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": result})
                continue
            break
        self.ui.self_review_done()

    def _review_transcript(self, messages: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for msg in messages[-36:]:
            role = msg.get("role", "")
            if role == "assistant" and msg.get("tool_calls"):
                calls = []
                for tc in msg.get("tool_calls", []):
                    fn = (tc.get("function") or {}).get("name", "?")
                    calls.append(fn)
                lines.append(f"[tool calls: {', '.join(calls)}]")
            elif role == "assistant":
                content = (msg.get("content") or "")[:200]
                if content:
                    lines.append(content)
            elif role == "user":
                content = (msg.get("content") or "")[:200]
                if content and not content.startswith("[CONTEXT COMPACTION"):
                    lines.append(f"user: {content}")
            elif role == "tool":
                name = msg.get("name", "?")
                content = (msg.get("content") or "")[:120]
                lines.append(f"  → {name}: {content}")
        return "\n".join(lines)
