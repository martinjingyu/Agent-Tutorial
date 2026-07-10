"""Shared §-delimited markdown entry list format, used by both the global memory
tool (tools/memory.py) and per-role memory (roles.py / tools/roles.py)."""
from __future__ import annotations

from pathlib import Path

DELIMITER = "\n§\n"


def read_entries(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    return [entry.strip() for entry in text.split(DELIMITER) if entry.strip()]


def write_entries(path: Path, entries: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DELIMITER.join(entries).strip() + ("\n" if entries else ""), encoding="utf-8")
