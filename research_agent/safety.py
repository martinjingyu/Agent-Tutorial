from __future__ import annotations

import os
import re
from pathlib import Path

from .paths import session_roots, shared_roots, workspace_root


_DESTRUCTIVE_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bRemove-Item\b.*\s-Recurse\b",
    r"\bdel\s+/[sq]\b",
    r"\brmdir\s+/s\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+checkout\s+--\b",
    r"\bformat\b",
]


def resolve_workspace_path(path: str | None, *, default: Path | None = None) -> Path:
    root = workspace_root()
    base = default or root
    raw = Path(path).expanduser() if path else base
    if not raw.is_absolute():
        raw = root / raw
    resolved = raw.resolve()
    # workspace_root() itself, plus any explicitly opted-in shared_roots(), plus this
    # agent's own tool-result spill cache (session_roots()) -- never an arbitrary
    # absolute path, which is what let participants read each other's private
    # workspaces / stale files from old runs. Writes (write_file/append_file/
    # patch_file) always go through this, never resolve_readable_path below --
    # unrestricted reads are one thing, letting a participant overwrite another
    # participant's files or arbitrary paths on disk is a different, much worse
    # one, and terminal/run_background's own destructive-pattern check
    # (check_command) doesn't cover targeted single-file overwrites either.
    for allowed in (root, *shared_roots(), *session_roots()):
        if resolved == allowed or allowed in resolved.parents:
            return resolved
    raise ValueError(f"Path escapes workspace root {root}: {path}")


def resolve_readable_path(path: str | None, *, default: Path | None = None) -> Path:
    """Like resolve_workspace_path, but for read-only tools (read_file, list_files,
    search_files, read_pdf): no sandbox check. Relative paths still resolve against
    workspace_root() for convenience; absolute paths (e.g. C:\\pics, a task's external
    read-only data directory that isn't part of workspace_root/shared_roots/
    session_roots) are allowed through as-is, matching what `terminal` could already
    read anyway -- see check_command, which never restricted read access, only a
    short list of destructive command patterns. Enforcing the sandbox on read tools
    but not on terminal was strictly worse than either extreme: it didn't stop
    anything terminal could still do, it just made the properly-logged, structured
    tool call fail and pushed the agent toward an unstructured shell workaround
    instead, which is exactly what happened in practice (participants falling back
    to `type`/`copy` after read_file/list_files rejected a legitimate path)."""
    root = workspace_root()
    base = default or root
    raw = Path(path).expanduser() if path else base
    if not raw.is_absolute():
        raw = root / raw
    return raw.resolve()


def check_command(command: str) -> None:
    lowered = command.strip()
    for pattern in _DESTRUCTIVE_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            raise ValueError(f"Blocked risky command pattern: {pattern}")


def build_subprocess_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    if extra:
        env.update(extra)
    return env
