"""Meeting orchestration tools — for a Moderator agent to run structured multi-agent discussions.

These tools are NOT in the default registry.  Call register_meeting_tools() to opt in.

Architecture:
  - Moderator: a GeneralAgent with meeting tools
  - Participants: lightweight GeneralAgents, always start FRESH each turn (no session_history),
                  receive all relevant context (agenda + notes + prior responses) in the user
                  message, and are restricted to respond_to_user (no file writing, no spawning)
  - group_discuss runs participants in parallel via ThreadPoolExecutor

Context design:
  - Each participant turn builds a single user message:
      [Meeting Agenda] [Moderator Notes] [Discussion So Far] [Your Turn]
  - "Discussion So Far" = all prior responses (by speaker + content), with round markers
  - Participants never see raw tool calls or internal agent loops from others
"""
from __future__ import annotations

import concurrent.futures
import contextvars
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..paths import SESSIONS_DIR
from .registry import ToolRegistry, json_result, registry

MEETINGS_DIR = SESSIONS_DIR / "meetings"

# ── Tool exclusion sets ───────────────────────────────────────────────────────

_MEETING_TOOL_NAMES = {
    "meeting_create_participants",
    "meeting_set_agenda",
    "meeting_add_notes",
    "meeting_ask_one",
    "meeting_chain",
    "meeting_group_discuss",
    "meeting_conclude",
}
_KANBAN_TOOL_NAMES = {
    "kanban_create_task", "kanban_list_tasks", "kanban_update_task",
    "kanban_dispatch", "kanban_notify_subscribe",
    "kanban_create_pipeline", "kanban_create_meeting_task",
}
# Participants must NOT write files, run shell, spawn sub-agents, or touch memory/kanban
_PARTICIPANT_WRITE_TOOLS = {
    "tool_subagent",
    "memory",
    "request_restart",
}
_PARTICIPANT_EXCLUDED = _MEETING_TOOL_NAMES | _KANBAN_TOOL_NAMES | _PARTICIPANT_WRITE_TOOLS


# ── Meeting state helpers ─────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _slugify(text: str, max_len: int = 40) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")[:max_len].rstrip("-")


def _meeting_path(meeting_id: str) -> Path:
    MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
    return MEETINGS_DIR / f"{meeting_id}.json"


def _load_meeting(meeting_id: str) -> dict[str, Any]:
    path = _meeting_path(meeting_id)
    if not path.exists():
        raise FileNotFoundError(f"Meeting not found: {meeting_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_meeting(data: dict[str, Any]) -> None:
    _meeting_path(data["meeting_id"]).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _meeting_id(runtime: dict) -> str:
    mid = runtime.get("meeting_id")
    if not mid:
        raise ValueError("No active meeting. Call meeting_create_participants first.")
    return mid


def _append_transcript(data: dict, speaker: str, content: str, round_num: int | None = None) -> None:
    entry: dict[str, Any] = {"speaker": speaker, "content": content, "timestamp": _now()}
    if round_num is not None:
        entry["round"] = round_num
    data["transcript"].append(entry)


def _append_action(data: dict, action: str, **payload: Any) -> None:
    data.setdefault("actions", []).append({"time": _now(), "action": action, **payload})


# ── Context builder ───────────────────────────────────────────────────────────

def _build_participant_message(
    data: dict[str, Any],
    speaker_name: str,
    question: str,
    discussion_history: list[dict[str, Any]],
) -> str:
    """Build the full user message for a participant's agent turn.

    Includes meeting agenda, moderator notes, all prior responses with round markers,
    and a clear 'your turn' prompt. Participants must respond via respond_to_user only.
    """
    parts: list[str] = []

    if data.get("agenda"):
        parts.append(f"=== Meeting Agenda ===\n{data['agenda']}")

    if data.get("notes"):
        parts.append(f"=== Moderator Notes ===\n{data['notes']}")

    if discussion_history:
        lines: list[str] = ["=== Discussion So Far ==="]
        current_round: int | None = None
        for entry in discussion_history:
            r = entry.get("round")
            if r is not None and r != current_round:
                current_round = r
                lines.append(f"\n[Round {r}]")
            lines.append(f"{entry['speaker']}: {entry['content']}")
        parts.append("\n".join(lines))

    parts.append(
        f"=== Your Turn ({speaker_name}) ===\n{question}\n\n"
        "Respond with your analysis and conclusions via respond_to_user. "
        "Do not write or create files — your output is your spoken response only."
    )

    return "\n\n".join(parts)


# ── Participant runner ────────────────────────────────────────────────────────

_PARTICIPANT_MAX_RETRIES = 2
_PARTICIPANT_RETRY_BASE_DELAY = 8.0


def _run_participant(
    participant: dict[str, Any],
    user_message: str,
) -> str:
    """Run one participant agent and return their respond_to_user output.

    History management:
      - participant["session_history"] holds CLEAN input/output pairs only:
          [{role:user, content:<round N context>}, {role:assistant, content:<final response>}, ...]
      - After each run, we append only the user message + final response (no tool calls).
      - This keeps the participant's context window coherent across rounds without noise.

    Restricted registry: no file writing, no shell, no spawning.

    Fault isolation: GeneralAgent.run() only catches KeyboardInterrupt internally, so an
    exhausted-retry API error (timeout, connection drop, 5xx) raises all the way out of
    agent.run(). Since a meeting nests moderator -> meeting_ask_one/chain/group_discuss ->
    participant agent, letting that propagate would crash the entire meeting (and, via
    ThreadPoolExecutor.result() in group_discuss, take down every other participant in the
    same round too). A flaky participant call must degrade to a tagged error string instead.
    """
    from ..agent import GeneralAgent
    from ..ui import ConsoleUI
    import time as _time

    participant_registry: ToolRegistry = registry.without(_PARTICIPANT_EXCLUDED)

    # session_history contains only clean user/assistant pairs from prior rounds
    history = participant.get("session_history") or []

    final = ""
    for attempt in range(_PARTICIPANT_MAX_RETRIES + 1):
        agent = GeneralAgent(
            model=participant.get("model"),
            provider=participant.get("provider"),
            max_iterations=int(participant.get("max_iterations") or 8),
            self_review=False,
            registry=participant_registry,
            ui=ConsoleUI(enabled=False, label=participant["name"]),
            sub_agent=True,
            agent_role="participant",
        )
        try:
            result = agent.run(
                user_message,
                history=history,
                system_prompt=participant.get("system_prompt"),
            )
        except Exception as exc:
            if attempt < _PARTICIPANT_MAX_RETRIES:
                delay = _PARTICIPANT_RETRY_BASE_DELAY * (attempt + 1)
                print(
                    f"[meeting] participant '{participant.get('name')}' turn failed "
                    f"({type(exc).__name__}), retry {attempt + 1}/{_PARTICIPANT_MAX_RETRIES} in {delay:.0f}s…",
                    flush=True,
                )
                _time.sleep(delay)
                continue
            final = (
                f"[PARTICIPANT ERROR: {participant.get('name')} could not complete this turn after "
                f"{_PARTICIPANT_MAX_RETRIES + 1} attempts due to repeated API failures "
                f"({type(exc).__name__}: {exc}). Treat this as a missing response for this round."
            )
            break
        else:
            final = result.get("final") or ""
            if result.get("session_id"):
                participant["session_id"] = result["session_id"]
            break

    # Append ONLY the clean input/output pair — no intermediate tool calls
    participant["session_history"] = history + [
        {"role": "user",      "content": user_message},
        {"role": "assistant", "content": final},
    ]

    return final


# ── Tool handlers ─────────────────────────────────────────────────────────────

def _handle_create_participants(args: dict, runtime: dict) -> str:
    participants_cfg = args.get("participants") or []
    if not participants_cfg:
        return json_result(success=False, error="participants list is required")

    existing_meeting_id = runtime.get("meeting_id")
    if existing_meeting_id:
        try:
            existing = _load_meeting(str(existing_meeting_id))
            return json_result(
                success=True,
                meeting_id=existing_meeting_id,
                participants=list((existing.get("participants") or {}).keys()),
                already_exists=True,
                hint=(
                    "A meeting is already active in this moderator run. "
                    "Do not call meeting_create_participants again; continue with agenda/discussion/conclusion."
                ),
            )
        except FileNotFoundError:
            runtime.pop("meeting_id", None)

    meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
    participant_names = [str(cfg.get("name") or "").strip() for cfg in participants_cfg if cfg.get("name")]
    default_name = "+".join(participant_names[:3])

    data: dict[str, Any] = {
        "meeting_id": meeting_id,
        "name":       default_name,
        "created_at": _now(),
        "agenda":     "",
        "notes":      "",
        "conclusion": "",
        "transcript": [],
        "actions":    [],
        "participants": {},
    }
    for cfg in participants_cfg:
        name = str(cfg.get("name") or "").strip()
        if not name:
            continue
        role   = str(cfg.get("role")   or "").strip()
        skills = str(cfg.get("skills") or "").strip()
        system_prompt = (
            "You are a meeting participant, not the main scheduling agent. "
            "Answer only from your assigned expertise and the meeting context. "
            "Do not create Kanban tasks, spawn agents, call meeting orchestration tools, or write project files.\n\n"
            f"You are {name}."
            + (f" Role: {role}." if role else "")
            + (f"\n\nSkills and knowledge:\n{skills}" if skills else "")
        )
        data["participants"][name] = {
            "name":           name,
            "role":           role,
            "system_prompt":  cfg.get("system_prompt") or system_prompt,
            "model":          cfg.get("model"),
            "provider":       cfg.get("provider"),
            "max_iterations": int(cfg.get("max_iterations") or 8),
            "session_id":     None,
        }

    _save_meeting(data)
    runtime["meeting_id"] = meeting_id
    _append_action(
        data,
        "create_participants",
        participants=[
            {"name": p.get("name"), "role": p.get("role"), "model": p.get("model"), "provider": p.get("provider")}
            for p in data["participants"].values()
        ],
    )
    _save_meeting(data)
    return json_result(
        success=True,
        meeting_id=meeting_id,
        participants=list(data["participants"].keys()),
        hint=(
            "Meeting created. Optionally call meeting_set_agenda / meeting_add_notes, "
            "then use meeting_ask_one / meeting_chain / meeting_group_discuss."
        ),
    )


def _handle_set_agenda(args: dict, runtime: dict) -> str:
    data = _load_meeting(_meeting_id(runtime))
    agenda = str(args.get("agenda") or "").strip()
    data["agenda"] = agenda
    if agenda:
        data["name"] = _slugify(agenda)
    _append_action(data, "set_agenda", agenda=agenda)
    _save_meeting(data)
    return json_result(success=True)


def _handle_add_notes(args: dict, runtime: dict) -> str:
    data = _load_meeting(_meeting_id(runtime))
    content = str(args.get("content") or "").strip()
    data["notes"] = (data["notes"] + f"\n\n{content}").strip() if data["notes"] else content
    _append_action(data, "add_notes", content=content)
    _save_meeting(data)
    return json_result(success=True)


def _handle_ask_one(args: dict, runtime: dict) -> str:
    """Ask a single participant a question.

    Context injected: agenda + notes + full transcript so far + question.
    """
    data     = _load_meeting(_meeting_id(runtime))
    name     = str(args.get("participant") or "").strip()
    question = str(args.get("question")    or "").strip()

    if name not in data["participants"]:
        return json_result(success=False, error=f"Participant '{name}' not found")

    participant = data["participants"][name]

    # Build discussion history from full transcript so far
    discussion_history = [
        {"speaker": e["speaker"], "content": e["content"], "round": e.get("round")}
        for e in data["transcript"]
        if e.get("speaker") != "moderator"
    ]

    user_message = _build_participant_message(data, name, question, discussion_history)
    response = _run_participant(participant, user_message)

    _append_transcript(data, name, response)
    _append_action(data, "ask_one", participant=name, question=question, response=response)
    data["participants"][name] = participant
    _save_meeting(data)

    return json_result(success=True, participant=name, response=response)


def _handle_chain(args: dict, runtime: dict) -> str:
    """Sequential chain: each participant sees ALL prior responses (all rounds, all speakers).

    Each turn's user message = agenda + notes + everything said so far + "your turn".
    """
    data         = _load_meeting(_meeting_id(runtime))
    participants = args.get("participants") or []
    prompt       = str(args.get("prompt") or "").strip()
    rounds       = int(args.get("rounds") or 1)

    missing = [n for n in participants if n not in data["participants"]]
    if missing:
        return json_result(success=False, error=f"Unknown participants: {missing}")

    # Accumulate responses across ALL rounds
    chain_history: list[dict[str, Any]] = []
    action_rounds: list[dict[str, Any]] = []

    for round_num in range(1, rounds + 1):
        round_entries: list[dict[str, Any]] = []
        for name in participants:
            participant = data["participants"][name]
            user_message = _build_participant_message(
                data, name, prompt, chain_history
            )
            response = _run_participant(participant, user_message)

            entry = {"speaker": name, "content": response, "round": round_num}
            chain_history.append(entry)
            round_entries.append(entry)
            _append_transcript(data, name, response, round_num=round_num)
            data["participants"][name] = participant
            _save_meeting(data)   # persist after each speaker so UI can refresh
        action_rounds.append({"round": round_num, "responses": round_entries})

    summary = "\n\n".join(
        f"[Round {e['round']}] {e['speaker']}: {e['content']}"
        for e in chain_history
    )
    _append_action(data, "chain", participants=participants, prompt=prompt, rounds=rounds, round_results=action_rounds)
    _save_meeting(data)
    return json_result(success=True, rounds=rounds, transcript=summary)


def _handle_group_discuss(args: dict, runtime: dict) -> str:
    """Parallel group discussion: all participants respond simultaneously each round.

    Each round:
      - All participants run in parallel (ThreadPoolExecutor)
      - Each participant sees agenda + notes + ALL responses from PREVIOUS rounds only
        (current-round peers haven't spoken yet — that's the parallel constraint)
      - After all parallel calls complete, responses are collected and become visible
        to all participants in the next round
    """
    data         = _load_meeting(_meeting_id(runtime))
    participants = args.get("participants") or []
    topic        = str(args.get("topic")  or "").strip()
    rounds       = int(args.get("rounds") or 2)

    missing = [n for n in participants if n not in data["participants"]]
    if missing:
        return json_result(success=False, error=f"Unknown participants: {missing}")

    all_rounds: list[list[dict[str, Any]]] = []

    for round_num in range(1, rounds + 1):
        # Prior rounds only — parallel peers haven't spoken yet
        prior_history: list[dict[str, Any]] = [
            entry
            for r_entries in all_rounds
            for entry in r_entries
        ]

        question = f"[Round {round_num}] {topic}"

        # Capture participant snapshots for thread safety
        participant_snapshots = {
            name: dict(data["participants"][name])
            for name in participants
        }

        def _run_one(name: str) -> dict[str, Any]:
            p = participant_snapshots[name]
            msg = _build_participant_message(data, name, question, prior_history)
            response = _run_participant(p, msg)
            # Write updated session_history + session_id back to live data
            # (thread-safe: each name is a distinct dict key)
            data["participants"][name]["session_history"] = p.get("session_history") or []
            if p.get("session_id"):
                data["participants"][name]["session_id"] = p["session_id"]
            return {"speaker": name, "content": response, "round": round_num}

        # ThreadPoolExecutor workers do NOT inherit the calling thread's contextvars
        # (unlike asyncio tasks). agent_browser binds the active browser session to a
        # ContextVar, so without this, each participant thread would see no session and
        # silently open a brand-new browser tab instead of the moderator's. Capturing the
        # context here and running workers inside it makes participants share the same
        # browser session as the moderator/main agent.
        ctx = contextvars.copy_context()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(participants)) as ex:
            futures = {ex.submit(ctx.run, _run_one, name): name for name in participants}
            round_responses_unordered = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Restore the declared participant order
        order = {name: i for i, name in enumerate(participants)}
        round_responses = sorted(round_responses_unordered, key=lambda e: order.get(e["speaker"], 999))

        all_rounds.append(round_responses)
        for entry in round_responses:
            _append_transcript(data, entry["speaker"], entry["content"], round_num=round_num)
        _save_meeting(data)

    summary_lines = [
        f"[Round {e['round']}] {e['speaker']}: {e['content']}"
        for r in all_rounds for e in r
    ]
    _append_action(data, "group_discuss", participants=participants, topic=topic, rounds=rounds, round_results=all_rounds)
    _save_meeting(data)
    return json_result(success=True, rounds=rounds, transcript="\n\n".join(summary_lines))


def _handle_conclude(args: dict, runtime: dict) -> str:
    data = _load_meeting(_meeting_id(runtime))
    conclusion = str(args.get("conclusion") or "").strip()
    data["conclusion"] = conclusion
    data["closed_at"]  = _now()
    _append_transcript(data, "moderator", f"[CONCLUSION] {conclusion}")
    _append_action(data, "conclude", conclusion=conclusion)
    _save_meeting(data)
    runtime.pop("meeting_id", None)
    runtime["final_response"] = conclusion
    return json_result(success=True, conclusion=conclusion, meeting_id=data["meeting_id"])


# ── Registration ──────────────────────────────────────────────────────────────

def register_meeting_tools() -> None:
    registry.register("meeting_create_participants", {
        "description": (
            "Start a meeting by creating participant agents. "
            "Each participant responds via respond_to_user only — no file writing. "
            "All context (agenda, notes, prior responses) is injected into each turn automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {
                    "type": "array",
                    "description": "List of participant configs.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":           {"type": "string"},
                            "role":           {"type": "string"},
                            "skills":         {"type": "string"},
                            "system_prompt":  {"type": "string", "description": "Override full system prompt (optional)"},
                            "model":          {"type": "string"},
                            "provider":       {"type": "string"},
                            "max_iterations": {"type": "integer", "default": 8},
                        },
                        "required": ["name"],
                    },
                },
            },
            "required": ["participants"],
        },
    }, _handle_create_participants)

    registry.register("meeting_set_agenda", {
        "description": "Set the meeting agenda. Automatically included in every participant's context.",
        "parameters": {
            "type": "object",
            "properties": {"agenda": {"type": "string"}},
            "required": ["agenda"],
        },
    }, _handle_set_agenda)

    registry.register("meeting_add_notes", {
        "description": (
            "Append text to shared moderator notes. "
            "Notes are included in every subsequent participant turn — use to inject background, "
            "constraints, or key facts discovered mid-meeting."
        ),
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    }, _handle_add_notes)

    registry.register("meeting_ask_one", {
        "description": (
            "Ask a single participant a question. "
            "They receive: agenda + notes + full transcript so far + your question. "
            "They respond via respond_to_user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participant": {"type": "string"},
                "question":    {"type": "string"},
            },
            "required": ["participant", "question"],
        },
    }, _handle_ask_one)

    registry.register("meeting_chain", {
        "description": (
            "Sequential chain: participants speak one by one. "
            "Each speaker receives ALL prior responses (all rounds, all speakers) in their context. "
            "Use rounds>1 to iterate the full chain multiple times."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of participant names"},
                "prompt":       {"type": "string", "description": "The question or topic for each speaker"},
                "rounds":       {"type": "integer", "default": 1},
            },
            "required": ["participants", "prompt"],
        },
    }, _handle_chain)

    registry.register("meeting_group_discuss", {
        "description": (
            "Parallel group discussion: all participants respond simultaneously each round. "
            "Within a round, participants cannot see each other's current-round responses "
            "(they run in parallel). Between rounds, all previous responses are visible. "
            "Use rounds>=2 for iterative refinement."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {"type": "array", "items": {"type": "string"}},
                "topic":        {"type": "string"},
                "rounds":       {"type": "integer", "default": 2},
            },
            "required": ["participants", "topic"],
        },
    }, _handle_group_discuss)

    registry.register("meeting_conclude", {
        "description": (
            "Record the final conclusion, close the meeting, and end the agent loop. "
            "Call this after all discussion is done."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "conclusion": {"type": "string"},
            },
            "required": ["conclusion"],
        },
    }, _handle_conclude)


def register_moderator_tools() -> None:
    """Register meeting discussion tools for a Moderator agent.

    Moderators can create the participant roster, run the discussion,
    and conclude the meeting.
    """
    registry.register("meeting_create_participants", {
        "description": (
            "Start a meeting by creating participant agents. "
            "Each participant responds via respond_to_user only; no file writing. "
            "All context (agenda, notes, prior responses) is injected into each turn automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {
                    "type": "array",
                    "description": "List of participant configs.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":           {"type": "string"},
                            "role":           {"type": "string"},
                            "skills":         {"type": "string"},
                            "system_prompt":  {"type": "string", "description": "Override full system prompt (optional)"},
                            "model":          {"type": "string"},
                            "provider":       {"type": "string"},
                            "max_iterations": {"type": "integer", "default": 8},
                        },
                        "required": ["name"],
                    },
                },
            },
            "required": ["participants"],
        },
    }, _handle_create_participants)

    registry.register("meeting_set_agenda", {
        "description": "Set the meeting agenda. Automatically included in every participant's context.",
        "parameters": {
            "type": "object",
            "properties": {"agenda": {"type": "string"}},
            "required": ["agenda"],
        },
    }, _handle_set_agenda)

    registry.register("meeting_add_notes", {
        "description": (
            "Append text to shared moderator notes. "
            "Notes are included in every subsequent participant turn — use to inject background, "
            "constraints, or key facts discovered mid-meeting."
        ),
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    }, _handle_add_notes)

    registry.register("meeting_ask_one", {
        "description": (
            "Ask a single participant a question. "
            "They receive: agenda + notes + full transcript so far + your question. "
            "They respond via respond_to_user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participant": {"type": "string"},
                "question":    {"type": "string"},
            },
            "required": ["participant", "question"],
        },
    }, _handle_ask_one)

    registry.register("meeting_chain", {
        "description": (
            "Sequential chain: participants speak one by one. "
            "Each speaker receives ALL prior responses (all rounds, all speakers) in their context. "
            "Use rounds>1 to iterate the full chain multiple times."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of participant names"},
                "prompt":       {"type": "string", "description": "The question or topic for each speaker"},
                "rounds":       {"type": "integer", "default": 1},
            },
            "required": ["participants", "prompt"],
        },
    }, _handle_chain)

    registry.register("meeting_group_discuss", {
        "description": (
            "Parallel group discussion: all participants respond simultaneously each round. "
            "Within a round, participants cannot see each other's current-round responses "
            "(they run in parallel). Between rounds, all previous responses are visible. "
            "Use rounds>=2 for iterative refinement."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {"type": "array", "items": {"type": "string"}},
                "topic":        {"type": "string"},
                "rounds":       {"type": "integer", "default": 2},
            },
            "required": ["participants", "topic"],
        },
    }, _handle_group_discuss)

    registry.register("meeting_conclude", {
        "description": (
            "Record the final conclusion, close the meeting, and end the agent loop. "
            "Call this after all discussion is done."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "conclusion": {"type": "string"},
            },
            "required": ["conclusion"],
        },
    }, _handle_conclude)
