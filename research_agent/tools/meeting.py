"""Meeting orchestration tools — for a Moderator agent to run structured multi-agent discussions.

These tools are NOT in the default registry.  Call register_meeting_tools() to opt in.

Architecture:
  - Moderator: a GeneralAgent with meeting tools (but no kanban tools)
  - Participants: full GeneralAgents with their own tool loops and session histories,
                  but without kanban_* and meeting_* tools
  - Each participant's internal tool calls are invisible to others;
    only their respond_to_user final text is shared
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..paths import SESSIONS_DIR
from .registry import ToolRegistry, json_result, registry

MEETINGS_DIR = SESSIONS_DIR / "meetings"

# Tool names excluded from participant registries
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
    "kanban_dispatch", "kanban_notify_subscribe", "kanban_wait_complete",
}
_PARTICIPANT_EXCLUDED = _MEETING_TOOL_NAMES | _KANBAN_TOOL_NAMES


# ── Meeting state helpers ─────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


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


def _append_transcript(data: dict, speaker: str, content: str) -> None:
    data["transcript"].append({
        "speaker": speaker,
        "content": content,
        "timestamp": _now(),
    })


# ── Participant agent runner ──────────────────────────────────────────────

def _run_participant(
    participant: dict[str, Any],
    question: str,
    shared_context: str = "",
) -> str:
    """Run one participant's agent loop and return their final response.

    shared_context is prepended as context from the meeting (e.g. previous
    responses in a chain) and is NOT added to the participant's own history —
    it is passed as part of the user message so the participant can reference
    it but it doesn't pollute their internal session.
    """
    from ..agent import GeneralAgent
    from ..ui import ConsoleUI

    # Build participant-specific registry (exclude meeting + kanban tools)
    participant_registry: ToolRegistry = registry.without(_PARTICIPANT_EXCLUDED)

    prompt = question
    if shared_context:
        prompt = f"{shared_context}\n\n---\n{question}"

    agent = GeneralAgent(
        model=participant.get("model"),
        provider=participant.get("provider"),
        max_iterations=participant.get("max_iterations", 12),
        self_review=False,
        registry=participant_registry,
        ui=ConsoleUI(enabled=False, label=participant["name"]),
    )
    result = agent.run(
        prompt,
        history=participant.get("session_history") or [],
        system_prompt=participant.get("system_prompt"),
    )
    # Persist updated session history back to participant record
    participant["session_history"] = result["messages"]
    return result.get("final") or ""


# ── Tool handlers ─────────────────────────────────────────────────────────

def _handle_create_participants(args: dict, runtime: dict) -> str:
    participants_cfg = args.get("participants") or []
    if not participants_cfg:
        return json_result(success=False, error="participants list is required")

    meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
    data: dict[str, Any] = {
        "meeting_id": meeting_id,
        "created_at": _now(),
        "agenda": "",
        "notes": "",
        "conclusion": "",
        "transcript": [],
        "participants": {},
    }
    for cfg in participants_cfg:
        name = str(cfg.get("name") or "").strip()
        if not name:
            continue
        role   = str(cfg.get("role") or "").strip()
        skills = str(cfg.get("skills") or "").strip()
        system_prompt = (
            f"You are {name}."
            + (f" Role: {role}." if role else "")
            + (f"\n\nSkills and knowledge:\n{skills}" if skills else "")
        )
        data["participants"][name] = {
            "name":            name,
            "role":            role,
            "system_prompt":   cfg.get("system_prompt") or system_prompt,
            "model":           cfg.get("model"),
            "provider":        cfg.get("provider"),
            "max_iterations":  int(cfg.get("max_iterations") or 12),
            "session_history": [],
        }

    _save_meeting(data)
    runtime["meeting_id"] = meeting_id
    return json_result(
        success=True,
        meeting_id=meeting_id,
        participants=list(data["participants"].keys()),
        hint="Meeting created. Optionally call meeting_set_agenda, then use meeting_ask_one / meeting_chain / meeting_group_discuss.",
    )


def _handle_set_agenda(args: dict, runtime: dict) -> str:
    data = _load_meeting(_meeting_id(runtime))
    data["agenda"] = str(args.get("agenda") or "").strip()
    _save_meeting(data)
    return json_result(success=True)


def _handle_add_notes(args: dict, runtime: dict) -> str:
    data = _load_meeting(_meeting_id(runtime))
    content = str(args.get("content") or "").strip()
    if data["notes"]:
        data["notes"] += f"\n\n{content}"
    else:
        data["notes"] = content
    _save_meeting(data)
    return json_result(success=True)


def _handle_ask_one(args: dict, runtime: dict) -> str:
    """Ask a single participant a question. Returns their response."""
    data        = _load_meeting(_meeting_id(runtime))
    name        = str(args.get("participant") or "").strip()
    question    = str(args.get("question") or "").strip()
    context     = str(args.get("context") or "").strip()

    if name not in data["participants"]:
        return json_result(success=False, error=f"Participant '{name}' not found")

    participant = data["participants"][name]
    response    = _run_participant(participant, question, shared_context=context)

    _append_transcript(data, name, response)
    data["participants"][name] = participant   # updated session_history
    _save_meeting(data)

    return json_result(success=True, participant=name, response=response)


def _handle_chain(args: dict, runtime: dict) -> str:
    """Sequential chain: each participant sees all previous responses before replying.

    Rounds > 1 means the whole chain repeats, with participants seeing the
    accumulated transcript from prior rounds as shared context.
    """
    data         = _load_meeting(_meeting_id(runtime))
    participants = args.get("participants") or []
    prompt       = str(args.get("prompt") or "").strip()
    rounds       = int(args.get("rounds") or 1)

    missing = [n for n in participants if n not in data["participants"]]
    if missing:
        return json_result(success=False, error=f"Unknown participants: {missing}")

    chain_transcript: list[dict] = []

    for round_num in range(1, rounds + 1):
        for name in participants:
            prior = "\n\n".join(
                f"{e['speaker']}: {e['content']}" for e in chain_transcript
            )
            shared = f"[Round {round_num}]\n{prior}" if prior else f"[Round {round_num}]"
            participant = data["participants"][name]
            response    = _run_participant(participant, prompt, shared_context=shared)
            entry = {"speaker": name, "content": response, "round": round_num}
            chain_transcript.append(entry)
            _append_transcript(data, name, response)
            data["participants"][name] = participant

    _save_meeting(data)
    summary = "\n\n".join(f"{e['speaker']} (r{e['round']}): {e['content']}" for e in chain_transcript)
    return json_result(success=True, rounds=rounds, transcript=summary)


def _handle_group_discuss(args: dict, runtime: dict) -> str:
    """Free group discussion: in each round every participant sees all responses
    from the previous round before replying.
    """
    data         = _load_meeting(_meeting_id(runtime))
    participants = args.get("participants") or []
    topic        = str(args.get("topic") or "").strip()
    rounds       = int(args.get("rounds") or 2)

    missing = [n for n in participants if n not in data["participants"]]
    if missing:
        return json_result(success=False, error=f"Unknown participants: {missing}")

    all_rounds: list[list[dict]] = []

    for round_num in range(1, rounds + 1):
        prior_text = ""
        if all_rounds:
            lines = []
            for r_idx, r_entries in enumerate(all_rounds, 1):
                for e in r_entries:
                    lines.append(f"[Round {r_idx}] {e['speaker']}: {e['content']}")
            prior_text = "\n\n".join(lines)

        round_entries: list[dict] = []
        for name in participants:
            shared = f"Topic: {topic}"
            if prior_text:
                shared += f"\n\nPrevious discussion:\n{prior_text}"
            participant = data["participants"][name]
            response    = _run_participant(participant, f"[Round {round_num}] Share your thoughts.", shared_context=shared)
            entry = {"speaker": name, "content": response, "round": round_num}
            round_entries.append(entry)
            _append_transcript(data, name, response)
            data["participants"][name] = participant

        all_rounds.append(round_entries)

    _save_meeting(data)
    summary_lines = [
        f"[Round {e['round']}] {e['speaker']}: {e['content']}"
        for r in all_rounds for e in r
    ]
    return json_result(success=True, rounds=rounds, transcript="\n\n".join(summary_lines))


def _handle_conclude(args: dict, runtime: dict) -> str:
    """Record the moderator's final conclusion, close the meeting, and end the agent loop.

    Setting runtime['final_response'] causes GeneralAgent to exit immediately —
    no separate respond_to_user call is needed.
    """
    data = _load_meeting(_meeting_id(runtime))
    conclusion = str(args.get("conclusion") or "").strip()
    data["conclusion"] = conclusion
    data["closed_at"]  = _now()
    _append_transcript(data, "moderator", f"[CONCLUSION] {conclusion}")
    _save_meeting(data)
    runtime.pop("meeting_id", None)
    runtime["final_response"] = conclusion   # triggers agent loop exit
    return json_result(success=True, conclusion=conclusion, meeting_id=data["meeting_id"])


# ── Registration ──────────────────────────────────────────────────────────

def register_meeting_tools() -> None:
    """Opt-in: register all meeting orchestration tools.

    Call this once at startup for agents that will act as meeting moderators.
    Do NOT call for regular research agents — they should not have these tools.
    """
    registry.register("meeting_create_participants", {
        "description": (
            "Start a meeting by creating participant agents. "
            "Each participant is a full agent with their own tool loop and session history, "
            "but without kanban or meeting tools. "
            "Returns a meeting_id that subsequent meeting tools use automatically."
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
                            "role":           {"type": "string", "description": "Short role description, e.g. 'Software Architect'"},
                            "skills":         {"type": "string", "description": "Domain knowledge or capabilities"},
                            "system_prompt":  {"type": "string", "description": "Override full system prompt (optional)"},
                            "model":          {"type": "string"},
                            "provider":       {"type": "string"},
                            "max_iterations": {"type": "integer", "default": 12},
                        },
                        "required": ["name"],
                    },
                },
            },
            "required": ["participants"],
        },
    }, _handle_create_participants)

    registry.register("meeting_set_agenda", {
        "description": "Set the meeting agenda (visible to the moderator, not automatically to participants).",
        "parameters": {
            "type": "object",
            "properties": {"agenda": {"type": "string"}},
            "required": ["agenda"],
        },
    }, _handle_set_agenda)

    registry.register("meeting_add_notes", {
        "description": "Append text to the shared meeting notes. Use this to record key points or compress prior discussion before it grows too long.",
        "parameters": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    }, _handle_add_notes)

    registry.register("meeting_ask_one", {
        "description": "Ask a single participant a question. The participant runs their full agent loop and returns a final response. Optionally pass context (e.g. prior responses) they should consider.",
        "parameters": {
            "type": "object",
            "properties": {
                "participant": {"type": "string", "description": "Participant name"},
                "question":    {"type": "string"},
                "context":     {"type": "string", "description": "Optional shared context to show this participant (not added to their session history)"},
            },
            "required": ["participant", "question"],
        },
    }, _handle_ask_one)

    registry.register("meeting_chain", {
        "description": (
            "Sequential chain: participants respond one by one, each seeing all previous responses. "
            "Optionally repeat for multiple rounds."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "participants": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of participant names"},
                "prompt":       {"type": "string", "description": "The question or topic for the chain"},
                "rounds":       {"type": "integer", "default": 1, "description": "Number of times to repeat the full chain"},
            },
            "required": ["participants", "prompt"],
        },
    }, _handle_chain)

    registry.register("meeting_group_discuss", {
        "description": (
            "Free group discussion: in each round every participant sees all responses from the previous round. "
            "Good for open brainstorming or debate."
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
        "description": "Record the final conclusion and close the meeting. Then call respond_to_user with the conclusion.",
        "parameters": {
            "type": "object",
            "properties": {
                "conclusion": {"type": "string", "description": "The moderator's synthesized conclusion from the discussion"},
            },
            "required": ["conclusion"],
        },
    }, _handle_conclude)
