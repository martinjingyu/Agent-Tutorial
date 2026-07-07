from __future__ import annotations

import json
import os
import shutil
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


def _new_board_name(prefix: str, seed: str) -> str:
    import re

    slug = re.sub(r"[^\w\s.-]", "", seed.lower()).strip()
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")[:48].rstrip("-")
    return f"{prefix}-{slug or uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}"


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
        "kind": "kanban_worker",
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
        "auto_compact": task.get("auto_compact", True),
        "user_prompt": prompt,
        "system_prompt": "",
        "agent_role": "meeting_moderator" if str(task.get("skill") or "") == "meeting_moderator" else "kanban_worker",
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
    resume_context = str(task.get("resume_context") or "").strip()
    resume_block = f"\nResume context from previous attempt:\n{resume_context}\n" if resume_context else ""
    return f"""You are a Kanban worker subagent.

Board: {board}
Task id: {task.get('id')}
Title: {task.get('title')}
{skill_block}{parent_note}{resume_block}
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


WORKER_TIMEOUT_SECONDS = 2700  # 45 min hard kill: 120s LLM timeout 脳 16 iter 脳 1.4 buffer


def _kill_pid(pid: int) -> None:
    try:
        import signal
        os.kill(pid, signal.SIGTERM if os.name != "nt" else signal.SIGTERM)
    except Exception:
        try:
            import ctypes
            ctypes.windll.kernel32.TerminateProcess(
                ctypes.windll.kernel32.OpenProcess(1, False, pid), 1
            )
        except Exception:
            pass


def _sync_running(data: dict[str, Any]) -> list[dict[str, Any]]:
    from datetime import datetime as _dt
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
        elif status == "cancelled":
            task["status"] = "cancelled"
            task["completed_at"] = cached.get("completed_at") or _now()
            task["error"] = cached.get("error", "worker cancelled")
            updates.append({"task_id": task["id"], "status": "cancelled", "error": task["error"]})
            _event(data, "task_cancelled", task_id=task["id"], error=task["error"])
        elif status == "blocked":
            # Worker's own top-level agent loop raised (e.g. exhausted-retry API error) and
            # could not make further progress. Not a code bug - just needs a human/main-agent
            # decision (retry via kanban_retry_task, or replan). See subprocess_worker.main().
            task["status"] = "blocked"
            task["completed_at"] = cached.get("completed_at") or _now()
            task["error"] = cached.get("error", "worker blocked")
            task["final"] = cached.get("final", "")
            updates.append({"task_id": task["id"], "status": "blocked", "error": task["error"]})
            _event(data, "task_blocked", task_id=task["id"], error=task["error"])
        else:
            # Check for hung worker: started_at too long ago 鈫?kill and mark error
            started = task.get("started_at") or cached.get("started_at")
            if started:
                try:
                    elapsed = (_dt.now() - _dt.fromisoformat(started)).total_seconds()
                    if elapsed > WORKER_TIMEOUT_SECONDS:
                        pid = task.get("pid") or cached.get("pid")
                        if pid:
                            _kill_pid(int(pid))
                        err = f"worker timeout after {int(elapsed)}s"
                        task["status"] = "error"
                        task["completed_at"] = _now()
                        task["error"] = err
                        updates.append({"task_id": task["id"], "status": "error", "error": err})
                        _event(data, "task_error", task_id=task["id"], error=err)
                except Exception:
                    pass

    # Cascade: a task whose parent(s) are permanently stuck (error/blocked/cancelled - terminal
    # but never "done") can never satisfy _parents_done and will never be spawned. Without this,
    # it would sit in "ready"/"todo" forever, and the board would never reach a state where
    # pipeline_complete notifications fire (see _auto_advance's still_active check below) - the
    # main agent's kanban_notify_subscribe would then wait forever for a notification that never
    # comes, even though the failure itself was already surfaced.
    changed = True
    while changed:
        changed = False
        for task in data.get("tasks", {}).values():
            if task.get("status") not in ("ready", "todo"):
                continue
            for parent_id in task.get("parents") or []:
                parent = data["tasks"].get(parent_id)
                if parent and parent.get("status") in ("error", "blocked", "cancelled"):
                    err = f"parent task {parent_id} did not complete (status={parent.get('status')})"
                    task["status"] = "blocked"
                    task["completed_at"] = _now()
                    task["error"] = err
                    updates.append({"task_id": task["id"], "status": "blocked", "error": err})
                    _event(data, "task_blocked", task_id=task["id"], error=err)
                    changed = True
                    break

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
    auto_compact: bool | None = None,
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
        "auto_compact": True if auto_compact is None else bool(auto_compact),
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
        auto_compact=args.get("auto_compact"),
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
            auto_compact=raw.get("auto_compact", args.get("auto_compact")),
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
            "DO NOT call kanban_dispatch repeatedly 鈥?workers run in the background."
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
            auto_compact=args.get("auto_compact"),
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
                auto_compact=args.get("auto_compact"),
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
            "DO NOT call kanban_dispatch repeatedly 鈥?workers run in the background."
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
            "DO NOT call kanban_list_tasks or kanban_show_task again to poll 鈥?"
            "workers advance the board automatically. "
            "Use kanban_notify_subscribe then respond_to_user to handle completion."
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


def _handle_list_boards(args: dict, runtime: dict) -> str:
    KANBAN_DIR.mkdir(parents=True, exist_ok=True)
    boards: list[dict[str, Any]] = []
    for path in sorted(KANBAN_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        board_name = str(data.get("board") or path.stem)
        tasks = list((data.get("tasks") or {}).values())
        status_counts: dict[str, int] = {}
        for task in tasks:
            if not isinstance(task, dict):
                continue
            status = str(task.get("status") or "ready")
            status_counts[status] = status_counts.get(status, 0) + 1
        has_active = any(
            status not in TERMINAL_STATES and status != "done"
            for status in status_counts
        )
        boards.append(
            {
                "name": board_name,
                "task_count": len(tasks),
                "status_counts": status_counts,
                "has_active": has_active,
                "updated_at": data.get("updated_at"),
                "path": str(path),
            }
        )
    active_only = bool(args.get("active_only"))
    if active_only:
        boards = [board for board in boards if board["has_active"]]
    return json_result(success=True, boards=boards, count=len(boards))


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


def _read_json_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _session_tail(session_path: str | None, *, limit: int = 8) -> list[dict[str, str]]:
    if not session_path:
        return []
    try:
        data = json.loads(Path(session_path).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
    except Exception:
        return []
    tail: list[dict[str, str]] = []
    for msg in data[-limit:]:
        if not isinstance(msg, dict) or msg.get("__meta__"):
            continue
        role = str(msg.get("role") or "")
        content = str(msg.get("content") or "")
        if not role or not content:
            continue
        tail.append({"role": role, "content": content[:1000]})
    return tail


def _build_resume_context(task: dict[str, Any], cached: dict[str, Any]) -> str:
    parts = [
        "A previous attempt for this same kanban task was interrupted or failed.",
        f"Previous status: {task.get('status') or cached.get('status') or 'unknown'}",
    ]
    if task.get("error") or cached.get("error"):
        parts.append(f"Previous error: {task.get('error') or cached.get('error')}")
    if cached.get("final") or task.get("final"):
        parts.append("Previous final/partial result:\n" + str(cached.get("final") or task.get("final"))[:2000])
    session_path = str(cached.get("session_path") or task.get("session_path") or "")
    if session_path:
        parts.append(f"Previous session path: {session_path}")
        tail = _session_tail(session_path)
        if tail:
            lines = [f"- {m['role']}: {m['content']}" for m in tail]
            parts.append("Recent messages from previous attempt:\n" + "\n".join(lines))
    parts.append("Continue the original task. Do not redo completed work when prior artifacts or messages show it is already done.")
    return "\n\n".join(parts)


def _archive_current_attempt(task: dict[str, Any], board_name: str) -> dict[str, Any]:
    attempts = task.setdefault("attempts", [])
    attempt_no = len(attempts) + 1
    archive_root = KANBAN_DIR / board_name / "workers" / "attempts"
    archive_root.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "attempt": attempt_no,
        "archived_at": _now(),
        "status": task.get("status"),
        "pid": task.get("pid"),
        "cache_path": task.get("cache_path"),
        "payload_path": task.get("payload_path"),
        "stdout_path": task.get("stdout_path"),
        "stderr_path": task.get("stderr_path"),
        "session_path": task.get("session_path"),
        "error": task.get("error"),
        "completed_at": task.get("completed_at"),
    }
    for key in ("cache_path", "payload_path", "stdout_path", "stderr_path"):
        source = task.get(key)
        if not source:
            continue
        src = Path(str(source))
        if not src.exists():
            continue
        dst = archive_root / f"{task['id']}.attempt{attempt_no}.{key}{src.suffix}"
        shutil.copy2(src, dst)
        record[f"archived_{key}"] = str(dst)
    attempts.append(record)
    return record


def _handle_retry_task(args: dict, runtime: dict) -> str:
    board_name = str(args.get("board") or DEFAULT_BOARD)
    task_id = str(args.get("task_id") or "")
    mode = str(args.get("mode") or "resume")
    force = bool(args.get("force"))
    if mode not in {"retry", "resume"}:
        return json_result(success=False, error="mode must be retry or resume")

    data = _load_board(board_name)
    updates = _sync_running(data)
    task = data.get("tasks", {}).get(task_id)
    if not task:
        return json_result(success=False, error=f"Task not found: {task_id}", board=board_name)

    status = str(task.get("status") or "")
    if status == "running" and not force:
        if updates:
            _save_board(data, board_name)
        return json_result(
            success=False,
            error="Task is still running. Pass force=true to kill the current worker before retrying.",
            board=board_name,
            task_id=task_id,
            status=status,
            synced=updates,
        )
    retryable_statuses = {"error", "cancelled", "blocked"}
    if status not in retryable_statuses and status != "running":
        if updates:
            _save_board(data, board_name)
        return json_result(
            success=False,
            error=f"Task status must be one of {sorted(retryable_statuses)} or running with force=true; got {status}",
            board=board_name,
            task_id=task_id,
            status=status,
            synced=updates,
        )

    cached = _read_json_file(task.get("cache_path"))
    if task.get("pid"):
        try:
            _kill_pid(int(task["pid"]))
        except Exception:
            pass

    archived = _archive_current_attempt(task, board_name)
    if mode == "resume":
        task["resume_context"] = _build_resume_context(task, cached)
    else:
        task.pop("resume_context", None)

    for key in (
        "pid",
        "cache_path",
        "payload_path",
        "stdout_path",
        "stderr_path",
        "started_at",
        "completed_at",
        "final",
        "error",
        "session_path",
    ):
        task.pop(key, None)

    spawn_info = _spawn_worker(task, board_name, runtime)
    task.update(spawn_info)
    task["status"] = "running"
    task["updated_at"] = _now()
    _event(data, "task_retried", task_id=task_id, mode=mode, pid=spawn_info["pid"], archived_attempt=archived.get("attempt"))
    _save_board(data, board_name)
    return json_result(
        success=True,
        board=board_name,
        task_id=task_id,
        mode=mode,
        archived_attempt=archived,
        spawned=spawn_info,
        task=task,
    )


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
            f"Workers running in background 鈥?running={len(running)}, ready={len(remaining_ready)}. "
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
    title        = str(args.get("title") or "").strip()
    topic        = str(args.get("topic") or "").strip()
    board_name   = str(args.get("board") or _new_board_name("meeting", title or topic))
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
        "End with meeting_conclude. Do not create downstream implementation tasks; "
        "the main scheduling agent will review the conclusion and create any follow-up Kanban work."
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
        auto_compact=args.get("auto_compact"),
        extra_tools=["meeting"],   # always included 鈥?moderator needs meeting tools
    )
    _save_board(data, board_name)
    return json_result(
        success=True,
        board=board_name,
        task=task,
        hint=(
            "Meeting task created with meeting tools pre-enabled. Call kanban_dispatch to start. "
            "After the meeting board completes, review the conclusion and create downstream Kanban tasks "
            "instead of doing the deliverable work inline."
        ),
    )


registry.register("kanban_create_meeting_task", {
    "description": (
        "Create a kanban task that runs a meeting moderator agent. "
        "The moderator decides the discussion format dynamically (ask_one / chain / group_discuss). "
        "You only need to specify the topic and optionally suggest participants 鈥?"
        "the moderator handles everything else. Meeting tools are enabled automatically."
    ),
    "parameters": {
        "type": "object",
            "properties": {
            "board":   {"type": "string", "description": "Optional board name. If omitted, a new meeting-specific board is created automatically."},
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
            "auto_compact": {
                "type": "boolean",
                "default": True,
                "description": "Whether the moderator worker may auto-compact its context.",
            },
            "provider":       {"type": "string"},
            "model":          {"type": "string"},
        },
        "required": ["title", "topic"],
    },
}, _handle_create_meeting_task)


def _slug(text: str, max_len: int = 60) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")[:max_len].rstrip("-") or "topic"


RESEARCH_DEFAULT_PARTICIPANTS = [
    "Framer: Problem Framer / chair. Turns the vague topic into a structured research question - "
    "defines setting, benchmark, evaluation protocol, and assumptions. Output is a research-space "
    "definition, not an idea.",
    "Scout: Literature Scout. Uses browser/search tools to find the closest prior work, clusters it "
    "(not a flat list), and explicitly names saturated areas vs underexplored gaps. Must cite what it found.",
    "Generator: Idea Generator (divergent). Produces 5-8 concrete research directions. Each idea MUST "
    "be a fenced json block with keys: name, mechanism, intuition, extends, expected_gain, risk. "
    "Ideas without this structure will not be scored.",
    "Skeptic: Adversarial Reviewer. For each idea INDIVIDUALLY (never batched), finds prior-art overlap, "
    "triviality, and evaluation-feasibility problems, and tags it: already-known / unclear-novelty / "
    "hard-to-evaluate / promising / high-novelty. Job is to kill weak ideas, not to be agreeable.",
    "Realist: Systems Realist. For each surviving idea, judges compute cost, data requirements, and "
    "engineering feasibility for a small-lab/single-researcher budget. Kills ideas needing infeasible scale.",
    "Synthesizer: Final ranking. Scores surviving ideas on novelty/feasibility/evaluability/expected impact "
    "(high/medium/low each) and produces a justified top 1-3 ranking.",
]


def _research_meeting_prompt(
    topic: str,
    constraints: str,
    participants: list[str],
    report_path: str,
    *,
    selected_idea: str = "",
    deepen_from_report: str = "",
    iteration: int = 1,
) -> str:
    participant_lines = "\n".join(f"  - {p}" for p in participants)
    constraints_block = f"\nConstraints: {constraints}\n" if constraints else ""

    if selected_idea and deepen_from_report:
        # Deepening mode: narrow the whole meeting to ONE previously-selected direction instead
        # of generating fresh divergent ideas. This is the iteration loop step - research quality
        # comes from repeatedly narrowing on a human-chosen direction, not from one big brainstorm.
        return f"""Research DEEPENING meeting (iteration {iteration}).

Original topic: {topic}
Direction selected by the human to deepen: {selected_idea}
{constraints_block}
Prior report (read this FIRST): {deepen_from_report}

Suggested participants:
{participant_lines}

You are the meeting moderator. Load the meeting_moderator skill for tool mechanics (meeting_ask_one /
meeting_chain / meeting_group_discuss / meeting_conclude), but follow THIS phase protocol instead of
choosing your own format - it is mandatory, not optional:

0. read_file the prior report at {deepen_from_report} so every participant turn can reference it via
   meeting_add_notes. Do NOT re-run open brainstorming on the whole topic - the human already chose
   "{selected_idea}"; your job is to deepen it, not replace it.
1. Framing: meeting_ask_one to Framer to narrow the research-space definition specifically to
   "{selected_idea}" (concrete setting, benchmark, evaluation, assumptions for THIS mechanism only).
2. Scouting: meeting_ask_one to Scout for a DEEPER, more specific search validating or refuting the
   exact mechanism in "{selected_idea}" (not the broad topic). Add findings via meeting_add_notes.
3. Generation: meeting_ask_one or meeting_chain to Generator for 3-5 REFINEMENTS of the selected idea
   only (alternate formalizations, ablations, or stronger variants) - not fresh unrelated ideas. Same
   per-idea JSON format (mechanism, intuition, extends, expected_gain, risk).
4. Adversarial review (CRITICAL - do not skip or batch this): meeting_ask_one to Skeptic ONCE PER
   REFINEMENT, stress-testing harder than a first-pass review since this direction already survived one
   round. Then meeting_ask_one to Realist ONCE PER SURVIVING REFINEMENT. Drop anything that does not
   hold up.
5. Synthesis: meeting_ask_one to Synthesizer - the question now is "is this ready for experiments", not
   "which of many ideas wins". Ask for the single tightest formalized version plus a clear go/no-go
   verdict.
6. Before concluding, use write_file to save the report to exactly this path: {report_path}
   Include a "Lineage" section at the top: original topic, selected direction, and a pointer back to
   {deepen_from_report}.
7. Call meeting_conclude with the tightened direction and go/no-go verdict. This ends your loop - do
   not call respond_to_user.

Do not create downstream implementation tasks yourself; a follow-up worker will formalize the result
into a method design.

When calling meeting_create_participants, do NOT set a model or provider for any participant - leave
those fields unset so every participant uses the default model.
"""

    return f"""Research ideation meeting.

Research area / question: {topic}
{constraints_block}
Suggested participants:
{participant_lines}

You are the meeting moderator. Load the meeting_moderator skill for tool mechanics (meeting_ask_one /
meeting_chain / meeting_group_discuss / meeting_conclude), but follow THIS phase protocol instead of
choosing your own format - it is mandatory for research ideation, not optional:

1. Framing: meeting_ask_one to Framer for a structured research-space definition (setting, benchmark,
   evaluation, assumptions). Adopt the result via meeting_set_agenda.
2. Scouting: meeting_ask_one to Scout. Scout must use browser/search tools to find real prior work,
   cluster it, and name concrete gaps. Add the result via meeting_add_notes.
3. Generation: meeting_ask_one or meeting_chain to Generator for 5-8 ideas in the required per-idea
   JSON format.
4. Adversarial review (CRITICAL - do not skip or batch this): call meeting_ask_one to Skeptic ONCE PER
   IDEA, not all ideas at once. Then call meeting_ask_one to Realist ONCE PER SURVIVING IDEA. Drop any
   idea tagged already-known or infeasible - do not carry it into synthesis.
5. Synthesis: meeting_ask_one to Synthesizer with the surviving ideas plus their Skeptic/Realist
   verdicts. Ask for a scored, justified top 1-3 ranking.
6. Before concluding, use write_file to save the full report (research question, surviving ideas with
   verdicts, final ranking) to exactly this path: {report_path}
7. Call meeting_conclude with the ranked top 1-3 ideas and justification. This ends your loop -
   do not call respond_to_user.

Do not create downstream implementation tasks yourself; a follow-up review will judge whether this
result has converged. If the human later wants to go deeper on ONE of these ideas outside that
automatic loop, call kanban_create_research_pipeline again with selected_idea and deepen_from_report
set to this report path - do not just re-run a fresh open brainstorm on the same topic.

When calling meeting_create_participants, do NOT set a model or provider for any participant - leave
those fields unset so every participant uses the default model.
"""


def _review_prompt(
    topic: str,
    report_path: str,
    iteration: int,
    max_loop_iterations: int,
    constraints: str,
    board_name: str,
) -> str:
    constraints_block = f"\nConstraints: {constraints}\n" if constraints else ""
    next_iteration = iteration + 1
    can_iterate = next_iteration <= max_loop_iterations

    if can_iterate:
        not_converged_block = f"""If NOT converged (this is iteration {iteration}/{max_loop_iterations}, budget remains):
1. Identify the ONE most important unresolved issue or most promising remaining direction from the
   report - the single thing worth deepening next. Do not try to fix everything at once.
2. Call kanban_create_research_pipeline with:
   - board: "{board_name}"
   - topic: "{topic}"
   - selected_idea: <the specific direction/fix to deepen, written in your own words>
   - deepen_from_report: "{report_path}"
   - iteration: {next_iteration}
   - max_loop_iterations: {max_loop_iterations}
   - constraints: the same constraints as this run, if any
3. Finish with respond_to_user stating: verdict=NEEDS-ITERATION, the issue you are sending back for
   another round, and the new iteration number spawned. Do not call kanban_dispatch yourself - the
   new task is spawned automatically once you finish."""
    else:
        not_converged_block = f"""If NOT converged: this is the last allowed iteration ({iteration}/{max_loop_iterations}) - the loop
budget is exhausted. Do NOT call kanban_create_research_pipeline. Finish with respond_to_user stating:
verdict=BUDGET-EXHAUSTED, and clearly list every unresolved issue so a human can decide whether to
continue manually (by calling kanban_create_research_pipeline again with a higher max_loop_iterations)."""

    return f"""Research convergence review (iteration {iteration} of at most {max_loop_iterations}).

Research area / question: {topic}
{constraints_block}
Report to review: {report_path}

Steps:
1. read_file the report at {report_path}.
2. Judge whether this direction has CONVERGED to something ready for real experiments. It has
   converged only if ALL of the following hold:
   - The Synthesizer's verdict in the report is an explicit GO (not NO-GO, not conditional, and not
     merely "ranked #1" without a concrete plan)
   - Every parameter needed to start an experiment is concrete - no "TBD", "some X", or open ranges
     left for hyperparameters, datasets, loss functions, or evaluation protocol
   - Skeptic/Realist objections recorded in the report were either resolved or explicitly accepted
     as a named limitation, not left dangling
   - There is at least one concrete falsification test defined
3. If converged: finish with respond_to_user stating verdict=APPROVED, a one-paragraph justification,
   and the final report_path. This ends the pipeline - do not create further tasks.
4. {not_converged_block}
"""


def _handle_create_research_pipeline(args: dict, runtime: dict) -> str:
    topic = str(args.get("topic") or "").strip()
    if not topic:
        return json_result(success=False, error="topic is required")
    constraints = str(args.get("constraints") or "").strip()
    participants = args.get("participants") or RESEARCH_DEFAULT_PARTICIPANTS
    board_name = str(args.get("board") or _new_board_name("research", topic))
    selected_idea = str(args.get("selected_idea") or "").strip()
    deepen_from_report = str(args.get("deepen_from_report") or "").strip()
    iteration = int(args.get("iteration") or (2 if selected_idea and deepen_from_report else 1))
    max_loop_iterations = int(args.get("max_loop_iterations") or 5)

    if bool(selected_idea) != bool(deepen_from_report):
        return json_result(success=False, error="selected_idea and deepen_from_report must be provided together")

    slug = _slug(topic)
    report_path = f"reports/research/{slug}.md" if iteration <= 1 else f"reports/research/{slug}-iter{iteration}.md"

    data = _load_board(board_name)

    meeting_task = _create_task(
        data,
        title=f"Research {'deepening' if selected_idea else 'ideation'} meeting (iter {iteration}): {topic[:40]}",
        prompt=_research_meeting_prompt(
            topic, constraints, participants, report_path,
            selected_idea=selected_idea, deepen_from_report=deepen_from_report, iteration=iteration,
        ),
        skill="meeting_moderator",
        parents=[],
        status="ready",
        max_iterations=args.get("max_iterations") or 40,
        auto_compact=args.get("auto_compact"),
        extra_tools=["meeting"],
        metadata={
            "kind": "research_ideation_meeting",
            "topic": topic,
            "report_path": report_path,
            "iteration": iteration,
            "selected_idea": selected_idea or None,
            "deepen_from_report": deepen_from_report or None,
        },
    )

    review_task = _create_task(
        data,
        title=f"Convergence review (iter {iteration}): {topic[:40]}",
        prompt=_review_prompt(topic, report_path, iteration, max_loop_iterations, constraints, board_name),
        parents=[meeting_task["id"]],
        status="ready",
        max_iterations=args.get("review_max_iterations") or 16,
        auto_compact=args.get("auto_compact"),
        metadata={
            "kind": "research_convergence_review",
            "topic": topic,
            "report_path": report_path,
            "iteration": iteration,
            "max_loop_iterations": max_loop_iterations,
        },
    )

    _save_board(data, board_name)
    return json_result(
        success=True,
        board=board_name,
        report_path=report_path,
        iteration=iteration,
        max_loop_iterations=max_loop_iterations,
        tasks=[meeting_task, review_task],
        board_path=str(_board_path(board_name)),
        hint=(
            "Call kanban_dispatch to start the meeting worker. The review task is blocked until the "
            "meeting task is done; it will be spawned automatically once its parent completes. The "
            "review task itself decides whether to approve (verdict=APPROVED, loop stops) or spawn the "
            "next iteration (verdict=NEEDS-ITERATION, this tool is called again automatically) - no "
            "manual intervention needed unless it reports verdict=BUDGET-EXHAUSTED. Subscribe with "
            "kanban_notify_subscribe, then respond_to_user."
        ),
    )


registry.register("kanban_create_research_pipeline", {
    "description": (
        "Create a research-idea-ideation pipeline: a structured meeting (Framer / Scout / Generator / "
        "Skeptic / Realist / Synthesizer, with mandatory per-idea adversarial review) followed by a "
        "convergence review that judges whether the result is ready for real experiments. If not "
        "converged, the review task automatically spawns the next deepening iteration itself (calling "
        "this tool again) and the loop repeats until the review approves or max_loop_iterations is hit - "
        "no manual re-invocation needed. Use this instead of kanban_create_meeting_task whenever the "
        "goal is finding or vetting research directions rather than a general-purpose discussion."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "description": "Optional board name; auto-generated from topic if omitted."},
            "topic": {"type": "string", "description": "The research area or question to explore."},
            "constraints": {"type": "string", "description": "Optional constraints: compute budget, dataset, timeline, etc."},
            "selected_idea": {
                "type": "string",
                "description": (
                    "Set together with deepen_from_report to run a DEEPENING iteration instead of a fresh "
                    "brainstorm: the one direction (from a prior report) to go deeper on. Normally set "
                    "automatically by the convergence review task, not by a human."
                ),
            },
            "deepen_from_report": {
                "type": "string",
                "description": "Path to the prior report.md this iteration deepens (the report_path returned by a previous call). Required together with selected_idea.",
            },
            "iteration": {
                "type": "integer",
                "description": "Optional explicit iteration number for the report filename. Defaults to 1 for a fresh pipeline, or 2 when selected_idea/deepen_from_report are set.",
            },
            "max_loop_iterations": {
                "type": "integer",
                "default": 5,
                "description": (
                    "Hard cap on how many deepening iterations the convergence-review loop may spawn on "
                    "its own before it must stop and report BUDGET-EXHAUSTED instead of approving or "
                    "iterating further."
                ),
            },
            "participants": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional override of the default 6-role roster (Framer/Scout/Generator/Skeptic/"
                    "Realist/Synthesizer), e.g. ['Framer: ...', 'Scout: ...']. Keep the same six "
                    "functional roles unless you have a specific reason to change them."
                ),
            },
            "max_iterations": {"type": "integer", "default": 25},
            "review_max_iterations": {"type": "integer", "default": 16},
            "auto_compact": {"type": "boolean", "default": True},
        },
        "required": ["topic"],
    },
}, _handle_create_research_pipeline)


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
            "auto_compact": {
                "type": "boolean",
                "default": True,
                "description": "Whether the worker may auto-compact its context. Keep true by default; set false for long writer/generator tasks.",
            },
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
            "auto_compact": {
                "type": "boolean",
                "default": True,
                "description": "Default auto_compact setting for tasks that do not specify their own value.",
            },
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
                        "auto_compact": {
                            "type": "boolean",
                            "description": "Whether this worker may auto-compact its context. Set false for long writer/generator tasks.",
                        },
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

registry.register("kanban_list_boards", {
    "description": "List all Kanban boards so the agent can discover board names before inspecting tasks.",
    "parameters": {
        "type": "object",
        "properties": {
            "active_only": {"type": "boolean", "default": False, "description": "If true, return only boards with non-terminal tasks."},
        },
        "required": [],
    },
}, _handle_list_boards)

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

registry.register("kanban_retry_task", {
    "description": (
        "Retry or resume a failed, cancelled, blocked, or force-killed running Kanban worker task. "
        "retry starts a fresh worker from the original task prompt. resume starts a fresh worker with "
        "context from the previous cache/session so it can continue without redoing completed work."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "board": {"type": "string", "default": DEFAULT_BOARD},
            "task_id": {"type": "string"},
            "mode": {"type": "string", "enum": ["retry", "resume"], "default": "resume"},
            "force": {
                "type": "boolean",
                "default": False,
                "description": "If true and the task is still running, kill the current worker before starting a new one.",
            },
        },
        "required": ["task_id"],
    },
}, _handle_retry_task)

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
        "session_id":        runtime.get("session_id", ""),
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
        {
            "id": t["id"],
            "title": t.get("title"),
            "status": t.get("status"),
            "skill": t.get("skill"),
            "final": (t.get("final") or "")[:300],
        }
        for t in sorted(all_tasks, key=lambda t: t.get("created_at", ""))
    ]
    has_meeting_task = any(str(t.get("skill") or "") == "meeting_moderator" for t in all_tasks)

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

        # Write wake file so the web server can auto-resume the session
        session_id = sub.get("session_id", "")
        if session_id:
            wake = {
                "session_id":        session_id,
                "board":             board_name,
                "pending_file":      str(pending_path),
                "on_complete_prompt": sub.get("on_complete_prompt") or "",
                "has_meeting_task":  has_meeting_task,
                "fired_at":          _now(),
            }
            (NOTIFY_DIR / f"wake_{session_id}_{sub['sub_id']}.json").write_text(
                json.dumps(wake, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        sub_file.unlink(missing_ok=True)

        sys.stdout.write(
            f"\n[kanban] Board '{board_name}' complete 鈥?"
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
        unfinished = [t for t in tasks if t.get("status") in ("error", "blocked", "cancelled")]
        # Only apply the generic meeting follow-up guidance to meetings that actually
        # produced a conclusion - a meeting task that is itself unfinished has no result to
        # treat as planning input, and telling the agent otherwise would be misleading.
        has_meeting_task = any(
            str(t.get("skill") or "") == "meeting_moderator" and t.get("status") not in ("error", "blocked", "cancelled")
            for t in tasks
        )
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
        if unfinished:
            names = "; ".join(f"{t['title']} ({t['status']})" for t in unfinished)
            content += (
                f"\n\nACTION NEEDED: {len(unfinished)} task(s) did not complete successfully and will "
                f"NOT be retried automatically: {names}. This usually means a worker's own API calls "
                "kept failing (e.g. connection errors) until it gave up - the task result above is "
                "partial or missing, not a finished deliverable. Do not treat this board as done. "
                "Either replan (adjust scope/approach and create new tasks) or call kanban_retry_task "
                "(mode=resume) on the affected task_id if the same approach is still worth retrying."
            )
        if has_meeting_task:
            content += (
                "\n\nMeeting follow-up rule:\n"
                "- Treat the meeting result as planning input for the next phase.\n"
                "- Review the conclusion, then create downstream Kanban tasks or a Kanban pipeline for substantial deliverables.\n"
                "- Do not perform the downstream worker work inline in this resumed turn unless the user explicitly asked for direct execution.\n"
                "- After dispatching follow-up Kanban work, subscribe to completion notifications and respond_to_user."
            )
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

