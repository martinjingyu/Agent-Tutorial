"""General tool-use agent library — import this package to get the agent loop and shared tools."""

from .agent import GeneralAgent
from .kanban_watcher import KanbanWatcher
from .session import ChatSession
from .tools import load_builtin_tools, registry
from .tools.kanban import register_kanban_wait_complete
from .tools.meeting import register_meeting_tools
from .tools.registry import ToolRegistry

__all__ = [
    "GeneralAgent",
    "ChatSession",
    "KanbanWatcher",
    "load_builtin_tools",
    "registry",
    "ToolRegistry",
    "register_kanban_wait_complete",
    "register_meeting_tools",
]
