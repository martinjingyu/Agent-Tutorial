from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime

from ..paths import SESSIONS_DIR
from ..safety import build_subprocess_env, check_command, resolve_workspace_path
from .registry import json_result, registry

NOTIFY_DIR = SESSIONS_DIR / ".background_notify"

_LOCK = threading.Lock()
_ACTIVE_JOBS: dict[str, subprocess.Popen] = {}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _tail(path: str, max_chars: int) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[-max_chars:]
    except OSError:
        return ""


def has_active_jobs() -> bool:
    """Whether any run_background job is still being watched. Used by callers
    (e.g. epistemic.interact_with_environment) to tell 'agent is genuinely
    done' apart from 'agent deferred to wait for a background job'."""
    with _LOCK:
        return bool(_ACTIVE_JOBS)


def has_pending_notifications() -> bool:
    return NOTIFY_DIR.exists() and any(NOTIFY_DIR.glob("pending_*.json"))


def _watch_and_fire(job_id: str, proc: subprocess.Popen, log_path: str, started: float) -> None:
    returncode = proc.wait()
    pending = {
        "event": "background_job_complete",
        "job_id": job_id,
        "returncode": returncode,
        "elapsed_sec": round(time.time() - started, 1),
        "log_tail": _tail(log_path, 8000),
        "fired_at": _now(),
    }
    NOTIFY_DIR.mkdir(parents=True, exist_ok=True)
    (NOTIFY_DIR / f"pending_{job_id}.json").write_text(
        json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with _LOCK:
        _ACTIVE_JOBS.pop(job_id, None)


def _run_background(args: dict, runtime: dict) -> str:
    command = str(args.get("command") or "")
    if not command:
        return json_result(success=False, error="command is required")
    check_command(command)
    if os.name == "nt":
        from .terminal import _normalize_windows_cmd

        command = _normalize_windows_cmd(command)
    try:
        workdir = resolve_workspace_path(args.get("workdir") or ".")
    except Exception as exc:
        return json_result(success=False, error=f"Invalid workdir: {exc}")

    settle = min(float(args.get("timeout") or 10), 60.0)
    job_id = uuid.uuid4().hex[:8]
    log_path = workdir / f".background_{job_id}.log"
    popen_kwargs: dict = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    log_file = open(log_path, "w", encoding="utf-8", errors="replace")
    started = time.time()
    try:
        proc = subprocess.Popen(
            command,
            cwd=str(workdir),
            shell=True,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=build_subprocess_env(),
            **popen_kwargs,
        )
    except Exception as exc:
        log_file.close()
        return json_result(success=False, error=f"{type(exc).__name__}: {exc}")

    # Fast path: short commands just finish within the settle window, no need
    # for the background/notify machinery at all.
    try:
        returncode = proc.wait(timeout=settle)
        log_file.close()
        return json_result(
            success=True,
            status="completed",
            returncode=returncode,
            elapsed_sec=round(time.time() - started, 1),
            log_tail=_tail(str(log_path), 8000),
        )
    except subprocess.TimeoutExpired:
        pass

    with _LOCK:
        _ACTIVE_JOBS[job_id] = proc
    log_file.close()
    threading.Thread(
        target=_watch_and_fire,
        args=(job_id, proc, str(log_path), started),
        daemon=True,
        name=f"background-watch-{job_id}",
    ).start()
    return json_result(
        success=True,
        status="running_in_background",
        job_id=job_id,
        pid=proc.pid,
        log_path=str(log_path),
        hint=(
            "Still running after the settle window, so it now continues under its own "
            "watcher thread -- it is never killed by anything, including this tool's "
            "timeout. Call respond_to_user now with a short note (not the final JSON) "
            "saying you're waiting on this job; you will be automatically notified with "
            "the full result on your next turn, with no need to poll or check on it."
        ),
    )


def _check_background(args: dict, runtime: dict) -> str:
    """Non-blocking peek by job_id. Normally unnecessary -- the completion
    notification arrives automatically as the next turn's context -- but
    useful if the agent wants to check without waiting for that turn."""
    job_id = str(args.get("job_id") or "")
    pending_path = NOTIFY_DIR / f"pending_{job_id}.json"
    if pending_path.is_file():
        try:
            data = json.loads(pending_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        return json_result(success=True, status="completed", **{k: v for k, v in data.items() if k != "event"})
    with _LOCK:
        still_active = job_id in _ACTIVE_JOBS
    if still_active:
        return json_result(success=True, status="running")
    return json_result(success=True, status="unknown", hint="No such active job and no completion notification found.")


def consume_pending_background_notifications() -> list[dict]:
    """Read all pending background-job completion files and return them as
    injected messages, mirroring kanban's consume_pending_notifications().
    Called by GeneralAgent.run() at the start of every turn. One-shot."""
    if not NOTIFY_DIR.exists():
        return []
    messages: list[dict] = []
    for pending_file in sorted(NOTIFY_DIR.glob("pending_*.json")):
        try:
            event = json.loads(pending_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        content = (
            f"[background job notification] job {event.get('job_id')} finished "
            f"(returncode={event.get('returncode')}, elapsed={event.get('elapsed_sec')}s)\n\n"
            f"Output:\n{event.get('log_tail', '')}"
        )
        messages.append({"role": "user", "content": content})
        pending_file.unlink(missing_ok=True)
    return messages


registry.register(
    "run_background",
    {
        "description": (
            "Run a shell command. If it finishes within the settle window (default 10s, max "
            "60s), its result is returned directly -- same as a normal blocking command. If "
            "it's still running after that, it keeps going under its own watcher thread -- "
            "never killed, never timed out -- and you will be automatically notified (as a new "
            "message, at the start of your next turn) with the full result. In that case, call "
            "respond_to_user right away so this turn ends cheaply instead of polling for status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "workdir": {"type": "string", "default": "."},
                "timeout": {
                    "type": "number",
                    "default": 10,
                    "description": "Settle window in seconds before switching to background+notify mode (max 60).",
                },
            },
            "required": ["command"],
        },
    },
    _run_background,
)
registry.register(
    "check_background",
    {
        "description": (
            "Non-blocking peek at a run_background job by job_id. You normally don't need "
            "this -- the completion notification arrives automatically on your next turn -- "
            "but it's available if you want to check without waiting."
        ),
        "parameters": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    _check_background,
)
