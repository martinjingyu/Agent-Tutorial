from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .agent import GeneralAgent
from .env import load_dotenv
from .llm import LLMClient
from .ui import ConsoleUI


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _run_agent(payload: dict[str, Any], cache_path: Path) -> None:
    prompt = str(payload.get("user_prompt") or "")
    agent = GeneralAgent(
        model=payload.get("model"),
        provider=payload.get("provider"),
        max_iterations=int(payload.get("max_iterations") or 12),
        self_review=False,
        ui=ConsoleUI(enabled=False),
        live_cache_path=cache_path,
        live_cache_metadata={
            "kind": "plan_subagent",
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "user_prompt": prompt,
            "started_at": payload.get("started_at"),
        },
    )
    result = agent.run(prompt)
    cached = {
        "kind": "plan_subagent",
        "status": "completed",
        "started_at": payload.get("started_at"),
        "completed_at": _now(),
        "parent_session_id": payload.get("parent_session_id"),
        "parent_task_id": payload.get("parent_task_id"),
        "session_id": result.get("session_id"),
        "session_path": result.get("session_path"),
        "user_prompt": prompt,
        "final": result.get("final", ""),
        "messages": result.get("messages", []),
    }
    _write_cache(cache_path, cached)


def _run_llm(payload: dict[str, Any], cache_path: Path) -> None:
    system_prompt = str(payload.get("system_prompt") or "")
    user_prompt = str(payload.get("user_prompt") or "")
    _write_cache(
        cache_path,
        {
            "kind": "plan_subllm",
            "status": "running",
            "started_at": payload.get("started_at"),
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        },
    )
    llm = LLMClient(model=payload.get("model"), provider=payload.get("provider"))
    response = llm.chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        [],
    )
    content = response.choices[0].message.content or ""
    _write_cache(
        cache_path,
        {
            "kind": "plan_subllm",
            "status": "completed",
            "started_at": payload.get("started_at"),
            "completed_at": _now(),
            "parent_session_id": payload.get("parent_session_id"),
            "parent_task_id": payload.get("parent_task_id"),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model": llm.model,
            "provider": llm.provider,
            "final": content,
        },
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m research_agent.subprocess_worker <payload.json>", file=sys.stderr)
        return 2
    load_dotenv()
    payload_path = Path(sys.argv[1]).resolve()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    cache_path = Path(payload["cache_path"]).resolve()

    try:
        if payload.get("kind") == "plan_subagent":
            _run_agent(payload, cache_path)
        elif payload.get("kind") == "plan_subllm":
            _run_llm(payload, cache_path)
        else:
            raise ValueError(f"Unknown subprocess kind: {payload.get('kind')}")
    except Exception as exc:
        _write_cache(
            cache_path,
            {
                **payload,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "completed_at": _now(),
            },
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
