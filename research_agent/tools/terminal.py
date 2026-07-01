from __future__ import annotations

import os
import re
import subprocess

from ..safety import build_subprocess_env, check_command, resolve_workspace_path
from .registry import json_result, registry

def _normalize_windows_cmd(cmd: str) -> str:
    cmd = re.sub(r'\bmkdir\s+-p\s+', 'mkdir ', cmd)
    cmd = re.sub(r'\bcp\s+-r\s+', 'xcopy /e /i /y ', cmd)
    cmd = re.sub(r'\bcp\s+', 'copy ', cmd)
    cmd = re.sub(r'\bmv\s+', 'move ', cmd)
    cmd = re.sub(r'\brm\s+-rf?\s+', 'rmdir /s /q ', cmd)
    cmd = re.sub(r'\brm\s+-f\s+', 'del /f /q ', cmd)
    cmd = re.sub(r'^\s*pwd\s*$', 'cd', cmd)
    cmd = re.sub(r'^\s*ls\b', 'dir', cmd)
    m = re.match(r'^\s*head\s+-n\s+(\d+)\s+(.+)$', cmd)
    if m:
        cmd = f'powershell -Command "Get-Content {m.group(2)} -TotalCount {m.group(1)}"'
    m = re.match(r'^\s*tail\s+-n\s+(\d+)\s+(.+)$', cmd)
    if m:
        cmd = f'powershell -Command "Get-Content {m.group(2)} -Tail {m.group(1)}"'
    m = re.match(r'^\s*grep\s+(.+?)\s+(.+)$', cmd)
    if m:
        cmd = f'powershell -Command "Select-String -Pattern {m.group(1)} -Path {m.group(2)}"'
    cmd = re.sub(r'^\s*cat\s+', 'type ', cmd)
    return cmd


def _execute_command(args: dict, runtime: dict, *, workdir_key: str = "workdir", default_timeout: int = 60) -> str:
    command = str(args.get("command") or "")
    if not command:
        return json_result(success=False, error="command is required")
    check_command(command)
    if os.name == "nt":
        command = _normalize_windows_cmd(command)
    try:
        raw_workdir = args.get(workdir_key) or args.get("workdir") or args.get("cwd") or "."
        workdir = resolve_workspace_path(raw_workdir)
    except Exception as exc:
        return json_result(success=False, error=f"Invalid workdir: {exc}")
    timeout = int(args.get("timeout") or default_timeout)
    try:
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
    except subprocess.TimeoutExpired:
        return json_result(success=False, error=f"Command timed out after {timeout}s")
    except Exception as exc:
        return json_result(success=False, error=f"{type(exc).__name__}: {exc}")
    stdout = proc.stdout[-20000:]
    stderr = proc.stderr[-8000:]
    return json_result(
        success=proc.returncode == 0,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _terminal(args: dict, runtime: dict) -> str:
    return _execute_command(args, runtime, workdir_key="workdir", default_timeout=60)


registry.register(
    "terminal",
    {
        "description": (
            "Run a non-destructive shell command inside the Code workspace. "
            "This project runs on Windows with cmd.exe shell semantics; prefer Windows commands "
            "(dir, type, copy, move, mkdir, rmdir /s /q, del /f /q) or explicit powershell -Command. "
            "Do not use Unix-only flags such as mkdir -p, cp -r, rm -rf, grep, sed, or head unless you "
            "know they are available. Common Unix commands are normalized on Windows when possible."
        ),
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
