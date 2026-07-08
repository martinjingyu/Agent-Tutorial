from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime
from typing import Callable

from ..paths import SESSIONS_DIR
from ..safety import build_subprocess_env, check_command, resolve_workspace_path
from .registry import json_result, registry

NOTIFY_DIR = SESSIONS_DIR / ".background_notify"

_LOCK = threading.Lock()
_ACTIVE_JOBS: dict[str, dict] = {}  # job_id -> {"proc", "log_path", "started"}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _tail(path: str, max_chars: int) -> tuple[str, bool]:
    """Returns (tail_text, was_truncated)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return "", False
    if len(text) > max_chars:
        return text[-max_chars:], True
    return text, False


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
    log_tail, truncated = _tail(log_path, 8000)
    pending = {
        "event": "background_job_complete",
        "job_id": job_id,
        "returncode": returncode,
        "elapsed_sec": round(time.time() - started, 1),
        "log_path": log_path,
        "log_tail": log_tail,
        "log_truncated": truncated,
        "fired_at": _now(),
    }
    NOTIFY_DIR.mkdir(parents=True, exist_ok=True)
    (NOTIFY_DIR / f"pending_{job_id}.json").write_text(
        json.dumps(pending, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with _LOCK:
        _ACTIVE_JOBS.pop(job_id, None)


def run_with_settle(command: str, workdir_arg: str | None, settle: float) -> str:
    """Shared core for run_background and terminal: run `command`, blocking for
    up to `settle` seconds. If it finishes in time, `success` reflects the
    command's own returncode (0 -> true), same as a normal terminal call. If
    it doesn't finish in time, the process is NEVER killed -- it's handed off
    to a watcher thread and tracked the same way regardless of which tool
    started it, so a plain `terminal` call that runs long gets exactly the
    same safe treatment as `run_background`: success=true (the tool call
    itself didn't fail, the command just isn't done), status=
    'running_in_background', and an automatic notification later. Timing out
    is not a failure -- the command started fine and may well still succeed;
    we just don't know yet, so we don't report false."""
    if not command:
        return json_result(success=False, error="command is required")
    check_command(command)
    if os.name == "nt":
        from .terminal import _normalize_windows_cmd

        command = _normalize_windows_cmd(command)
        # Note: `chcp 65001` does NOT help here -- it only affects a live console's
        # display codepage, and stdout below is redirected straight to a file, never
        # attached to a real console. cmd.exe's own builtins (dir, echo, etc.) still
        # emit the system ANSI/OEM codepage for non-ASCII text when redirected like
        # this, regardless of chcp. PYTHONIOENCODING below fixes this for Python
        # children specifically (the primary way this framework expects real work to
        # happen); non-ASCII output from cmd.exe builtins themselves may still be
        # garbled when read back as UTF-8 -- prefer doing substantive work (and its
        # output) via a Python script rather than relying on shell builtins for it.
    try:
        workdir = resolve_workspace_path(workdir_arg or ".")
    except Exception as exc:
        return json_result(success=False, error=f"Invalid workdir: {exc}")

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
            # PYTHONIOENCODING/PYTHONUTF8 force any Python child to encode its own
            # stdout as UTF-8 -- when stdout is redirected to a file rather than a
            # live console, Python decides its own text encoding independent of
            # chcp/the console codepage, so chcp above doesn't reach it.
            # PYTHONUNBUFFERED: without a real terminal, Python block-buffers stdout
            # (only flushes every few KB), so a slow-but-working script can leave the
            # log file looking empty for a long time -- indistinguishable from hung.
            # This makes every print() land on disk immediately.
            env=build_subprocess_env(
                {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
            ),
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
        log_tail, truncated = _tail(str(log_path), 8000)
        return json_result(
            success=returncode == 0,
            status="completed",
            returncode=returncode,
            elapsed_sec=round(time.time() - started, 1),
            log_path=str(log_path),
            log_tail=log_tail,
            log_truncated=truncated,
        )
    except subprocess.TimeoutExpired:
        pass

    with _LOCK:
        _ACTIVE_JOBS[job_id] = {"proc": proc, "log_path": str(log_path), "started": started}
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
            "saying you're waiting on this job; you will be automatically notified on your "
            "next turn with its returncode and the tail of its output (last 8000 chars). "
            "The notification also repeats this log_path, so if the output was longer than "
            "that you can read_file it directly for the full, untruncated log -- no need to "
            "poll or check on it in the meantime."
        ),
    )


def _run_background(args: dict, runtime: dict) -> str:
    settle = min(float(args.get("timeout") or 10), 60.0)
    return run_with_settle(str(args.get("command") or ""), args.get("workdir"), settle)


def _pid_alive(pid: int) -> bool:
    """Cross-process liveness check by PID. Needed because _ACTIVE_JOBS is only
    ever known to the process that called run_background/terminal -- a
    completely different process (a fresh script, a different agent run) has
    no way to find a job there even though the real OS process and its log
    file are just as inspectable from anywhere."""
    if os.name == "nt":
        # os.kill(pid, 0) is NOT a safe no-op probe on Windows -- for any signal
        # value other than CTRL_C_EVENT/CTRL_BREAK_EVENT it calls TerminateProcess
        # with that value as the exit code, i.e. os.kill(pid, 0) would actually
        # kill the process. Use tasklist instead, which only ever reads state.
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=5,
            )
            return str(pid) in out.stdout
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _check_background(args: dict, runtime: dict) -> str:
    """Peek at a run_background job's status. Normally unnecessary -- the
    completion notification arrives automatically as the next turn's context
    in the process that started it -- but useful to check without waiting,
    and it's the only way to check at all from a *different* process than the
    one that called run_background (_ACTIVE_JOBS is in-memory and process-
    local). Pass pid and/or log_path (both were in the original run_background
    response) to make that cross-process case work; without them, a job
    unknown to this process's memory can only be reported as such."""
    job_id = str(args.get("job_id") or "")
    pid = args.get("pid")
    log_path_arg = args.get("log_path")

    pending_path = NOTIFY_DIR / f"pending_{job_id}.json"
    if pending_path.is_file():
        try:
            data = json.loads(pending_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        return json_result(success=True, status="completed", **{k: v for k, v in data.items() if k != "event"})

    with _LOCK:
        job = _ACTIVE_JOBS.get(job_id)
    if job is not None:
        log_tail, truncated = _tail(job["log_path"], 8000)
        return json_result(
            success=True,
            status="running",
            log_path=job["log_path"],
            elapsed_sec=round(time.time() - job["started"], 1),
            log_tail=log_tail,
            log_truncated=truncated,
        )

    # Not tracked by this process. If the caller gave us pid/log_path (from the
    # original run_background response), reconstruct a best-effort status
    # directly from the OS and the log file instead of just giving up.
    if log_path_arg:
        log_tail, truncated = _tail(str(log_path_arg), 8000)
        alive = _pid_alive(int(pid)) if pid else None
        if alive is True:
            status = "running"
        elif alive is False:
            status = "not_running"
        else:
            status = "unknown_liveness"
        return json_result(
            success=True,
            status=status,
            log_path=str(log_path_arg),
            log_tail=log_tail,
            log_truncated=truncated,
            note=(
                "Reconstructed from the OS process and log file directly -- this job "
                "wasn't started by this process, so it has no bookkeeping for it. "
                "'not_running' means the process is gone, which usually means it "
                "finished, but if you're seeing this from the process that actually "
                "started the job, a missing completion notification would be a real bug."
            ),
        )

    return json_result(
        success=True,
        status="unknown",
        hint=(
            "No such active job and no completion notification found in this process. "
            "If this job was started by a different process, pass pid and log_path "
            "(both were in the original run_background response) to check it directly."
        ),
    )


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
        truncation_note = (
            f" (last 8000 chars only -- read_file {event.get('log_path')} for the full, "
            "untruncated log)"
            if event.get("log_truncated")
            else ""
        )
        content = (
            f"[background job notification] job {event.get('job_id')} finished "
            f"(returncode={event.get('returncode')}, elapsed={event.get('elapsed_sec')}s)\n"
            f"Full log at: {event.get('log_path')}\n\n"
            f"Output{truncation_note}:\n{event.get('log_tail', '')}"
        )
        messages.append({"role": "user", "content": content})
        pending_file.unlink(missing_ok=True)
    return messages


class BackgroundJobWatcher:
    """Background thread that polls for run_background completion notifications.

    Mirrors research_agent.kanban_watcher.KanbanWatcher, but for run_background
    jobs instead of kanban pipelines. When a job's notification appears, calls
    on_event with the injected messages -- the caller decides what to do,
    typically re-invoking GeneralAgent.run() with them as the next user turn.
    This is what actually makes notification delivery independent of any
    particular driver loop: as long as this thread is alive, a completed job's
    notification will be picked up and handed to on_event on its own, without
    requiring an external loop to keep polling has_active_jobs()/
    has_pending_notifications() itself.

    Usage::

        watcher = BackgroundJobWatcher(on_event=lambda msgs: ...).start()
        ...
        watcher.stop()
    """

    def __init__(
        self,
        on_event: Callable[[list[dict]], None],
        poll_interval: float = 0.5,
    ) -> None:
        self._on_event = on_event
        self._poll_interval = poll_interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> "BackgroundJobWatcher":
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="background-job-watcher"
        )
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        while not self._stop.wait(self._poll_interval):
            try:
                msgs = consume_pending_background_notifications()
                if msgs:
                    self._on_event(msgs)
            except Exception:
                pass


registry.register(
    "run_background",
    {
        "description": (
            "Run a shell command. If it finishes within the settle window (default 10s, max "
            "60s), its result is returned directly (with log_path, and log_tail truncated to "
            "the last 8000 chars if the output was longer) -- same as a normal blocking command. "
            "If it's still running after that, it keeps going under its own watcher thread -- "
            "never killed, never timed out -- and you will be automatically notified (as a new "
            "message, at the start of your next turn) with its returncode and log tail. The "
            "notification always repeats log_path, so read_file it directly if you need the full "
            "output and the tail looks truncated. In that case, call respond_to_user right away "
            "so this turn ends cheaply instead of polling for status."
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
            "but it's available if you want to check without waiting. Also pass pid and "
            "log_path (both were in the original run_background response) if you're checking "
            "from a different process than the one that started the job -- job tracking is "
            "in-memory and process-local, so without them a job unknown to this process can "
            "only be reported as 'unknown' even if it's genuinely still running."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "pid": {"type": "integer", "description": "From the original run_background response; enables a real liveness check when querying cross-process."},
                "log_path": {"type": "string", "description": "From the original run_background response; enables reading the log directly when querying cross-process."},
            },
            "required": ["job_id"],
        },
    },
    _check_background,
)
