from __future__ import annotations

import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent import GeneralAgent
from .env import load_dotenv
from .ui import ConsoleUI


_TOOL_SUBAGENT_EXCLUDED = {
    "tool_subagent",
    "meeting_create_participants",
    "meeting_set_agenda",
    "meeting_add_notes",
    "meeting_ask_one",
    "meeting_chain",
    "meeting_group_discuss",
    "meeting_conclude",
    "kanban_create_task",
    "kanban_list_tasks",
    "kanban_show_task",
    "kanban_update_task",
    "kanban_retry_task",
    "kanban_dispatch",
    "kanban_notify_subscribe",
    "kanban_wait_complete",
    "kanban_create_pipeline",
    "kanban_create_meeting_task",
    "kanban_list_boards",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _start_parent_monitor(cache_path: Path) -> None:
    if os.environ.get("AGENT_KILL_CHILDREN_ON_PARENT_EXIT") != "1":
        return
    try:
        parent_pid = int(os.environ.get("AGENT_PARENT_PID") or "0")
    except ValueError:
        return
    if parent_pid <= 0:
        return

    def _monitor() -> None:
        while True:
            time.sleep(2)
            if _process_exists(parent_pid):
                continue
            try:
                cached: dict[str, Any] = {}
                if cache_path.exists():
                    cached = json.loads(cache_path.read_text(encoding="utf-8"))
                    if cached.get("status") in {"completed", "error", "cancelled"}:
                        os._exit(0)
                _write_cache(
                    cache_path,
                    {
                        **cached,
                        "status": "cancelled",
                        "error": f"parent process {parent_pid} exited",
                        "completed_at": _now(),
                    },
                )
            finally:
                os._exit(130)

    threading.Thread(target=_monitor, daemon=True, name="parent-process-monitor").start()


def _load_extra_tools(extra_tools: list[str]) -> None:
    """Register optional tool sets requested by the task payload."""
    for name in extra_tools:
        if name == "meeting":
            from .tools.meeting import register_moderator_tools
            register_moderator_tools()
        elif name == "kanban_wait":
            from .tools.kanban import register_kanban_wait_complete
            register_kanban_wait_complete()


def _run_agent(payload: dict[str, Any], cache_path: Path) -> None:
    prompt = str(payload.get("user_prompt") or "")
    _load_extra_tools(payload.get("extra_tools") or [])
    agent_role = str(payload.get("agent_role") or "tool_subagent")
    auto_compact = bool(payload.get("auto_compact", True))
    registry = None
    if agent_role == "tool_subagent":
        from .tools import load_builtin_tools, registry as global_registry
        load_builtin_tools()
        registry = global_registry.without(_TOOL_SUBAGENT_EXCLUDED)
    agent = GeneralAgent(
        model=payload.get("model"),
        provider=payload.get("provider"),
        max_iterations=int(payload.get("max_iterations") or 12),
        self_review=False,
        sub_agent=True,
        agent_role=agent_role,
        registry=registry,
        auto_compact=auto_compact,
        ui=ConsoleUI(enabled=False),
        live_cache_path=cache_path,
        live_cache_metadata={
            "kind": payload.get("kind") or "tool_subagent",
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "user_prompt": prompt,
            "auto_compact": auto_compact,
            "started_at": payload.get("started_at"),
        },
    )
    result = agent.run(prompt)
    cached = {
        "kind": payload.get("kind") or "tool_subagent",
        "status": "completed",
        "started_at": payload.get("started_at"),
        "completed_at": _now(),
        "parent_session_id": payload.get("parent_session_id"),
        "parent_task_id": payload.get("parent_task_id"),
        "session_id": result.get("session_id"),
        "session_path": result.get("session_path"),
        "user_prompt": prompt,
        "auto_compact": auto_compact,
        "final": result.get("final", ""),
        "messages": result.get("messages", []),
    }
    _write_cache(cache_path, cached)
    _auto_advance(payload)


def _auto_advance(payload: dict[str, Any]) -> None:
    """After this worker finishes, push the kanban board forward autonomously.

    Spawns all newly-ready tasks whose parents are now done.
    If the board reaches completion (no running/ready tasks remain),
    fires any registered notifications.
    """
    board_name = payload.get("kanban_board")
    if not board_name:
        return
    try:
        from .tools.kanban import (
            _load_board, _save_board, _sync_running,
            _parents_done, _spawn_worker, READY_STATES, TERMINAL_STATES,
            fire_notifications,
        )
        data = _load_board(board_name)
        _sync_running(data)  # marks this task as completed
        runtime = {
            "session_id": payload.get("parent_session_id", ""),
            "task_id":    payload.get("parent_task_id", ""),
        }
        spawned = 0
        for task in sorted(data["tasks"].values(), key=lambda t: t.get("created_at", "")):
            if task.get("status") not in READY_STATES:
                continue
            if not _parents_done(data["tasks"], task):
                continue
            spawn_info = _spawn_worker(task, board_name, runtime)
            task.update(spawn_info)
            task["status"] = "running"
            spawned += 1
        _save_board(data, board_name)
        if spawned:
            print(f"[kanban auto-advance] board={board_name} spawned={spawned}", flush=True)

        # Check if board is now fully complete → fire subscriptions
        all_tasks = list(data.get("tasks", {}).values())
        still_active = any(
            t.get("status") not in TERMINAL_STATES and t.get("status") != "done"
            for t in all_tasks
        )
        if not still_active:
            fire_notifications(board_name, data)

    except Exception as exc:
        print(f"[kanban auto-advance] failed: {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m research_agent.subprocess_worker <payload.json>", file=sys.stderr)
        return 2
    load_dotenv()
    payload_path = Path(sys.argv[1]).resolve()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    cache_path = Path(payload["cache_path"]).resolve()
    _start_parent_monitor(cache_path)

    try:
        if payload.get("kind") in {"tool_subagent", "kanban_worker"}:
            _run_agent(payload, cache_path)
        else:
            raise ValueError(f"Unknown subprocess kind: {payload.get('kind')}")
    except Exception as exc:
        # The agent's own top-level loop only retries transient API errors a couple of
        # times before re-raising (see LLMClient.chat / GeneralAgent.run). If that happens
        # here, this task cannot make further progress on its own - mark it blocked (not a
        # code bug, just "needs a human/main-agent decision") and, critically, still run
        # _auto_advance so the board gets synced and any pending notification actually
        # fires. Without this, a crash here would leave the board stuck on "running"
        # forever, since _auto_advance is normally only called from the success path.
        _write_cache(
            cache_path,
            {
                **payload,
                "status": "blocked",
                "error": f"{type(exc).__name__}: {exc}",
                "completed_at": _now(),
            },
        )
        _auto_advance(payload)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
