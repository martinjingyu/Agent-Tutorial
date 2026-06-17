from __future__ import annotations

from .registry import registry


def load_builtin_tools() -> None:
    from . import browser, compact, files, kanban, memory, respond, restart, skills, subprocess_tools, terminal  # noqa: F401


__all__ = ["registry", "load_builtin_tools"]
