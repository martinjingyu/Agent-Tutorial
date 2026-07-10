from __future__ import annotations

import os
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORIES_DIR = PROJECT_ROOT / "memories"
SKILLS_DIR = PROJECT_ROOT / "skills"
SESSIONS_DIR = PROJECT_ROOT / "sessions"


def ensure_project_dirs() -> None:
    for path in (MEMORIES_DIR, SKILLS_DIR, SESSIONS_DIR):
        path.mkdir(parents=True, exist_ok=True)


_workspace_root_override: Path | None = None


def set_workspace_root(path: str | Path) -> None:
    """Programmatic override for workspace_root(), for callers embedding this
    library that need file/terminal tools sandboxed to a different directory."""
    global _workspace_root_override
    _workspace_root_override = Path(path).expanduser().resolve()


def workspace_root() -> Path:
    if _workspace_root_override is not None:
        return _workspace_root_override
    env_override = os.getenv("AGENT_WORKSPACE_ROOT")
    if env_override:
        return Path(env_override).expanduser().resolve()
    return Path(PROJECT_ROOT / "workspace").expanduser().resolve()


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
