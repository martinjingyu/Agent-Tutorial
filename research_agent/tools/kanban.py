from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ..paths import PROJECT_ROOT, SESSIONS_DIR
from .registry import json_result, registry


KANBAN_DIR = SESSIONS_DIR / "kanban"
NOTIFY_DIR  = KANBAN_DIR / "subscriptions"
DEFAULT_BOARD = "default"
READY_STATES = {"ready"}
TERMINAL_STATES = {"done", "blocked", "error", "cancelled"}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _board_path(board: str | None = None) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in (board or DEFAULT_BOARD))
    return KANBAN_DIR / f"{safe}.json"


def _empty_board(board: str | None = None) -> dict[str, Any]:
    return {
        "board": board or DEFAULT_BOARD,
        "created_at": _now(),
        "updated_at": _now(),
        "tasks": {},
        "events": [],
    }


def _load_board(board: str | None = None) -> dict[str, Any]:
    path = _board_path(board)
    if not path.exists():
        return _empty_board(board)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("board root is not an object")
        data.setdefault("board", board or DEFAULT_BOARD)
        data.setdefault("tasks", {})
        data.setdefault("events", [])
        return data
    except Exception:
        corrupt = path.with_suffix(path.suffix + f".corrupt.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        path.replace(corrupt)
        data = _empty_board(board)
        data["events"].append({"time": _now(), "kind": "board_recovered", "corrupt_path": str(corrupt)})
        return data


def _save_board(data: dict[str, Any], board: str | None = None) -> None:
    path = _board_path(board or data.get("board"))
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _event(data: dict[str, Any], kind: str, **payload: Any) -> None:
    data.setdefault("events", []).append({"time": _now(), "kind": kind, **payload})


def _task_id(prefix: str = "t") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _cache_paths(board: str, task_id: str) -> tuple[Path, Path, Path]:
    root = KANBAN_DIR / board / "workers"
    cache_path = root / f"{task_id}.json"
    payload_path = root / f"{task_id}.payload.json"
    stdout_path = root / f"{task_id}.stdout.txt"
    return cache_path, payload_path, stdout_path


def _spawn_worker(task: dict[str, Any], board: str, runtime: dict[str, Any]) -> dict[str, Any]:
    cache_path, payload_path, stdout_path = _cache_paths(board, task["id"])
    stderr_path = stdout_path.with_name(stdout_path.name.replace(".stdout.", ".stderr."))
    started_at = _now()
    prompt = _worker_prompt(task, board)
    payload = {
        "kind": "plan_subagent",
        "status": "queued",
        "run_id": f"kanban_{task['id']}",
        "cache_path": str(cache_path),
        "payload_path": str(payload_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "started_at": started_at,
        "parent_session_id": runtime.get("session_id"),
        "parent_task_id": runtime.get("task_id"),
        "provider": task.get("provider"),
        "model": task.get("model"),
        "max_iterations": task.get("max_iterations") or 16,
        "user_prompt": prompt,
        "system_prompt": "",
        "extra_tools": task.get("extra_tools") or [],
        # Auto-advance: worker uses these to push the board forward on completion
        "kanban_board": board,
        "kanban_task_id": task["id"],
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    kwargs: dict[str, Any] = {}
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
    return {
        "pid": int(proc.pid),
        "cache_path": str(cache_path),
        "payload_path": str(payload_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "started_at": started_at,
    }


def _worker_prompt(task: dict[str, Any], board: str) -> str:
    skill = str(task.get("skill") or "").strip()
    skill_block = ""
    if skill:
        skill_block = (
            f"\nBefore acting, call skill_view with name='{skill}' and follow that skill. "
            "If the skill is missing, continue with the task and report that gap.\n"
        )
    parents = task.get("parents") or []
    parent_note = f"\nParent tasks already completed: {parents}\n" if parents else ""
    return f"""You are a Kanban worker subagent.

Board: {board}
Task id: {task.get('id')}
Title: {task.get('title')}
{skill_block}{parent_note}
Task prompt:
{task.get('prompt') or task.get('body') or ''}

Work autonomously. Use tools as needed. Prefer saving durable files or reports when the task asks for output.
End with respond_to_user containing a concise completion summary, files touched, and any blockers.
"""


def _parents_done(tasks: dict[str, dict[str, Any]], task: dict[str, Any]) -> bool:
    for parent_id in task.get("parents") or []:
        parent = tasks.get(parent_id)
        if not parent or parent.get("status") != "done":
            return False
    return True


def _sync_running(data: dict[str, Any]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for task in data.get("tasks", {}).values():
        if task.get("status") != "running":
            continue
        cache_path = task.get("cache_path")
        if not cache_path:
            continue
        path = Path(cache_path)
        if not path.exists():
            continue
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = cached.get("status")
        if status == "completed":
            task["status"] = "done"
            task["completed_at"] = cached.get("completed_at") or _now()
            task["final"] = cached.get("final", "")
            task["session_path"] = cached.get("session_path")
            updates.append({"task_id": task["id"], "status": "done"})
            _event(data, "task_done", task_id=task["id"], cache_path=cache_path)
        elif status == "error":
            task["status"] = "error"
            task["completed_at"] = cached.get("completed_at") or _now()
            task["error"] = cached.get("error", "worker error")
            updates.append({"task_id": task["id"], "status": "error", "error": task["error"]})
            _event(data, "task_error", task_id=task["id"], error=task["error"])
    return updates


def _create_task(
    data: dict[str, Any],
    *,
    title: str,
    prompt: str,
    skill: str | None = None,
    parents: list[str] | None = None,
    status: str = "ready",
    metadata: dict[str, Any] | None = None,
    max_iterations: int | None = None,
    provider: str | None = None,
    model: str | None = None,
    extra_tools: list[str] | None = None,
) -> dict[str, Any]:
    task = {
        "id": _task_id(),
        "title": title,
        "prompt": prompt,
        "skill": skill,
        "parents": parents or [],
        "status": status,
        "created_at": _now(),
        "updated_at": _now(),
        "metadata": metadata or {},
        "max_iterations": max_iterations,
        "provider": provider,
        "model": model,
        "extra_tools": extra_tools or [],
    }
    data.setdefault("tasks", {})[task["id"]] = task
    _event(data, "task_created", task_id=task["id"], title=title, status=status, parents=task["parents"])
    return task


def _handle_create_task(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    title = str(args.get("title") or "").strip()
    prompt = str(args.get("prompt") or args.get("body") or "").strip()
    if not title or not prompt:
        return json_result(success=False, error="title and prompt are required")
    data = _load_board(board_name)
    task = _create_task(
        data,
        title=title,
        prompt=prompt,
        skill=args.get("skill"),
        parents=[str(x) for x in (args.get("parents") or [])],
        status=str(args.get("status") or "ready"),
        metadata=args.get("metadata") if isinstance(args.get("metadata"), dict) else None,
        max_iterations=args.get("max_iterations"),
        provider=args.get("provider"),
        model=args.get("model"),
    )
    _save_board(data, board_name)
    return json_result(success=True, board=board_name, task=task, board_path=str(_board_path(board_name)))


def _handle_create_pipeline(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    raw_tasks = args.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        return json_result(success=False, error="tasks must be a non-empty array")

    data = _load_board(board_name)
    created: list[dict[str, Any]] = []
    alias_to_id: dict[str, str] = {}
    sequential = bool(args.get("sequential", False))
    previous_id: str | None = None

    for index, raw in enumerate(raw_tasks, start=1):
        if not isinstance(raw, dict):
            return json_result(success=False, error=f"tasks[{index}] must be an object")
        title = str(raw.get("title") or "").strip()
        prompt = str(raw.get("prompt") or raw.get("body") or "").strip()
        if not title or not prompt:
            return json_result(success=False, error=f"tasks[{index}] requires title and prompt")

        parents: list[str] = []
        for parent in raw.get("parents") or raw.get("depends_on") or []:
            parent_id = alias_to_id.get(str(parent), str(parent))
            parents.append(parent_id)
        if sequential and previous_id and not parents:
            parents = [previous_id]

        task = _create_task(
            data,
            title=title,
            prompt=prompt,
            skill=raw.get("skill") or args.get("default_skill"),
            parents=parents,
            status=str(raw.get("status") or "ready"),
            metadata=raw.get("metadata") if isinstance(raw.get("metadata"), dict) else None,
            max_iterations=raw.get("max_iterations") or args.get("max_iterations"),
            provider=raw.get("provider") or args.get("provider"),
            model=raw.get("model") or args.get("model"),
        )
        alias = raw.get("id") or raw.get("alias")
        if alias:
            alias_to_id[str(alias)] = task["id"]
        created.append(task)
        previous_id = task["id"]

    _save_board(data, board_name)
    return json_result(
        success=True,
        board=board_name,
        created_count=len(created),
        tasks=created,
        alias_to_id=alias_to_id,
        board_path=str(_board_path(board_name)),
        next_step=(
            "Call kanban_dispatch once to start workers, then call respond_to_user to end this turn. "
            "DO NOT call kanban_dispatch repeatedly — workers run in the background."
        ),
    )


def _handle_create_cv_pipeline(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or "cv-screening")
    stage = str(args.get("stage") or "1")
    workspace = str(args.get("workspace") or r"C:\Users\LX034\Code\CVScreeningAgent\workspace\candidates")
    candidates = [str(x) for x in (args.get("candidates") or [])]
    force = bool(args.get("force"))
    config = args.get("config")
    max_iterations = int(args.get("max_iterations") or 18)
    if not candidates and not args.get("batch"):
        return json_result(success=False, error="Provide candidates or set batch=true")

    data = _load_board(board_name)
    created: list[dict[str, Any]] = []
    base_cmd = [
        "python",
        r"C:\Users\LX034\Code\CVScreeningAgent\ScreeningPipeline\main.py",
        stage,
    ]
    if config:
        base_cmd.extend(["--config", str(config)])
    if force:
        base_cmd.append("--force")

    if args.get("batch"):
        cmd = [*base_cmd, "--workspace", workspace, "--batch"]
        prompt = _cv_worker_prompt(cmd, workspace, stage, "batch")
        created.append(_create_task(
            data,
            title=f"Run CV screening pipeline stage {stage} for batch",
            prompt=prompt,
            skill="cv-screening-pipeline-worker",
            parents=[],
            max_iterations=max_iterations,
            provider=args.get("provider"),
            model=args.get("model"),
            metadata={"kind": "cv_pipeline", "stage": stage, "workspace": workspace, "batch": True, "command": cmd},
        ))
    else:
        previous_id: str | None = None
        sequential = bool(args.get("sequential", True))
        for candidate in candidates:
            parents = [previous_id] if sequential and previous_id else []
            cmd = [*base_cmd, "--workspace", workspace, candidate]
            prompt = _cv_worker_prompt(cmd, workspace, stage, candidate)
            task = _create_task(
                data,
                title=f"Run CV screening pipeline stage {stage} for candidate {candidate}",
                prompt=prompt,
                skill="cv-screening-pipeline-worker",
                parents=parents,
                max_iterations=max_iterations,
                provider=args.get("provider"),
                model=args.get("model"),
                metadata={"kind": "cv_pipeline", "stage": stage, "workspace": workspace, "candidate": candidate, "command": cmd},
            )
            created.append(task)
            previous_id = task["id"]

    _save_board(data, board_name)
    return json_result(
        success=True,
        board=board_name,
        created_count=len(created),
        tasks=created,
        board_path=str(_board_path(board_name)),
        next_step=(
            "Call kanban_dispatch once to start workers, then call respond_to_user to end this turn. "
            "DO NOT call kanban_dispatch repeatedly — workers run in the background."
        ),
    )


def _cv_worker_prompt(cmd: list[str], workspace: str, stage: str, label: str) -> str:
    command = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    if "--force" in cmd:
        command = f"echo y | {command}"
    return f"""Run the CVScreeningAgent pipeline task.

Target: {label}
Stage: {stage}
Workspace: {workspace}

Command to run from C:\\Users\\LX034\\Code\\CVScreeningAgent:
{command}

Steps:
1. Inspect the relevant candidate folder if useful.
2. Run the command with terminal.
3. If it fails, inspect the error and make one narrow fix or retry only when clearly safe.
4. Verify expected outputs such as stage1_profile.json, stage1_verdict.json, or stage1_report.md when applicable.
5. Finish with a concise summary: command run, status, output files, and blockers.
"""


def _polling_hint(tasks: list[dict]) -> str:
    running = sum(1 for t in tasks if t.get("status") == "running")
    if running:
        return (
            f"{running} task(s) still running. "
            "DO NOT call kanban_list_tasks or kanban_show_task again to poll — "
            "workers advance the board automatically. "
            "Use kanban_notify_subscribe then respond_to_user, "
            "or kanban_wait_complete, to handle completion."
        )
    return ""


def _handle_list(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    data = _load_board(board_name)
    updates = _sync_running(data)
    if updates:
        _save_board(data, board_name)
    status_filter = args.get("status")
    tasks = list(data.get("tasks", {}).values())
    if status_filter:
        tasks = [t for t in tasks if t.get("status") == status_filter]
    tasks.sort(key=lambda t: t.get("created_at", ""))
    hint = _polling_hint(list(data.get("tasks", {}).values()))
    return json_result(success=True, board=board_name, tasks=tasks, count=len(tasks),
                       synced=updates, **({} if not hint else {"hint": hint}))


def _handle_show(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    task_id = str(args.get("task_id") or "")
    data = _load_board(board_name)
    updates = _sync_running(data)
    task = data.get("tasks", {}).get(task_id)
    if updates:
        _save_board(data, board_name)
    if not task:
        return json_result(success=False, error=f"Task not found: {task_id}", board=board_name)
    hint = _polling_hint(list(data.get("tasks", {}).values()))
    return json_result(success=True, board=board_name, task=task,
                       synced=updates, **({} if not hint else {"hint": hint}))


def _handle_update(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    task_id = str(args.get("task_id") or "")
    data = _load_board(board_name)
    task = data.get("tasks", {}).get(task_id)
    if not task:
        return json_result(success=False, error=f"Task not found: {task_id}")
    status = args.get("status")
    if status:
        task["status"] = str(status)
    if "note" in args:
        task.setdefault("notes", []).append({"time": _now(), "text": str(args.get("note") or "")})
    task["updated_at"] = _now()
    _event(data, "task_updated", task_id=task_id, status=task.get("status"))
    _save_board(data, board_name)
    return json_result(success=True, board=board_name, task=task)


def _handle_dispatch(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    max_spawn = int(args.get("max_spawn") or 1)
    data = _load_board(board_name)
    tasks = data.setdefault("tasks", {})
    synced = _sync_running(data)
    spawned: list[dict[str, Any]] = []

    for task in sorted(tasks.values(), key=lambda t: t.get("created_at", "")):
        if len(spawned) >= max_spawn:
            break
        if task.get("status") not in READY_STATES:
            continue
        if not _parents_done(tasks, task):
            continue
        spawn_info = _spawn_worker(task, board_name, runtime)
        task.update(spawn_info)
        task["status"] = "running"
        task["updated_at"] = _now()
        spawned.append({"task_id": task["id"], "title": task.get("title"), **spawn_info})
        _event(data, "task_spawned", task_id=task["id"], pid=spawn_info["pid"])

    _save_board(data, board_name)
    remaining_ready = [
        t["id"] for t in tasks.values()
        if t.get("status") in READY_STATES and _parents_done(tasks, t)
    ]
    running = [t["id"] for t in tasks.values() if t.get("status") == "running"]
    if running or remaining_ready:
        hint = (
            f"Workers running in background — running={len(running)}, ready={len(remaining_ready)}. "
            "DO NOT call kanban_dispatch again. "
            "Call respond_to_user to end this turn; the user will resume when ready."
        )
    else:
        all_tasks = list(tasks.values())
        n_done    = sum(1 for t in all_tasks if t.get("status") == "done")
        n_blocked = sum(1 for t in all_tasks if t.get("status") in ("blocked", "error", "cancelled"))
        hint = (
            f"Pipeline complete. done={n_done}, blocked/error={n_blocked}. "
            "No need to call kanban_dispatch again unless you add more tasks."
        )
    return json_result(
        success=True,
        board=board_name,
        synced=synced,
        spawned=spawned,
        running=running,
        ready=remaining_ready,
        board_path=str(_board_path(board_name)),
        hint=hint,
    )


def _handle_create_meeting_task(args: dict, runtime: dict) -> str:
    board_name   = str(args.get("board") or DEFAULT_BOARD)
    title        = str(args.get("title") or "").strip()
    topic        = str(args.get("topic") or "").strip()
    participants = args.get("suggested_participants") or []
    if not title or not topic:
        return json_result(success=False, error="title and topic are required")

    # Build moderator prompt from topic + participant suggestions
    parts = [f"Topic: {topic}"]
    if participants:
        lines = "\n".join(f"  - {p}" for p in participants)
        parts.append(f"Suggested participants:\n{lines}")
    parts.append(
        "You are the meeting moderator. Load the meeting_moderator skill, "
        "then create the participants and run the discussion as you see fit. "
        "End with meeting_conclude."
    )
    prompt = "\n\n".join(parts)

    data = _load_board(board_name)
    task = _create_task(
        data,
        title=title,
        prompt=prompt,
        skill="meeting_moderator",
        parents=[str(x) for x in (args.get("parents") or [])],
        status=str(args.get("status") or "ready"),
        max_iterations=args.get("max_iterations") or 30,
        provider=args.get("provider"),
        model=args.get("model"),
        extra_tools=["meeting"],   # always included — moderator needs meeting tools
    )
    _save_board(data, board_name)
    return json_result(success=True, board=board_name, task=task,
                       hint="Meeting task created with meeting tools pre-enabled. Call kanban_dispatch to start.")


registry.register("kanban_create_meeting_task", {
    "description": (
        "Create a kanban task that runs a meeting moderator agent. "
        "The moderator decides the discussion format dynamically (ask_one / chain / group_discuss). "
        "You only need to specify the topic and optionally suggest participants — "
        "the moderator handles everything else. Meeting tools are enabled automatically."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "board":   {"type": "string", "default": DEFAULT_BOARD},
            "title":   {"type": "string", "description": "Short task title for the kanban board"},
            "topic":   {"type": "string", "description": "What the meeting should resolve or discuss"},
            "suggested_participants": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of participant descriptions, e.g. ['Alice: software architect', 'Bob: security expert']. The moderator may adjust.",
            },
            "parents":        {"type": "array", "items": {"type": "string"}, "description": "Task IDs this meeting depends on"},
            "status":         {"type": "string", "enum": ["ready", "todo", "blocked"], "default": "ready"},
            "max_iterations": {"type": "integer", "default": 30},
            "provider":       {"type": "string"},
            "model":          {"type": "string"},
        },
        "required": ["title", "topic"],
    },
}, _handle_create_meeting_task)


registry.register("kanban_create_task", {
    "description": "Create a persistent Kanban task for a future subagent. Use parents to enforce order; use skill to tell the worker which skill_view to load.",
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "title": {"type": "string"},
            "prompt": {"type": "string"},
            "body": {"type": "string"},
            "skill": {"type": "string"},
            "parents": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string", "enum": ["ready", "todo", "blocked"], "default": "ready"},
            "metadata": {"type": "object"},
            "max_iterations": {"type": "integer", "default": 16},
            "provider": {"type": "string", "enum": ["deepseek", "codex", "openai"]},
            "model": {"type": "string"},
        },
        "required": ["title", "prompt"],
    },
}, _handle_create_task)

registry.register("kanban_create_pipeline", {
    "description": (
        "Create a generic ordered or dependency-based Kanban pipeline from task specs. "
        "This is domain-neutral: encode project-specific work in each task prompt and optional skill. "
        "Use aliases in depends_on/parents to refer to earlier tasks in the same call."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "sequential": {"type": "boolean", "default": False, "description": "If true, each task depends on the previous task unless it already has parents/depends_on."},
            "default_skill": {"type": "string", "description": "Optional skill applied to tasks that do not specify their own skill."},
            "max_iterations": {"type": "integer", "default": 16},
            "provider": {"type": "string", "enum": ["deepseek", "codex", "openai"]},
            "model": {"type": "string"},
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Optional local alias used by later tasks' depends_on."},
                        "alias": {"type": "string", "description": "Alias alternative to id."},
                        "title": {"type": "string"},
                        "prompt": {"type": "string"},
                        "body": {"type": "string"},
                        "skill": {"type": "string"},
                        "parents": {"type": "array", "items": {"type": "string"}},
                        "depends_on": {"type": "array", "items": {"type": "string"}},
                        "status": {"type": "string", "enum": ["ready", "todo", "blocked"], "default": "ready"},
                        "metadata": {"type": "object"},
                        "max_iterations": {"type": "integer"},
                        "provider": {"type": "string", "enum": ["deepseek", "codex", "openai"]},
                        "model": {"type": "string"},
                    },
                    "required": ["title", "prompt"],
                },
            },
        },
        "required": ["tasks"],
    },
}, _handle_create_pipeline)

registry.register("kanban_list_tasks", {
    "description": "List Kanban tasks, syncing completed running workers from their cache files first.",
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "status": {"type": "string"},
        },
        "required": [],
    },
}, _handle_list)

registry.register("kanban_show_task", {
    "description": "Show one Kanban task, including worker cache path, status, final summary, and errors.",
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "task_id": {"type": "string"},
        },
        "required": ["task_id"],
    },
}, _handle_show)

registry.register("kanban_update_task", {
    "description": "Manually update a Kanban task status or append a note.",
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "task_id": {"type": "string"},
            "status": {"type": "string", "enum": ["ready", "todo", "running", "blocked", "done", "error", "cancelled"]},
            "note": {"type": "string"},
        },
        "required": ["task_id"],
    },
}, _handle_update)

def _handle_wait_complete(args: dict, runtime: dict) -> str:
    """Blocking wait — polls until all board tasks reach a terminal state.

    No LLM calls are made during the wait.  Intended for non-interactive
    contexts (subprocesses, batch pipelines) where blocking is acceptable.
    NOT registered by default; call register_kanban_wait_complete() to opt in.
    """
    import time as _time

    board_name = str(args.get("board") or DEFAULT_BOARD)
    timeout    = float(args.get("timeout") or 3600)
    poll       = float(args.get("poll_interval") or 3.0)

    deadline = _time.monotonic() + timeout
    while _time.monotonic() < deadline:
        data = _load_board(board_name)
        _sync_running(data)
        _save_board(data, board_name)
        all_tasks = list(data["tasks"].values())
        still_active = any(
            t.get("status") not in TERMINAL_STATES and t.get("status") != "done"
            for t in all_tasks
        )
        if not still_active:
            n_done  = sum(1 for t in all_tasks if t.get("status") == "done")
            n_error = sum(1 for t in all_tasks if t.get("status") in ("error", "blocked", "cancelled"))
            summaries = [
                {
                    "id":     t["id"],
                    "title":  t.get("title"),
                    "status": t.get("status"),
                    "final":  (t.get("final") or "")[:500],
                }
                for t in sorted(all_tasks, key=lambda t: t.get("created_at", ""))
            ]
            return json_result(
                success=True, board=board_name,
                done=n_done, error=n_error, tasks=summaries,
                hint="All tasks complete. Review results and continue.",
            )
        _time.sleep(poll)

    return json_result(
        success=False, error="timeout", board=board_name,
        hint="Pipeline timed out — some tasks may still be running.",
    )


def register_kanban_wait_complete() -> None:
    """Opt-in: register the blocking kanban_wait_complete tool.

    Call this once at startup in non-interactive contexts (e.g. ScreeningPipeline).
    Do NOT call in interactive CLI agents — use kanban_notify_subscribe instead.
    """
    registry.register(
        "kanban_wait_complete",
        {
            "description": (
                "Block and wait for ALL tasks on a Kanban board to finish. "
                "Polls the board every poll_interval seconds without using LLM tokens. "
                "Returns full task results when the pipeline is complete. "
                "Use this instead of kanban_notify_subscribe in batch/subprocess contexts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "board":          {"type": "string", "default": DEFAULT_BOARD},
                    "timeout":        {"type": "number", "default": 3600, "description": "Max seconds to wait."},
                    "poll_interval":  {"type": "number", "default": 3.0,  "description": "Seconds between status checks."},
                },
                "required": [],
            },
        },
        _handle_wait_complete,
    )


def _handle_notify_subscribe(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    events     = args.get("events") or ["pipeline_complete"]
    on_complete_prompt = str(args.get("on_complete_prompt") or "").strip()
    sub_id = _task_id("sub")
    sub = {
        "sub_id":            sub_id,
        "board":             board_name,
        "events":            events,
        "on_complete_prompt": on_complete_prompt,
        "subscribed_at":     _now(),
    }
    NOTIFY_DIR.mkdir(parents=True, exist_ok=True)
    (NOTIFY_DIR / f"{board_name}_{sub_id}.json").write_text(
        json.dumps(sub, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return json_result(
        success=True,
        sub_id=sub_id,
        board=board_name,
        hint=(
            "Subscription active. Call respond_to_user now to end this turn. "
            "You will be notified automatically when the pipeline completes."
        ),
    )


def fire_notifications(board_name: str, data: dict[str, Any]) -> None:
    """Called by subprocess_worker when a board reaches completion.

    Writes a pending-event file for each matching subscription.
    The pending file is read by GeneralAgent.run() on the next invocation
    and injected into the conversation history so the agent can review results.
    Subscriptions are one-shot: deleted after firing.
    """
    if not NOTIFY_DIR.exists():
        return
    all_tasks = list(data.get("tasks", {}).values())
    n_done    = sum(1 for t in all_tasks if t.get("status") == "done")
    n_error   = sum(1 for t in all_tasks if t.get("status") in ("error", "blocked", "cancelled"))
    task_summaries = [
        {"id": t["id"], "title": t.get("title"), "status": t.get("status"),
         "final": (t.get("final") or "")[:300]}
        for t in sorted(all_tasks, key=lambda t: t.get("created_at", ""))
    ]

    for sub_file in sorted(NOTIFY_DIR.glob(f"{board_name}_sub_*.json")):
        try:
            sub = json.loads(sub_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "pipeline_complete" not in sub.get("events", []):
            continue

        pending = {
            "event":             "pipeline_complete",
            "board":             board_name,
            "fired_at":          _now(),
            "sub_id":            sub.get("sub_id"),
            "on_complete_prompt": sub.get("on_complete_prompt") or "",
            "summary":           {"done": n_done, "error": n_error},
            "tasks":             task_summaries,
        }
        pending_path = NOTIFY_DIR / f"{board_name}_pending_{sub['sub_id']}.json"
        pending_path.write_text(json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8")
        sub_file.unlink(missing_ok=True)

        # Also print a one-liner so the user knows to resume the agent
        sys.stdout.write(
            f"\n[kanban] Board '{board_name}' complete — "
            f"done={n_done}, error={n_error}. Resume your agent to review.\n"
        )
        sys.stdout.flush()


def consume_pending_notifications() -> list[dict[str, Any]]:
    """Read all pending notification files and return them as injected messages.

    Called by GeneralAgent.run() at startup.  Each pending event becomes a
    tool-result-style message in history so the agent sees it naturally.
    Pending files are deleted after reading (one-shot).
    """
    if not NOTIFY_DIR.exists():
        return []
    messages: list[dict[str, Any]] = []
    for pending_file in sorted(NOTIFY_DIR.glob("*_pending_*.json")):
        try:
            event = json.loads(pending_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        board    = event.get("board", "?")
        summary  = event.get("summary", {})
        tasks    = event.get("tasks", [])
        extra    = event.get("on_complete_prompt", "")
        task_lines = "\n".join(
            f"  [{t['status']}] {t['title']}: {t['final']}" for t in tasks
        )
        content = (
            f"[kanban notification] Board '{board}' pipeline_complete\n"
            f"done={summary.get('done',0)}, error={summary.get('error',0)}\n\n"
            f"Task results:\n{task_lines}"
        )
        if extra:
            content += f"\n\nRequested follow-up: {extra}"
        messages.append({"role": "user", "content": content})
        pending_file.unlink(missing_ok=True)
    return messages


registry.register("kanban_notify_subscribe", {
    "description": (
        "Subscribe to kanban board events so the agent does NOT need to poll. "
        "After calling this, call respond_to_user to end the turn. "
        "A notification subprocess will automatically fire when the pipeline completes, "
        "printing results to the terminal without requiring agent intervention."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "board": {
                "type": "string",
                "default": DEFAULT_BOARD,
                "description": "Board to watch.",
            },
            "events": {
                "type": "array",
                "items": {"type": "string", "enum": ["pipeline_complete"]},
                "default": ["pipeline_complete"],
                "description": "Event types to subscribe to.",
            },
            "on_complete_prompt": {
                "type": "string",
                "description": "Optional: extra instruction injected into the notification agent's prompt.",
            },
        },
        "required": [],
    },
}, _handle_notify_subscribe)


registry.register("kanban_dispatch", {
    "description": "Sync running Kanban workers, then spawn ready tasks whose parents are done. Call repeatedly to advance a pipeline.",
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "max_spawn": {"type": "integer", "default": 1},
        },
        "required": [],
    },
}, _handle_dispatch)
