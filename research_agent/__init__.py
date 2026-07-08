"""General tool-use agent library — import this package to get the agent loop and shared tools."""

from .agent import GeneralAgent
from .kanban_watcher import KanbanWatcher
from .session import ChatSession
from .tools import load_builtin_tools, registry
from .tools.background import BackgroundJobWatcher
from .tools.meeting import register_meeting_tools, register_moderator_tools
from .tools.registry import ToolRegistry

__all__ = [
    "GeneralAgent",
    "ChatSession",
    "KanbanWatcher",
    "BackgroundJobWatcher",
    "load_builtin_tools",
    "registry",
    "ToolRegistry",
    "register_meeting_tools",
    "register_moderator_tools",
]
