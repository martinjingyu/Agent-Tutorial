from __future__ import annotations

import os
import re
import subprocess

from ..safety import build_subprocess_env, check_command, resolve_workspace_path
from .registry import json_result, registry

_MAX_OUTPUT_CHARS = 20_000


def _normalize_windows_cmd(cmd: str) -> str:
    cmd = re.sub(r'\bmkdir\s+-p\s+', 'mkdir ', cmd)
    cmd = re.sub(r'\brm\s+-rf?\s+', 'rmdir /s /q ', cmd)
    cmd = re.sub(r'\brm\s+-f\s+', 'del /f /q ', cmd)
    cmd = re.sub(r'^\s*pwd\s*$', 'cd', cmd)
    cmd = re.sub(r'^\s*ls\b', 'dir', cmd)
    m = re.match(r'^\s*head\s+-n\s+(\d+)\s+(.+)$', cmd)
    if m:
        cmd = f'powershell -Command "Get-Content {m.group(2)} -TotalCount {m.group(1)}"'
    cmd = re.sub(r'^\s*cat\s+', 'type ', cmd)
    return cmd


def _terminal(args: dict, runtime: dict) -> str:
    command = str(args.get("command") or "")
    if not command:
        return json_result(success=False, error="command is required")
    check_command(command)
    workdir = resolve_workspace_path(args.get("workdir") or ".")
    timeout = int(args.get("timeout") or 60)
    proc = subprocess.run(
        command,
        cwd=str(workdir),
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding='utf-8',
        errors='replace',
        env=build_subprocess_env(),
    )
    stdout = proc.stdout[-20000:]
    stderr = proc.stderr[-8000:]
    return json_result(
        success=proc.returncode == 0,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )


registry.register(
    "terminal",
    {
        "description": "Run a non-destructive shell command inside the Code workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "workdir": {"type": "string", "default": "."},
                "timeout": {"type": "integer", "default": 60},
            },
            "required": ["command"],
        },
    },
    _terminal,
)


def _run_cmd(args: dict, runtime: dict) -> str:
    command: str = args.get("command", "").strip()
    if not command:
        return json_result(success=False, error="command is required")

    if os.name == "nt":
        command = _normalize_windows_cmd(command)

    cwd: str | None = args.get("cwd") or runtime.get("candidate_folder") or None
    timeout: int = int(args.get("timeout") or 120)

    kwargs: dict = {}
    if os.name == "nt":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW

    try:
        encoding = "mbcs" if os.name == "nt" else "utf-8"
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors="replace",
            cwd=cwd,
            timeout=timeout,
            **kwargs,
        )
    except subprocess.TimeoutExpired:
        return json_result(success=False, error=f"Command timed out after {timeout}s")
    except Exception as exc:
        return json_result(success=False, error=str(exc))

    result: dict = {"success": proc.returncode == 0, "returncode": proc.returncode}
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if stdout:
        result["stdout"] = stdout[:_MAX_OUTPUT_CHARS]
        if len(stdout) > _MAX_OUTPUT_CHARS:
            result["stdout_truncated"] = True
    if stderr:
        result["stderr"] = stderr[:5000]
    return json_result(**result)


registry.register(
    "run_cmd",
    {
        "description": (
            "Run a shell command and return stdout/stderr. "
            "On Windows, common Unix commands (mkdir -p, rm -rf, ls, cat, head) are "
            "automatically translated to their cmd.exe equivalents. "
            "Working directory defaults to candidate_folder from runtime if not specified."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory (optional)"},
                "timeout": {"type": "integer", "default": 120, "description": "Timeout in seconds"},
            },
            "required": ["command"],
        },
    },
    _run_cmd,
)
