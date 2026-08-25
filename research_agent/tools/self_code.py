from __future__ import annotations

import fnmatch
from pathlib import Path

from ..paths import PROJECT_ROOT
from .registry import json_result, registry


SELF_CODE_ROOT = (PROJECT_ROOT / "research_agent").resolve()
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".venv", "venv"}
_MAX_SNIPPET_CHARS = 500


def _safe_self_code_path(raw_path: str | None) -> Path:
    if not raw_path:
        raise ValueError("path is required")
    raw = Path(raw_path).expanduser()
    if not raw.is_absolute():
        raw = SELF_CODE_ROOT / raw
    resolved = raw.resolve()
    if resolved != SELF_CODE_ROOT and SELF_CODE_ROOT not in resolved.parents:
        raise ValueError(f"Path escapes self code root {SELF_CODE_ROOT}: {raw_path}")
    return resolved


def _iter_files(root: Path, file_glob: str | None = None):
    candidates = [root] if root.is_file() else root.rglob("*")
    for path in candidates:
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if file_glob and not fnmatch.fnmatch(path.name, file_glob) and not fnmatch.fnmatch(str(path), file_glob):
            continue
        yield path


def _self_code_search(args: dict, runtime: dict) -> str:
    pattern = str(args.get("pattern") or "")
    if not pattern:
        return json_result(success=False, error="pattern is required")
    root = _safe_self_code_path(args.get("path") or ".")
    file_glob = args.get("file_glob")
    file_glob = str(file_glob) if file_glob else None
    limit = max(1, min(int(args.get("limit") or 50), 200))
    matches: list[dict[str, object]] = []
    total_count = 0
    for path in _iter_files(root, file_glob):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_index, line in enumerate(lines):
            if pattern.lower() not in line.lower():
                continue
            total_count += 1
            if len(matches) < limit:
                matches.append(
                    {
                        "path": str(path),
                        "line": line_index + 1,
                        "text": line[:_MAX_SNIPPET_CHARS],
                    }
                )
    return json_result(
        success=True,
        self_code_root=str(SELF_CODE_ROOT),
        pattern=pattern,
        matches=matches,
        total_count=total_count,
        truncated=total_count > len(matches),
    )


def _self_code_read(args: dict, runtime: dict) -> str:
    path = _safe_self_code_path(args.get("path"))
    max_chars = max(1, min(int(args.get("max_chars") or 20000), 100000))
    offset = max(0, int(args.get("offset") or 0))
    if not path.is_file():
        return json_result(success=False, error=f"File not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    page = text[offset : offset + max_chars]
    return json_result(
        success=True,
        self_code_root=str(SELF_CODE_ROOT),
        path=str(path),
        content=page,
        offset=offset,
        total_chars=len(text),
        truncated=offset + max_chars < len(text),
        next_offset=(offset + max_chars if offset + max_chars < len(text) else None),
    )


def _self_code_patch(args: dict, runtime: dict) -> str:
    path = _safe_self_code_path(args.get("path"))
    old = str(args.get("old_text") or "")
    new = args.get("new_text")
    replace_all = bool(args.get("replace_all"))
    if not old or new is None:
        return json_result(success=False, error="old_text and new_text are required")
    if not path.is_file():
        return json_result(success=False, error=f"File not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    count = text.count(old)
    if count != 1 and not replace_all:
        return json_result(success=False, error=f"Expected one match, found {count}")
    path.write_text(text.replace(old, str(new), -1 if replace_all else 1), encoding="utf-8")
    return json_result(success=True, path=str(path), replacements=count if replace_all else 1)


registry.register(
    "self_code_search",
    {
        "description": "Search this agent's core source code under research_agent/. Use before reading or patching agent internals.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "default": "."},
                "file_glob": {"type": "string", "description": "Optional file filter, e.g. '*.py'."},
                "limit": {"type": "integer", "default": 50},
            },
            "required": ["pattern"],
        },
    },
    _self_code_search,
)
registry.register(
    "self_code_read",
    {
        "description": "Read this agent's core source code under research_agent/. Use offset/max_chars for large files.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_chars": {"type": "integer", "default": 20000},
                "offset": {"type": "integer", "default": 0},
            },
            "required": ["path"],
        },
    },
    _self_code_read,
)
registry.register(
    "self_code_patch",
    {
        "description": "Patch this agent's core source code under research_agent/. Requires a unique old_text unless replace_all is true.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string"},
                "new_text": {"type": "string"},
                "replace_all": {"type": "boolean", "default": False},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    _self_code_patch,
)
