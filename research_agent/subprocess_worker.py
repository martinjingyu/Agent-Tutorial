from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent import GeneralAgent
from .env import load_dotenv
from .llm import LLMClient
from .ui import ConsoleUI


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _load_extra_tools(extra_tools: list[str]) -> None:
    """Register optional tool sets requested by the task payload."""
    for name in extra_tools:
        if name == "meeting":
            from .tools.meeting import register_meeting_tools
            register_meeting_tools()
        elif name == "kanban_wait":
            from .tools.kanban import register_kanban_wait_complete
            register_kanban_wait_complete()


def _run_agent(payload: dict[str, Any], cache_path: Path) -> None:
    prompt = str(payload.get("user_prompt") or "")
    _load_extra_tools(payload.get("extra_tools") or [])
    agent = GeneralAgent(
        model=payload.get("model"),
        provider=payload.get("provider"),
        max_iterations=int(payload.get("max_iterations") or 12),
        self_review=False,
        sub_agent=True,
        ui=ConsoleUI(enabled=False),
        live_cache_path=cache_path,
        live_cache_metadata={
            "kind": "plan_subagent",
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "user_prompt": prompt,
            "started_at": payload.get("started_at"),
        },
    )
    result = agent.run(prompt)
    cached = {
        "kind": "plan_subagent",
        "status": "completed",
        "started_at": payload.get("started_at"),
        "completed_at": _now(),
        "parent_session_id": payload.get("parent_session_id"),
        "parent_task_id": payload.get("parent_task_id"),
        "session_id": result.get("session_id"),
        "session_path": result.get("session_path"),
        "user_prompt": prompt,
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


def _run_llm(payload: dict[str, Any], cache_path: Path) -> None:
    system_prompt = str(payload.get("system_prompt") or "")
    user_prompt = str(payload.get("user_prompt") or "")
    _write_cache(
        cache_path,
        {
            "kind": "plan_subllm",
            "status": "running",
            "started_at": payload.get("started_at"),
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        },
    )
    llm = LLMClient(model=payload.get("model"), provider=payload.get("provider"))
    response = llm.chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        [],
    )
    content = response.choices[0].message.content or ""
    _write_cache(
        cache_path,
        {
            "kind": "plan_subllm",
            "status": "completed",
            "started_at": payload.get("started_at"),
            "completed_at": _now(),
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model": llm.model,
            "provider": llm.provider,
            "final": content,
        },
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m research_agent.subprocess_worker <payload.json>", file=sys.stderr)
        return 2
    load_dotenv()
    payload_path = Path(sys.argv[1]).resolve()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    cache_path = Path(payload["cache_path"]).resolve()

    try:
        if payload.get("kind") == "plan_subagent":
            _run_agent(payload, cache_path)
        elif payload.get("kind") == "plan_subllm":
            _run_llm(payload, cache_path)
        else:
            raise ValueError(f"Unknown subprocess kind: {payload.get('kind')}")
    except Exception as exc:
        _write_cache(
            cache_path,
            {
                **payload,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "completed_at": _now(),
            },
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
