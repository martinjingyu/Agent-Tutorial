from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def _api_key() -> str | None:
    return os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")


def _base_url() -> str | None:
    return (
        os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEEPSEEK_BASE_URL
    )


def _is_deepseek() -> bool:
    return (_base_url() or "").rstrip("/") == DEEPSEEK_BASE_URL


def _default_model() -> str:
    if os.getenv("DEEPSEEK_MODEL"):
        return os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    if os.getenv("DEEPSEEK_API_KEY") or _base_url().rstrip("/") == DEEPSEEK_BASE_URL:
        return "deepseek-v4-flash"
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class LLMClient:
    def __init__(self, model: str | None = None):
        self.model = model or _default_model()
        self.client = OpenAI(
            api_key=_api_key(),
            base_url=_base_url(),
        )

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": "auto" if tools else None,
            "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.2")),
        }
        if _is_deepseek():
            thinking = os.getenv("DEEPSEEK_THINKING", "disabled").strip().lower()
            if thinking in {"enabled", "disabled"}:
                kwargs["extra_body"] = {"thinking": {"type": thinking}}
        return self.client.chat.completions.create(**kwargs)

    def complete_text(self, prompt: str, *, temperature: float = 0.2) -> str:
        kwargs: dict[str, Any] = {
            "model": os.getenv("COMPACTION_MODEL", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if _is_deepseek():
            thinking = os.getenv("DEEPSEEK_THINKING", "disabled").strip().lower()
            if thinking in {"enabled", "disabled"}:
                kwargs["extra_body"] = {"thinking": {"type": thinking}}
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
