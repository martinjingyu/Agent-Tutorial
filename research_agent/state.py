from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import SESSIONS_DIR


def new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_session(
    session_id: str,
    messages: list[dict[str, Any]],
    *,
    sub_agent: bool = False,
    system_prompt: str | None = None,
) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{session_id}.json"
    data: Any = messages
    if sub_agent or system_prompt is not None:
        meta: dict[str, Any] = {"__meta__": True, "sub_agent": sub_agent}
        if system_prompt is not None:
            meta["system_prompt"] = system_prompt
        data = [meta, *messages]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def load_session(session_id: str) -> list[dict[str, Any]]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    # Strip meta marker if present
    if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("__meta__"):
        return data[1:]
    return data

