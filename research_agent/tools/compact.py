from __future__ import annotations

from .registry import json_result, registry


def _compact_context(args: dict, runtime: dict) -> str:
    runtime["compact_requested"] = args.get("focus") or "manual compact_context tool call"
    return json_result(success=True, message="Context compaction requested")


registry.register(
    "compact_context",
    {
        "description": "Request context compaction when the conversation is getting long or noisy.",
        "parameters": {
            "type": "object",
            "properties": {"focus": {"type": "string", "description": "What the compaction should preserve most carefully."}},
            "required": [],
        },
    },
    _compact_context,
)


def _compact_checkpoint(args: dict, runtime: dict) -> str:
    return json_result(
        success=False,
        error="compact_checkpoint can only be used when explicitly instructed to enter compact mode.",
    )


registry.register(
    "compact_checkpoint",
    {
        "description": (
            "Internal tool used only during context-compaction mode. Do not call this unless "
            "you have just been explicitly instructed to enter compaction mode — the required "
            "format will be given to you at that time. Calling it otherwise has no effect."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "checkpoint": {
                    "type": "string",
                    "description": "Only used in compaction mode; see the compaction instructions for the required format.",
                }
            },
            "required": ["checkpoint"],
        },
    },
    _compact_checkpoint,
)

