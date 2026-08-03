from __future__ import annotations

import os
import threading
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORIES_DIR = PROJECT_ROOT / "memories"
SKILLS_DIR = PROJECT_ROOT / "skills"
SESSIONS_DIR = PROJECT_ROOT / "sessions"


def ensure_project_dirs() -> None:
    for path in (MEMORIES_DIR, SKILLS_DIR, SESSIONS_DIR):
        path.mkdir(parents=True, exist_ok=True)


# Thread-local, not a plain module global: embedding projects that run multiple
# GeneralAgent instances concurrently in different threads (e.g. Agent-Meeting's
# parallel participants) each need their own workspace_root override without racing
# each other -- a plain global would let one thread's set_workspace_root() clobber
# another's mid-run, since file/terminal tools re-read workspace_root() on every call,
# not just once at construction time. Each thread gets its own independent override;
# a thread that never calls set_workspace_root() falls through to the env var / default
# below exactly as before (single-threaded callers see no behavior change).
_workspace_local = threading.local()


def set_workspace_root(path: str | Path) -> None:
    """Programmatic override for workspace_root(), for callers embedding this
    library that need file/terminal tools sandboxed to a different directory.
    Scoped to the calling thread only."""
    _workspace_local.override = Path(path).expanduser().resolve()


def workspace_root() -> Path:
    override = getattr(_workspace_local, "override", None)
    if override is not None:
        return override
    env_override = os.getenv("AGENT_WORKSPACE_ROOT")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return Path(PROJECT_ROOT / "workspace").expanduser().resolve()


# Thread-local, same reasoning as _workspace_local above: extra directories a file
# tool call may access besides workspace_root(), for embedding projects (e.g.
# Agent-Meeting) that want a small, explicit, opt-in area participants can use to
# intentionally share files with each other -- without falling back to letting a
# model read *any* path it can guess (that was the whole problem: participants
# reading each other's private workspaces or stale files from old runs).
_shared_roots_local = threading.local()


def set_shared_roots(paths: list[str | Path] | None) -> None:
    """Programmatic override for shared_roots(). Pass None (or an empty list) to
    clear it -- always call this explicitly on every GeneralAgent construction
    (not only when sharing is wanted), since ThreadPoolExecutor reuses threads and
    a stale override from a previous turn/meeting would otherwise leak forward."""
    _shared_roots_local.override = [Path(p).expanduser().resolve() for p in paths] if paths else []


def shared_roots() -> list[Path]:
    return getattr(_shared_roots_local, "override", None) or []


# Thread-local, same reasoning as _shared_roots_local: the current agent's own tool-result
# spill cache (agent.py's self._spill_dir, under SESSIONS_DIR/.tool_cache/<session_id>) lives
# outside workspace_root/shared_roots since SESSIONS_DIR is this package's own directory, not
# the embedding project's. It's the agent's own prior tool output, not another participant's
# data, so it's safe to always allow -- unlike shared_roots this isn't participant-facing/opt-in,
# it's set automatically per GeneralAgent construction (see agent.py.__init__).
_session_roots_local = threading.local()


def set_session_roots(paths: list[str | Path] | None) -> None:
    """Programmatic override for session_roots(). Always call this on every GeneralAgent
    construction (not only when there's a spill dir), since ThreadPoolExecutor reuses threads
    and a stale override from a previous turn/meeting would otherwise leak forward."""
    _session_roots_local.override = [Path(p).expanduser().resolve() for p in paths] if paths else []


def session_roots() -> list[Path]:
    return getattr(_session_roots_local, "override", None) or []


_roles_root_override: Path | None = None


def set_roles_root(path: str | Path) -> None:
    """Programmatic override for roles_root(), for embedding projects (e.g.
    Agent-Meeting) that keep their own private role library instead of sharing
    this package's own roles/ directory."""
    global _roles_root_override
    _roles_root_override = Path(path).expanduser().resolve()


def roles_root() -> Path:
    if _roles_root_override is not None:
        return _roles_root_override
    env_override = os.getenv("AGENT_ROLES_ROOT")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return Path(PROJECT_ROOT / "roles").expanduser().resolve()
