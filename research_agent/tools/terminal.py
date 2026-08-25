from __future__ import annotations

import re

from .registry import registry


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


def _terminal(args: dict, runtime: dict) -> str:
    # Note: run_with_settle applies _normalize_windows_cmd itself -- don't
    # duplicate that here.
    from .background import run_with_settle

    command = str(args.get("command") or "")
    timeout = float(args.get("timeout") or 60)
    workdir_arg = args.get("workdir") or args.get("cwd")
    return run_with_settle(command, workdir_arg, timeout)


registry.register(
    "terminal",
    {
        "description": (
            "Run a non-destructive shell command inside the Code workspace. "
            "This project runs on Windows with cmd.exe shell semantics; prefer Windows commands "
            "(dir, type, copy, move, mkdir, rmdir /s /q, del /f /q) or explicit powershell -Command. "
            "Do not use Unix-only flags such as mkdir -p, cp -r, rm -rf, grep, sed, or head unless you "
            "know they are available. Common Unix commands are normalized on Windows when possible. "
            "If the command doesn't finish within `timeout` seconds (default 60), it is NOT killed "
            "and this is NOT reported as a failure -- it's handed off to a background watcher (the "
            "same mechanism as run_background) and you'll be notified automatically with the result "
            "on your next turn, no polling needed."
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
