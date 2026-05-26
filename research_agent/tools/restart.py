"""
Tool: request_restart

Allows the agent to signal that it has modified its own source code and
needs to restart to load the changes. This tool writes a signal file and
sets a flag on the agent instance. After the current run completes, the
agent's run() method will detect the flag and exit with code 42, which
the Guardian (parent process) interprets as a restart signal.

Usage:
    request_restart(changes=["Fixed terminal encoding bug in tools/terminal.py"])

# TEST: Guardian restart test - 2025-07-11
"""

from __future__ import annotations

from .registry import json_result, registry


def _request_restart(args: dict, runtime: dict) -> str:
    changes = args.get("changes", [])
    if not changes:
        return json_result(
            success=False,
            error="'changes' list is required. Describe what was modified.",
        )

    # Store the restart request in the runtime so agent.py can pick it up
    runtime["_pending_restart"] = changes
    runtime["_pending_restart_prompt"] = args.get("next_prompt")

    return json_result(
        success=True,
        message=(
            f"Restart requested. {len(changes)} change(s) recorded. "
            "The agent will exit after this response, and the Guardian "
            "will spawn a fresh process with the updated code."
        ),
        changes=changes,
    )


registry.register(
    "request_restart",
    {
        "description": (
            "Signal that the agent has modified its own source code and needs to restart. "
            "After calling this, the agent will exit and the Guardian (parent process) "
            "will spawn a fresh process with the updated code. "
            "Use this after fixing a bug in the agent's own source files (agent.py, tools/*.py, prompts.py, etc.)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "changes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of human-readable descriptions of what was changed.",
                },
                "next_prompt": {
                    "type": "string",
                    "description": "Optional. The prompt to run after restart (for chat continuity).",
                },
            },
            "required": ["changes"],
        },
    },
    _request_restart,
)
