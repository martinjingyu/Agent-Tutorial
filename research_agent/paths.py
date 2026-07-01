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


def workspace_root() -> Path:
    return Path(PROJECT_ROOT / "workspace").expanduser().resolve()
