from __future__ import annotations

from .registry import registry


_builtin_loaded = False


def load_builtin_tools() -> None:
    global _builtin_loaded
    if _builtin_loaded:
        return
    from . import browser, compact, files, kanban, memory, respond, restart, skills, subprocess_tools, terminal  # noqa: F401
    _builtin_loaded = True


__all__ = ["registry", "load_builtin_tools"]
