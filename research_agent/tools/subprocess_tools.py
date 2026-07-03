from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

from ..paths import PROJECT_ROOT, SESSIONS_DIR
from .registry import json_result, registry


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _cache_paths(runtime: dict, kind: str) -> tuple[Path, Path, Path, str]:
    parent_session = str(runtime.get("session_id") or "unknown_session")
    run_id = f"{kind}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    root = SESSIONS_DIR / "subprocess_cache" / parent_session
    cache_path = root / f"{run_id}.json"
    payload_path = root / f"{run_id}.payload.json"
    stdout_path = root / f"{run_id}.stdout.txt"
    return cache_path, payload_path, stdout_path, run_id


def _spawn(payload: dict, payload_path: Path, stdout_path: Path) -> int:
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    stderr_path = stdout_path.with_name(stdout_path.name.replace(".stdout.", ".stderr."))
    kwargs: dict = {}
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        proc = subprocess.Popen(
            [sys.executable, "-B", "-m", "research_agent.subprocess_worker", str(payload_path)],
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            **kwargs,
        )
    return int(proc.pid)


def _start(kind: str, args: dict, runtime: dict) -> str:
    cache_path, payload_path, stdout_path, run_id = _cache_paths(runtime, kind)
    started_at = _now()
    payload = {
        "kind": kind,
        "status": "queued",
        "run_id": run_id,
        "cache_path": str(cache_path),
        "payload_path": str(payload_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stdout_path.with_name(stdout_path.name.replace(".stdout.", ".stderr."))),
        "started_at": started_at,
        "parent_session_id": runtime.get("session_id"),
        "parent_task_id": runtime.get("task_id"),
        "provider": args.get("provider"),
        "model": args.get("model"),
        "max_iterations": args.get("max_iterations"),
        "auto_compact": args.get("auto_compact", True),
        "user_prompt": args.get("user_prompt") or args.get("prompt") or "",
        "system_prompt": "",
        "agent_role": "tool_subagent",
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    pid = _spawn(payload, payload_path, stdout_path)
    return json_result(
        success=True,
        pid=pid,
        run_id=run_id,
        cache_path=str(cache_path),
        payload_path=str(payload_path),
        stdout_path=str(stdout_path),
        stderr_path=str(payload["stderr_path"]),
        message="Background subprocess started. Read cache_path for live status and final result.",
    )


def _h_tool_subagent(args: dict, runtime: dict) -> str:
    prompt = str(args.get("user_prompt") or args.get("prompt") or "").strip()
    if not prompt:
        return json_result(success=False, error="user_prompt is required")
    return _start("tool_subagent", args, runtime)


registry.register("tool_subagent", {
    "description": (
        "Start a restricted backend helper sub-agent subprocess with a user_prompt. "
        "Returns immediately with a cache_path. This is for narrow independent helper work; "
        "by default the sub-agent cannot spawn more subagents, manage Kanban, or run meetings. "
        "It writes live session status, messages, and final result to that cache file."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_prompt": {"type": "string"},
            "max_iterations": {"type": "integer", "default": 12},
            "auto_compact": {
                "type": "boolean",
                "default": True,
                "description": "Whether the subagent may auto-compact its context. Keep true by default; set false for writer/generator tasks where exact in-progress context matters.",
            },
            "provider": {"type": "string", "enum": ["deepseek", "codex", "openai"]},
            "model": {"type": "string"},
        },
        "required": ["user_prompt"],
    },
}, _h_tool_subagent)
