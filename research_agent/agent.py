from __future__ import annotations

import json
import re
import sys
import time
import uuid
from typing import Any, Callable
from pathlib import Path

from .context import compact_messages, rough_tokens
from .llm import LLMClient
from .paths import SESSIONS_DIR, ensure_project_dirs, set_session_roots, set_shared_roots, set_workspace_root
from .prompts import build_system_prompt
from .self_review import trigger_self_review
from .state import new_session_id, save_session
from .text_clean import clean_text
from .tools import load_builtin_tools, registry as _global_registry
from .tools.registry import ToolRegistry
from .ui import ConsoleUI


def _consume_notifications() -> list[dict]:
    """Safely consume pending kanban and background-job notifications (no-op
    for whichever of those isn't loaded)."""
    messages: list[dict] = []
    try:
        from .tools.kanban import consume_pending_notifications
        messages.extend(consume_pending_notifications())
    except Exception:
        pass
    try:
        from .tools.background import consume_pending_background_notifications
        messages.extend(consume_pending_background_notifications())
    except Exception:
        pass
    return messages


COMPACT_AFTER_FINAL_TOOL_COUNT = 8
"""If the number of tool results after the last final_response exceeds this,
the agent will compact before executing the next batch of tool calls."""


def _user_message_text(user_message: Any, limit: int | None = None) -> str:
    """Text-only rendering of a run() user_message, which may be a plain string or a
    chat-completions-style multimodal list ([{"type": "text", ...}, {"type":
    "image_url", ...}]) -- for previews/logging/fallbacks that need a string and
    should not choke on or garble the image parts."""
    if isinstance(user_message, str):
        text = user_message
    elif isinstance(user_message, list):
        texts = [
            part.get("text", "")
            for part in user_message
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        has_images = any(
            isinstance(part, dict) and part.get("type") == "image_url" for part in user_message
        )
        text = "\n".join(texts) + (" [+images]" if has_images else "")
    else:
        text = str(user_message)
    return text[:limit] if limit is not None else text


def _prepend_text_to_user_message(user_message: Any, text: str) -> Any:
    """Prepends `text` ahead of a run() user_message, preserving it whether it's a
    plain string or a multimodal content list (image parts must never be routed
    through string formatting/concatenation, which would silently mangle them)."""
    if isinstance(user_message, list):
        return [{"type": "text", "text": text}] + user_message
    return f"{text}\n\n---\n{user_message}" if user_message.strip() else text


def _display_model_name(model: str, provider: str) -> str:
    """Distinguish Codex-quota calls (free) from token-billed API calls with the
    same underlying model name, e.g. "gpt-5.5" via codex -> "codex-5.5"."""
    if provider == "codex" and model.startswith("gpt-"):
        return "codex-" + model[len("gpt-"):]
    return model


def _log_usage(response: Any, model: str, provider: str, session_id: str) -> None:
    """Append one line to sessions/usage_log.jsonl with token counts from this LLM call."""
    try:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        in_tok  = getattr(usage, "prompt_tokens",     None) or getattr(usage, "input_tokens",  0)
        out_tok = getattr(usage, "completion_tokens", None) or getattr(usage, "output_tokens", 0)
        if not in_tok and not out_tok:
            return
        from datetime import datetime
        entry = json.dumps({
            "ts":         datetime.now().isoformat(timespec="seconds"),
            "session_id": session_id,
            "model":      _display_model_name(model, provider),
            "provider":   provider,
            "in":         in_tok,
            "out":        out_tok,
        }, ensure_ascii=False)
        log_path = SESSIONS_DIR / "usage_log.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass

MAX_TOOL_RESULT_CHARS = 8_000
SPILL_PREVIEW_CHARS = 600
SNAPSHOT_TOOL_NAMES = {"browser_navigate", "browser_snapshot"}
READ_FILE_TOOL_NAMES = {"read_file"}
RECOVERABLE_FILE_WRITE_TOOL_NAMES = {"write_file", "append_file"}
NOTES_TOOL_NAME = "save_research_notes"
PREVIOUS_SNAPSHOT_LIMIT = 2_000
PREVIOUS_READ_FILE_LIMIT = 500
CONTINUATION_MAX_ITERS = 30
TRAJECTORY_COMPRESS_THRESHOLD = 180_000
COMPACT_MIN_GAP = 3
"""Minimum iterations between any two automatic compactions (pre-action check,
trajectory/token threshold check). Prevents different triggers from firing back
to back and burning extra LLM calls on the same few iterations."""
FINISH_BLOCKED_TOOLS = {
    "bing_search",
    "google_search",
    "baidu_search",
    "reddit_search",
    "browser_navigate",
    "browser_snapshot",
    "browser_click",
    "browser_type",
    "browser_press_key",
    "browser_scroll",
    "browser_screenshot",
    "browser_back",
    "view_image",
}
FINISH_REMINDER = (
    "Out of iteration budget for this turn. Search/browsing tools are blocked now, so "
    "stop exploring. If there's a genuinely important file still to write, write it -- "
    "but don't rush to force-complete work you haven't actually done, and don't "
    "fabricate a result to make it look finished. Call respond_to_user with an honest "
    "status: what's actually done and verified, and if the task isn't finished, what's "
    "still left. This isn't necessarily a hard stop -- if you're in an ongoing "
    "conversation, whoever you're working for can just tell you to continue next time."
)


def _decode_json_string_prefix(fragment: str) -> tuple[str | None, int]:
    """Decode a JSON string body that may be cut off near the end."""
    max_trim = min(len(fragment), 128)
    for trim in range(max_trim + 1):
        candidate = fragment if trim == 0 else fragment[:-trim]
        try:
            return json.loads(f'"{candidate}"'), trim
        except json.JSONDecodeError:
            continue
    return None, 0


def _extract_json_string_value(raw: str, key: str) -> tuple[str | None, bool, int]:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*"', raw)
    if not match:
        return None, False, 0

    start = match.end()
    escaped = False
    for pos in range(start, len(raw)):
        ch = raw[pos]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            value, trimmed = _decode_json_string_prefix(raw[start:pos])
            return value, True, trimmed

    value, trimmed = _decode_json_string_prefix(raw[start:])
    return value, False, trimmed


def _recover_file_write_args(tool_name: str, raw_args: str, exc: json.JSONDecodeError) -> dict[str, Any] | None:
    """Recover write_file/append_file args when a long content string was truncated."""
    if tool_name not in RECOVERABLE_FILE_WRITE_TOOL_NAMES or not raw_args:
        return None

    path, path_closed, _ = _extract_json_string_value(raw_args, "path")
    content, content_closed, trimmed = _extract_json_string_value(raw_args, "content")
    if not path or content is None or content == "":
        return None

    return {
        "path": path,
        "content": content,
        "_recovered_truncated_tool_arguments": True,
        "_recovery_warning": (
            f"{tool_name} arguments were invalid/truncated at char {exc.pos}; "
            f"recovered {len(content)} characters of content and wrote them. "
            "Continue from the saved file tail with append_file in smaller chunks."
        ),
        "_content_string_closed": content_closed,
    }


def _add_recovery_metadata(result: str, args: dict[str, Any]) -> str:
    if not args.get("_recovered_truncated_tool_arguments"):
        return result
    try:
        data = json.loads(result)
        if isinstance(data, dict):
            data["recovered_truncated_arguments"] = True
            data["content_may_be_incomplete"] = not bool(args.get("_content_string_closed"))
            data["warning"] = "Recovered partial content from truncated file-write arguments. Continue with append_file."
            return json.dumps(data, ensure_ascii=False)
    except Exception:
        pass
    return result


def _reasoning_content(message: Any) -> str | None:
    value = getattr(message, "reasoning_content", None)
    if value:
        return str(value)
    extra = getattr(message, "model_extra", None)
    if isinstance(extra, dict) and extra.get("reasoning_content"):
        return str(extra["reasoning_content"])
    return None


class GeneralAgent:
    def __init__(
        self,
        *,
        model: str | None = None,
        provider: str | None = None,
        reasoning_effort: str | None = None,
        max_iterations: int = 24,
        context_threshold_tokens: int = 90000,
        auto_compact: bool = True,
        semantic_review: bool = False,
        self_review: bool = False,
        ui: ConsoleUI | None = None,
        live_cache_path: str | Path | None = None,
        live_cache_metadata: dict[str, Any] | None = None,
        # Extension points for downstream pipelines
        registry: ToolRegistry | None = None,
        finish_tools: set[str] | frozenset[str] | None = None,
        candidate_folder: str | Path | None = None,
        session_path: str | Path | None = None,
        session_id: str | None = None,
        sub_agent: bool = False,
        agent_role: str | None = None,
        cancel_check: Callable[[], bool] | None = None,
        workspace_root: str | Path | None = None,
        shared_roots: list[str | Path] | None = None,
        extra_runtime: dict[str, Any] | None = None,
    ) -> None:
        if workspace_root is not None:
            set_workspace_root(workspace_root)
        # Always set (even to clear it), unlike workspace_root above: ThreadPoolExecutor
        # reuses threads across turns/meetings, and a stale shared_roots override left
        # over from a previous construction on this thread must not leak forward.
        set_shared_roots(shared_roots)
        ensure_project_dirs()
        load_builtin_tools()
        self.llm = LLMClient(model=model, provider=provider, reasoning_effort=reasoning_effort)
        self.max_iterations = max_iterations
        self.context_threshold_tokens = context_threshold_tokens
        self.auto_compact = auto_compact
        # Off by default: this does an extra LLM call on every single turn just to
        # decide whether to compact, which adds latency/cost that most turns don't need.
        # The threshold-based triggers (token/char count) already catch runaway growth.
        self.semantic_review = semantic_review
        self.self_review_enabled = self_review
        self.ui = ui or ConsoleUI(enabled=True)
        self.session_id = session_id or new_session_id()
        self._sub_agent = sub_agent
        self.agent_role = agent_role or ("sub_agent" if sub_agent else "main")
        self.task_id = f"task_{uuid.uuid4().hex[:8]}"
        self._spill_dir = SESSIONS_DIR / ".tool_cache" / self.session_id
        self._spill_counter = 0
        # Own tool-result spill cache is always safe to read back, regardless of
        # workspace_root/shared_roots -- see set_session_roots docstring.
        set_session_roots([self._spill_dir])
        self._last_compact_iter = 0
        self._live_cache_path = Path(live_cache_path) if live_cache_path else None
        self._live_cache_metadata = live_cache_metadata or {}
        self.ui.session_start(self.session_id, self.task_id)
        self._pending_restart: list[str] | None = None
        self._pending_restart_prompt: str | None = None
        load_builtin_tools()
        self._registry = registry if registry is not None else _global_registry
        self._finish_tools: frozenset[str] = frozenset(finish_tools) if finish_tools else frozenset()
        self._candidate_folder = str(candidate_folder) if candidate_folder else None
        self._session_path = Path(session_path) if session_path else None
        self._cancel_check = cancel_check
        self._system_prompt_override: str | None = None
        # Free-form extra keys merged into the per-run runtime dict (agent.py's run()
        # builds a fresh one every call) -- lets embedding projects thread caller-specific
        # context (e.g. a role's memory file path, an explicit skill allowlist) through to
        # tool handlers via the runtime dict, the same way task_id/agent_role already are,
        # without needing a new constructor param per use case.
        self._extra_runtime: dict[str, Any] = dict(extra_runtime) if extra_runtime else {}

    def _cancel_requested(self) -> bool:
        if not self._cancel_check:
            return False
        try:
            return bool(self._cancel_check())
        except Exception:
            return False

    def _skills_index(self) -> str:
        if "skills_list" not in self._registry.names:
            return ""
        result = self._registry.dispatch(
            "skills_list",
            {},
            {"task_id": self.task_id, "agent_role": self.agent_role},
        )
        try:
            data = json.loads(result)
            lines = []
            for skill in data.get("skills", []):
                cat = f"{skill.get('category')}/" if skill.get("category") else ""
                audience = skill.get("audience")
                audience_text = f" [audience: {audience}]" if audience else ""
                lines.append(f"- {cat}{skill.get('name')}{audience_text}: {skill.get('description')}")
            return "\n".join(lines)
        except Exception:
            return ""

    def _build_system_prompt(self) -> str:
        # A caller-supplied system_prompt (run(..., system_prompt=...)) is an identity
        # override, not just a first-turn default -- every internal rebuild (post-compact,
        # fallback-finish) must keep honoring it for the rest of this run, otherwise a long
        # run silently drops the caller's identity/instructions and falls back to this
        # library's generic default prompt mid-conversation.
        if self._system_prompt_override is not None:
            return self._system_prompt_override
        return build_system_prompt(self._skills_index(), agent_role=self.agent_role)

    def _pre_loop_compact_review(
        self,
        messages: list[dict[str, Any]],
        user_message: str | list[dict[str, Any]],
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
        {_user_message_text(user_message, 2000)}

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
                        focus = decision.get("focus") or _user_message_text(user_message, 200)
                        self.ui.compact(
                            f"pre-loop: {decision.get('reason', 'new independent task')}"
                        )
                        compacted = compact_messages(
                            messages, self.llm, system_prompt, self._registry, focus=focus
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

        The last message may be the assistant message that just emitted tool_calls.
        That message is a pending protocol boundary: it must remain verbatim and
        must not be "repaired" with synthetic tool results before the real tools
        execute.

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
        pending_tool_call_msg = (
            messages[-1]
            if messages
            and messages[-1].get("role") == "assistant"
            and messages[-1].get("tool_calls")
            else None
        )
        if pending_tool_call_msg is not None:
            prefix = self._repair_tool_sequences(messages[:-1])
            compacted_prefix = compact_messages(
                prefix, self.llm, system_prompt, self._registry, focus=user_message
            )
            return self._repair_tool_sequences(compacted_prefix) + [pending_tool_call_msg]

        compacted = compact_messages(
            messages, self.llm, system_prompt, self._registry, focus=user_message
        )
        return self._repair_tool_sequences(compacted)

    def run(
        self,
        user_message: str | list[dict[str, Any]],
        history: list[dict[str, Any]] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        # user_message is normally a plain string, but callers may instead pass a
        # chat-completions-style multimodal content list ([{"type": "text", ...},
        # {"type": "image_url", ...}]) when the turn needs to show the model an
        # image -- e.g. Agent-Meeting's visual-reviewer participant. Every place
        # below that touches user_message as a string goes through
        # _user_message_text()/_prepend_text_to_user_message() so it degrades to a
        # text-only view instead of crashing or mangling the image parts.

        # Consume any pending kanban notifications and prepend to current message
        # so the agent wakes up aware of board completion without a second user turn.
        pending = _consume_notifications()
        if pending:
            notif_text = "\n\n".join(m["content"] for m in pending)
            user_message = _prepend_text_to_user_message(user_message, notif_text)

        messages = self._repair_tool_sequences(list(history or []))
        self._system_prompt_override = system_prompt
        system_prompt = system_prompt or self._build_system_prompt()
        # Iteration numbers are per-run (start at 1 below), so the gap throttle
        # must reset per run too, otherwise a compaction late in a previous run
        # can suppress compaction early in this one.
        self._last_compact_iter = 0

        # ── Pre-loop compact review (semantic, opt-in) ─────────────────────
        if self.auto_compact and self.semantic_review and messages:
            compacted = self._pre_loop_compact_review(
                messages, user_message, system_prompt
            )
            if compacted is not None:
                messages = compacted
                system_prompt = self._build_system_prompt()
                self._last_compact_iter = 0
        # ─────────────────────────────────────────────────────────────────

        messages.append({"role": "user", "content": user_message})
        self._write_live_cache("running", messages, final_text="")
        final_text = ""
        # Single runtime dict shared across ALL tool calls in this run.
        # Tools can store state here (e.g. meeting_id) and it will persist.
        self._runtime: dict[str, Any] = {
            "task_id":   self.task_id,
            "session_id": self.session_id,
            "agent_role": self.agent_role,
            "user_task": user_message,
            **({"candidate_folder": self._candidate_folder} if self._candidate_folder else {}),
            **self._extra_runtime,
        }

        for iteration in range(1, self.max_iterations + 1):
            if self._cancel_requested():
                final_text = "Interrupted by user. Session state was saved."
                messages.append({"role": "assistant", "content": final_text})
                self._write_live_cache("interrupted", messages, final_text=final_text)
                self.ui.final()
                break

            # ── Trajectory/token threshold compaction (single gatekeeper) ──────
            # Both size signals are checked together, behind one shared cooldown,
            # so a single oversized turn can't trigger two back-to-back compactions.
            if self.auto_compact and iteration - self._last_compact_iter >= COMPACT_MIN_GAP:
                over_chars = self._estimate_message_chars(messages) >= TRAJECTORY_COMPRESS_THRESHOLD
                over_tokens = rough_tokens(messages, system_prompt) > self.context_threshold_tokens
                if over_chars or over_tokens:
                    reason = (
                        f"trajectory exceeded {TRAJECTORY_COMPRESS_THRESHOLD:,} chars"
                        if over_chars
                        else "context threshold exceeded"
                    )
                    self.ui.compact(reason)
                    messages = compact_messages(
                        messages, self.llm, system_prompt, self._registry, focus=user_message,
                        protect_last=18 if over_chars else 12,
                    )
                    messages = self._repair_tool_sequences(messages)
                    system_prompt = self._build_system_prompt()
                    self._last_compact_iter = iteration
            # ─────────────────────────────────────────────────────────────────

            messages = self._repair_tool_sequences(messages)
            api_messages = [{"role": "system", "content": system_prompt}, *messages]
            self.ui.model_start(iteration)
            try:
                response = self.llm.chat(api_messages, self._registry.definitions())
                _log_usage(response, self.llm.model, self.llm.provider, self.session_id)
            except KeyboardInterrupt:
                correction = self._interrupt_correction()
                if correction:
                    messages.append({"role": "user", "content": correction})
                    self._write_live_cache("running", messages, final_text="")
                    continue
                final_text = "Interrupted by user. Session state was saved."
                messages.append({"role": "assistant", "content": final_text})
                self._write_live_cache("interrupted", messages, final_text=final_text)
                self.ui.final()
                break
            assistant = response.choices[0].message
            if self._cancel_requested():
                final_text = "Interrupted by user. Session state was saved."
                messages.append({"role": "assistant", "content": final_text})
                self._write_live_cache("interrupted", messages, final_text=final_text)
                self.ui.final()
                break
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
                self._write_live_cache("running", messages, final_text=final_text)

                # ── Pre-action compact check ──────────────────────────────
                if self.auto_compact and iteration - self._last_compact_iter >= COMPACT_MIN_GAP:
                    compacted = self._pre_action_compact_check(
                        messages, system_prompt, user_message
                    )
                    if compacted is not None:
                        messages = compacted
                        system_prompt = self._build_system_prompt()
                        self._last_compact_iter = iteration
                # ──────────────────────────────────────────────────────────

                compact_focus = None
                interrupted = False
                for index, tc in enumerate(tool_calls):
                    if self._cancel_requested():
                        args = {}
                        result = json.dumps(
                            {"success": False, "error": "Tool skipped because the user interrupted this run."},
                            ensure_ascii=False,
                        )
                        interrupted = True
                    elif final_text:
                        args = {}
                        result = json.dumps(
                            {
                                "success": True,
                                "message": "Skipped because final response was already captured.",
                            },
                            ensure_ascii=False,
                        )
                    else:
                        recovered_args = False
                        try:
                            args = json.loads(tc.function.arguments or "{}")
                            if not isinstance(args, dict):
                                self.ui.event(
                                    "tool-args",
                                    f"{tc.function.name} arguments were not a JSON object; using empty arguments",
                                )
                                args = {}
                        except json.JSONDecodeError as exc:
                            recovered = _recover_file_write_args(
                                tc.function.name,
                                tc.function.arguments or "",
                                exc,
                            )
                            if recovered is not None:
                                args = recovered
                                recovered_args = True
                                self.ui.event("tool-args", str(args.get("_recovery_warning")))
                            else:
                                self.ui.event(
                                    "tool-args",
                                    f"{tc.function.name} arguments JSON parse failed at char {exc.pos}: {exc.msg}",
                                )
                                args = {}
                        runtime = self._runtime
                        self.ui.tool_start(tc.function.name, args)
                        try:
                            result = self._registry.dispatch(tc.function.name, args, runtime)
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
                        if self._finish_tools and tc.function.name in self._finish_tools and not final_text:
                            final_text = result or "Task completed."
                        if runtime.get("compact_requested"):
                            compact_focus = str(runtime["compact_requested"])
                        if runtime.get("_pending_restart"):
                            self._pending_restart = runtime["_pending_restart"]
                            if runtime.get("_pending_restart_prompt"):
                                self._pending_restart_prompt = runtime["_pending_restart_prompt"]
                        if recovered_args:
                            result = _add_recovery_metadata(result, args)
                    result = self._process_tool_result(result, tc.function.name, args)
                    self.ui.tool_done(tc.function.name, result)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": result,
                        }
                    )
                    self._write_live_cache("running", messages, final_text=final_text)
                    if tc.function.name in SNAPSHOT_TOOL_NAMES:
                        self._compress_previous_snapshot(messages)
                    elif tc.function.name == NOTES_TOOL_NAME:
                        self._replace_previous_result_with_notes(messages, args.get("notes", ""))
                        self._compress_old_read_files(messages)
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
                            self._write_live_cache("running", messages, final_text=final_text)
                        correction = self._interrupt_correction()
                        if correction:
                            messages.append({"role": "user", "content": correction})
                            self._write_live_cache("running", messages, final_text=final_text)
                        else:
                            final_text = "Interrupted by user. Session state was saved."
                            messages.append({"role": "assistant", "content": final_text})
                            self._write_live_cache("interrupted", messages, final_text=final_text)
                            self.ui.final()
                        break
                # Flush any images queued by view_image calls in this batch only after
                # every tool_call in the batch has its own contiguous tool-role result
                # appended above -- _repair_tool_sequences() expects an assistant
                # tool_calls message to be followed immediately by all of its own tool
                # results with nothing interleaved; injecting per-tool-call (inside the
                # loop above) split later tool results away from their assistant
                # message whenever the model batched more than one view_image call
                # (parallel_tool_calls=True makes that the common case, not an edge
                # case), so repair treated them as orphaned/missing and manufactured a
                # false "Recovered missing tool result" error for each one.
                if self._runtime.get("_pending_images"):
                    self._inject_pending_images(messages, self._runtime)
                    self._compress_previous_images(messages)
                if interrupted:
                    if final_text:
                        break
                    continue
                if compact_focus and self.auto_compact:
                    self.ui.compact(compact_focus)
                    messages = compact_messages(
                        messages, self.llm, system_prompt, self._registry, focus=compact_focus
                    )
                    messages = self._repair_tool_sequences(messages)
                    system_prompt = self._build_system_prompt()
                    self._last_compact_iter = iteration
                if final_text:
                    self.ui.final()
                    break
                continue

            final_text = assistant.content or ""
            self.ui.final()
            messages.append(assistant_msg)
            self._write_live_cache("completed", messages, final_text=final_text)
            break

        if not final_text:
            final_text = self._fallback_final_response(messages, user_message)
            messages.append({"role": "assistant", "content": final_text})
            self._write_live_cache("completed", messages, final_text=final_text)
            self.ui.final()

        messages = self._repair_tool_sequences(messages)
        # A caller-supplied session_path means the caller owns where this session lives
        # (e.g. an embedding project keeping its own runs/ directory) -- skip the default
        # SESSIONS_DIR write entirely rather than writing the same messages to both places.
        # _write_live_cache() (below) persists the final, repaired `messages` to
        # self._session_path atomically once this block returns.
        if self._session_path:
            session_path = self._session_path
        else:
            session_path = save_session(
                self.session_id, messages, sub_agent=self._sub_agent, system_prompt=system_prompt
            )
        self._write_live_cache("completed", messages, final_text=final_text, session_path=str(session_path))
        self.ui.final_answer(final_text, iteration)
        self.ui.saved(str(session_path))
        if final_text and self.self_review_enabled:
            trigger_self_review(
                session_id=self.session_id,
                task_id=self.task_id,
                messages=messages,
                skills_index=self._skills_index(),
                model=self.llm.model,
                provider=self.llm.provider,
                background=True,
            )

        if self._pending_restart:
            from .guardian import request_restart
            request_restart(
                changes=self._pending_restart,
                session_id=self.session_id,
                resume_path=str(session_path),
                next_prompt=self._pending_restart_prompt,
            )
            sys.stdout.flush()
            sys.exit(42)

        return {
            "session_id": self.session_id,
            "session_path": str(session_path),
            "final": final_text,
            "messages": messages,
        }

    @staticmethod
    def _atomic_write(path: Path, body: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(body, encoding="utf-8")
        # Windows readers can briefly lock the target while dashboards or
        # kanban sync inspect it. Retry the atomic replace before falling back.
        for attempt in range(5):
            try:
                tmp.replace(path)
                return
            except PermissionError:
                if attempt < 4:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                path.write_text(body, encoding="utf-8")
                try:
                    tmp.unlink(missing_ok=True)
                except Exception:
                    pass
                return

    def _write_live_cache(
        self,
        status: str,
        messages: list[dict[str, Any]],
        *,
        final_text: str = "",
        session_path: str | None = None,
    ) -> None:
        # session_path (if the caller supplied one) is persisted here too, at the
        # same granular points as the live cache below -- not just once at the end
        # of run(). A session_path that only gets written once, after the whole
        # (possibly many-tool-call, possibly long-running) call finishes reflects
        # nothing while it's in flight and loses everything if the process is
        # killed partway through; there's no cost reason to treat it differently
        # from the live cache, which already does this same messages-array
        # serialize-and-write on essentially every iteration and every tool result.
        if self._session_path:
            self._atomic_write(
                self._session_path,
                json.dumps(messages, ensure_ascii=False, indent=2, default=str),
            )

        if not self._live_cache_path:
            return
        payload = {
            **self._live_cache_metadata,
            "status": status,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "final": final_text,
            "messages": messages,
        }
        if session_path:
            payload["session_path"] = session_path
        self._atomic_write(
            self._live_cache_path,
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        )

    def _process_tool_result(self, result: Any, tool_name: str, tool_args: dict[str, Any] | None = None) -> Any:
        if not isinstance(result, str):
            return result
        result = clean_text(result)
        if len(result) <= MAX_TOOL_RESULT_CHARS:
            return result
        if tool_name in READ_FILE_TOOL_NAMES and tool_args and "max_chars" in tool_args:
            return result
        return self._spill_tool_result(result, tool_name)

    def _estimate_message_chars(self, messages: list[dict[str, Any]]) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content") or ""
            total += len(content) if isinstance(content, str) else len(str(content))
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    total += len((tc.get("function") or {}).get("arguments", ""))
        return total

    def _spill_tool_result(self, result: str, tool_name: str) -> str:
        self._spill_dir.mkdir(parents=True, exist_ok=True)
        self._spill_counter += 1
        path = self._spill_dir / f"{tool_name}_{self._spill_counter:04d}_{int(time.time())}.txt"
        path.write_text(result, encoding="utf-8")
        preview = result[:SPILL_PREVIEW_CHARS]
        return (
            "[tool result truncated to save context]\n"
            f"cache_path: {path}\n"
            f"full_content: saved at {path}\n"
            "To inspect the complete untruncated result, call read_file with this cache_path and explicit max_chars/offset chunks.\n"
            "read_file results with explicit max_chars are not spilled again by the agent.\n"
            "Example: read_file({\"path\": \""
            + str(path).replace("\\", "\\\\")
            + "\", \"max_chars\": 6000, \"offset\": 0})\n\n"
            f"--- preview ({SPILL_PREVIEW_CHARS} chars) ---\n"
            f"{preview}\n[...]"
        )

    def _inject_pending_images(self, messages: list[dict[str, Any]], runtime: dict[str, Any]) -> None:
        """Delivers whatever view_image() calls staged this iteration as a synthetic
        user message right after their (text-only) tool results, so the images are
        part of the model's input on the very next call -- see tools/vision.py."""
        pending = runtime.pop("_pending_images", None)
        if pending:
            messages.append({"role": "user", "content": pending})

    def _compress_previous_images(self, messages: list[dict[str, Any]]) -> None:
        """Mirrors _compress_previous_snapshot's pattern for view_image (see
        tools/vision.py + _inject_pending_images): once a new batch of images has
        just been injected as the newest image-carrying message, strip the pixel
        data out of the SECOND-most-recent image batch (the one that was "current"
        until this call). Called every time a new batch arrives, so each older
        batch gets compressed exactly once, right when it stops being the most
        recent -- at most one batch ever carries live pixel data at a time. The
        model already reasoned over those pixels in an earlier step of this same
        turn; resending them unchanged on every later call is pure repeated cost
        with no new information. Text labels (path, focus question) are kept in
        place so there's still a paper trail of what was reviewed and why."""
        found = 0
        for index in range(len(messages) - 1, -1, -1):
            msg = messages[index]
            content = msg.get("content")
            if msg.get("role") != "user" or not isinstance(content, list):
                continue
            if not any(isinstance(p, dict) and p.get("type") == "image_url" for p in content):
                continue
            found += 1
            if found != 2:
                continue
            new_content = [
                {"type": "text", "text": "[image content omitted here -- already reviewed in an earlier step of this turn]"}
                if isinstance(part, dict) and part.get("type") == "image_url"
                else part
                for part in content
            ]
            messages[index] = {**msg, "content": new_content}
            return

    def _compress_previous_snapshot(self, messages: list[dict[str, Any]]) -> None:
        found = 0
        for index in range(len(messages) - 1, -1, -1):
            msg = messages[index]
            if msg.get("role") != "tool" or msg.get("name") not in SNAPSHOT_TOOL_NAMES:
                continue
            found += 1
            if found != 2:
                continue
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > PREVIOUS_SNAPSHOT_LIMIT:
                messages[index] = {
                    **msg,
                    "content": content[:PREVIOUS_SNAPSHOT_LIMIT] + "\n[previous browser snapshot compressed]",
                }
            return

    def _replace_previous_result_with_notes(self, messages: list[dict[str, Any]], notes_content: str) -> None:
        notes_content = str(notes_content or "").strip()
        if not notes_content:
            return
        for index in range(len(messages) - 2, -1, -1):
            msg = messages[index]
            if msg.get("role") == "tool" and msg.get("name") != NOTES_TOOL_NAME:
                previous = str(msg.get("content", ""))
                cache_match = re.search(r"^cache_path:\s*(.+)$", previous, re.MULTILINE)
                cache_note = ""
                if cache_match:
                    cache_note = (
                        "\n\nOriginal full tool result cache_path: "
                        + cache_match.group(1).strip()
                        + "\nUse read_file(path) with this cache_path if the full original result is needed."
                    )
                if previous.startswith("[notes saved from previous result]"):
                    content = previous + "\n\n" + notes_content
                else:
                    content = "[notes saved from previous result]\n" + notes_content + cache_note
                messages[index] = {**msg, "content": content}
                break

        for index in range(len(messages) - 1, -1, -1):
            msg = messages[index]
            if msg.get("role") == "tool" and msg.get("name") == NOTES_TOOL_NAME:
                messages[index] = {**msg, "content": "[compressed]"}
                break

    def _compress_old_read_files(self, messages: list[dict[str, Any]]) -> None:
        for index, msg in enumerate(messages):
            if msg.get("role") != "tool" or msg.get("name") not in READ_FILE_TOOL_NAMES:
                continue
            content = str(msg.get("content", ""))
            if (
                content.startswith("[notes saved from previous result]")
                or content.startswith("[compressed]")
                or content.startswith("[content too large; saved to disk]")
                or content.startswith("[tool result truncated to save context]")
            ):
                continue
            if len(content) > PREVIOUS_READ_FILE_LIMIT:
                messages[index] = {
                    **msg,
                    "content": content[:PREVIOUS_READ_FILE_LIMIT] + "\n[old read_file result compressed; call read_file again if needed]",
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

    def _fallback_final_response(self, messages: list[dict[str, Any]], user_message: str | list[dict[str, Any]]) -> str:
        messages.append({"role": "user", "content": FINISH_REMINDER})
        return self._run_to_finish(messages)

    def _run_to_finish(self, messages: list[dict[str, Any]]) -> str:
        for iteration in range(1, CONTINUATION_MAX_ITERS + 1):
            api_messages = [{"role": "system", "content": self._build_system_prompt()}, *messages]
            try:
                response = self.llm.chat(api_messages, self._registry.definitions())
            except Exception as exc:
                self.ui.event("finish", f"model error: {type(exc).__name__}")
                time.sleep(3)
                continue

            assistant = response.choices[0].message
            tool_calls = getattr(assistant, "tool_calls", None) or []
            if not tool_calls:
                return assistant.content or "Stopped after reaching the iteration limit without a final answer."

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": assistant.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in tool_calls
                ],
            }
            messages.append(assistant_msg)

            final_text = ""
            for tc in tool_calls:
                recovered_args = False
                try:
                    args = json.loads(tc.function.arguments or "{}")
                    if not isinstance(args, dict):
                        args = {}
                except json.JSONDecodeError as exc:
                    recovered = _recover_file_write_args(
                        tc.function.name,
                        tc.function.arguments or "",
                        exc,
                    )
                    if recovered is not None:
                        args = recovered
                        recovered_args = True
                    else:
                        args = {}

                if tc.function.name in FINISH_BLOCKED_TOOLS:
                    result = json.dumps(
                        {
                            "success": False,
                            "error": f"Tool {tc.function.name} is blocked in finish mode. {FINISH_REMINDER}",
                        },
                        ensure_ascii=False,
                    )
                else:
                    runtime = self._runtime
                    result = self._registry.dispatch(tc.function.name, args, runtime)
                    if runtime.get("final_response") is not None:
                        final_text = str(runtime.get("final_response") or "")
                    if self._finish_tools and tc.function.name in self._finish_tools and not final_text:
                        final_text = result or "Task completed."
                    if recovered_args:
                        result = _add_recovery_metadata(result, args)

                result = self._process_tool_result(result, tc.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.function.name,
                        "content": result,
                    }
                )
                if tc.function.name in SNAPSHOT_TOOL_NAMES:
                    self._compress_previous_snapshot(messages)
                elif tc.function.name == NOTES_TOOL_NAME:
                    self._replace_previous_result_with_notes(messages, args.get("notes", ""))
                    self._compress_old_read_files(messages)
                if final_text:
                    break

            if final_text:
                return final_text
            messages.append({"role": "user", "content": FINISH_REMINDER})

        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                return str(msg["content"])
        return "Stopped after reaching the iteration limit without a final answer."

    def _repair_tool_sequences(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        repaired: list[dict[str, Any]] = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg.get("role") == "tool":
                # Orphaned tool result with no preceding assistant tool_call —
                # drop it; injecting as user message pollutes context.
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
                        pass  # mismatched tool_call_id — drop
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


ResearchAgent = GeneralAgent
