from __future__ import annotations

import os
import platform
from datetime import datetime
from pathlib import Path

from ..paths import SOURCE_DIR, SKILLS_DIR, workspace_root
from ..tools.memory import memory_snapshot
from .base import BASE_SYSTEM_PROMPT
from .compact import COMPACT_MODE_PROMPT
from .roles import ROLE_PROFILES

_STRUCTURE_SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".agentbrowser",
    "node_modules",
    ".venv",
    "venv",
    "memories",
    "reports",
    "sessions",
    "workspace",
    "candidates",
    "research_agent.egg-info",
}


def _directory_tree(root: Path, *, skip_dirs: set[str] | None = None) -> str:
    root = root.resolve()
    if not root.exists():
        return f"{root.name}/ (missing)"
    skip = skip_dirs or set()
    lines = [f"{root.name}/"]

    def visit(path: Path, depth: int) -> None:
        try:
            children = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        except OSError:
            return
        visible = [child for child in children if not (child.is_dir() and child.name in skip)]
        for child in visible:
            indent = "  " * depth
            suffix = "/" if child.is_dir() else ""
            lines.append(f"{indent}{child.name}{suffix}")
            if child.is_dir():
                visit(child, depth + 1)

    visit(root, 1)
    return "\n".join(lines)


def build_system_prompt(skills_index: str = "", *, agent_role: str = "main") -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    workspace = workspace_root()
    role_profile = ROLE_PROFILES.get(agent_role, ROLE_PROFILES["main"])
    include_code_structure = agent_role == "self_review"
    shell_context = (
        f"Shell 上下文：\n"
        f"- 操作系统：{platform.system()} {platform.release()}\n"
        f"- os.name：{os.name}\n"
        "- terminal 以 shell=True 方式执行命令。\n"
        "- 在 Windows 上，请使用 cmd.exe 命令或显式的 PowerShell 命令。优先使用 dir/type/copy/move/mkdir/rmdir/del，或 powershell -Command。\n"
        "- 避免使用仅 Unix 才有的命令和参数，例如 mkdir -p、cp -r、rm -rf、grep、sed、head、tail、chmod。"
    )
    parts = [
        f"当前日期：{today}",
        (
            "路径上下文：\n"
            f"- Agent 源码根目录：{SOURCE_DIR}\n"
            f"- 文件工具的 workspace 根目录：{workspace}\n"
            "- 传给文件工具的相对路径，会基于 workspace 根目录解析。"
        ),
        shell_context,
        role_profile.strip(),
        BASE_SYSTEM_PROMPT.strip(),
        COMPACT_MODE_PROMPT.strip(),
    ]
    if include_code_structure:
        project_structure = _directory_tree(SOURCE_DIR, skip_dirs=_STRUCTURE_SKIP_DIRS | {"skills"})
        skills_structure = _directory_tree(SKILLS_DIR, skip_dirs=_STRUCTURE_SKIP_DIRS)
        parts.insert(-1, "Agent 项目代码结构：\n" + project_structure)
        parts.insert(-1, "Skills 目录结构：\n" + skills_structure)
    # Sub-agents are narrow, single-task workers with no ownership of the user
    # relationship -- they don't need (and shouldn't see) the accumulated
    # cross-session memory that main/self_review use to stay consistent.
    if agent_role in ("main", "self_review"):
        mem = memory_snapshot()
        if mem:
            parts.append("持久化 memory 快照：\n" + mem)
    if skills_index:
        parts.append("可用 skill 索引：\n" + skills_index)
    return "\n\n".join(parts)
