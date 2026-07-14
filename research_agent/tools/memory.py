from __future__ import annotations

import json
from pathlib import Path

from ..env import get_env
from ..md_entries import read_entries, write_entries
from ..paths import MEMORIES_DIR
from .registry import json_result, registry

# memory_snapshot() re-injects every entry into every system prompt of every
# session, forever, with no built-in expiry. Left unbounded, self-review's
# automatic `memory add` calls after each run accumulate one-off facts and
# stale project state indefinitely, bloating every future prompt. Cap total
# size per target file; once exceeded, ask the model to triage the whole set
# in one pass (merge duplicates, drop stale/one-off notes, keep durable
# lessons) the same way a human review would. FIFO-drop-oldest is kept only
# as a fallback if the LLM call fails or doesn't return usable output, and as
# a final safety net in case the model doesn't compress enough on its own.
_DEFAULT_MAX_CHARS = 16000


def _max_chars() -> int:
    try:
        return int(get_env("MEMORY_MAX_CHARS", str(_DEFAULT_MAX_CHARS)))
    except ValueError:
        return _DEFAULT_MAX_CHARS


def _compact_prompt(entries: list[str]) -> str:
    numbered = "\n\n".join(f"[{i}] {entry}" for i, entry in enumerate(entries))
    return (
        "The following are persistent memory entries accumulated across many past agent "
        "sessions. They have grown too large to keep injecting in full into every prompt. "
        "Compress them into a smaller set of entries:\n"
        "- Merge duplicate or overlapping entries into one.\n"
        "- Drop entries that are one-off task/project facts rather than durable, reusable "
        "lessons.\n"
        "- Drop entries that only describe a bug/change that is already fully resolved, with "
        "no further actionable value.\n"
        "- Keep entries that are durable technical facts, tool behaviors, or preferences "
        "likely to matter in future sessions.\n"
        "- Preserve exact specifics (file paths, function/tool names, error messages) in "
        "whatever you keep; do not paraphrase them away.\n\n"
        f"Entries:\n{numbered}\n\n"
        "Respond with ONLY a JSON array of strings, one per surviving entry. No other text."
    )


def _parse_compacted(raw: str) -> list[str] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, list) and parsed and all(isinstance(x, str) and x.strip() for x in parsed):
        return [x.strip() for x in parsed]
    return None


def _try_llm_compact(entries: list[str]) -> list[str] | None:
    try:
        from ..llm import LLMClient

        client = LLMClient()
        return _parse_compacted(client.complete_text(_compact_prompt(entries)))
    except Exception:
        return None


def _enforce_cap(entries: list[str]) -> list[str]:
    max_chars = _max_chars()
    total = sum(len(entry) for entry in entries)
    if total <= max_chars:
        return entries

    compacted = _try_llm_compact(entries)
    if compacted is not None:
        entries = compacted
        total = sum(len(entry) for entry in entries)

    # Fallback / final guarantee: FIFO-trim anything still over cap. Covers both
    # LLM failure (compacted is None, entries unchanged) and a compacted result
    # that's still too large.
    while total > max_chars and len(entries) > 1:
        dropped = entries.pop(0)
        total -= len(dropped)
    return entries


def _memory_path(target: str) -> Path:
    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORIES_DIR / ("USER.md" if target == "user" else "MEMORY.md")


def _read_entries(target: str) -> list[str]:
    return read_entries(_memory_path(target))


def _write_entries(target: str, entries: list[str]) -> None:
    write_entries(_memory_path(target), entries)


def memory_snapshot() -> str:
    parts: list[str] = []
    for target, title in (("user", "USER PROFILE"), ("memory", "AGENT MEMORY")):
        entries = _read_entries(target)
        if entries:
            parts.append(f"## {title}\n" + "\n".join(f"- {entry}" for entry in entries))
    return "\n\n".join(parts)


def _memory(args: dict, runtime: dict) -> str:
    action = str(args.get("action") or "read")
    target = str(args.get("target") or "memory")
    if target not in {"memory", "user"}:
        return json_result(success=False, error="target must be memory or user")
    entries = _read_entries(target)

    if action == "read":
        return json_result(success=True, target=target, entries=entries)
    if action == "add":
        content = str(args.get("content") or "").strip()
        if not content:
            return json_result(success=False, error="content is required")
        if content not in entries:
            entries.append(content)
            entries = _enforce_cap(entries)
            _write_entries(target, entries)
        return json_result(success=True, message="Entry added", target=target)
    if action == "replace":
        old_text = str(args.get("old_text") or "")
        content = str(args.get("content") or "").strip()
        matches = [i for i, entry in enumerate(entries) if old_text and old_text in entry]
        if len(matches) != 1:
            return json_result(success=False, error=f"Expected one match, found {len(matches)}")
        entries[matches[0]] = content
        _write_entries(target, entries)
        return json_result(success=True, message="Entry replaced", target=target)
    if action == "remove":
        old_text = str(args.get("old_text") or "")
        new_entries = [entry for entry in entries if old_text not in entry]
        removed = len(entries) - len(new_entries)
        _write_entries(target, new_entries)
        return json_result(success=True, message="Entries removed", removed=removed, target=target)
    return json_result(success=False, error="action must be read, add, replace, or remove")


registry.register(
    "memory",
    {
        "description": "Read or update persistent memory. Use user for user preferences and memory for durable agent/project facts.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["read", "add", "replace", "remove"]},
                "target": {"type": "string", "enum": ["memory", "user"], "default": "memory"},
                "content": {"type": "string"},
                "old_text": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    _memory,
)

