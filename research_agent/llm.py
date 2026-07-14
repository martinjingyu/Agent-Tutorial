from __future__ import annotations

import base64
import json
import os
import random
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from openai import OpenAI

from .env import get_env


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"


def _provider(explicit: str | None = None) -> str:
    if explicit:
        return explicit.strip().lower()
    value = (
        get_env("AGENT_PROVIDER")
        or get_env("MODEL_PROVIDER")
        or get_env("SCREENING_MODEL_PROVIDER")
    )
    if value:
        return value.strip().lower()
    if get_env("CODEX_MODEL"):
        return "codex"
    if get_env("DEEPSEEK_API_KEY"):
        return "deepseek"
    return "openai"


def _deepseek_model() -> str:
    return get_env("DEEPSEEK_MODEL", "deepseek-v4-flash")


def _openai_model() -> str:
    return get_env("OPENAI_MODEL", "gpt-4o-mini")


def _codex_model() -> str:
    return get_env("CODEX_MODEL", "gpt-5.4")


def _default_model(provider: str) -> str:
    if provider == "codex":
        return _codex_model()
    if provider == "deepseek":
        return _deepseek_model()
    return _openai_model()


def _deepseek_extra_body() -> dict[str, Any] | None:
    thinking = get_env("DEEPSEEK_THINKING", "disabled").strip().lower()
    if thinking in {"enabled", "disabled"}:
        return {"thinking": {"type": thinking}}
    return None


def _read_codex_access_token() -> str:
    candidates = [
        Path(get_env("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json",
        Path.home() / ".hermes" / "auth.json",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        tokens = None
        providers = data.get("providers")
        if isinstance(providers, dict):
            state = providers.get("openai-codex")
            if isinstance(state, dict):
                tokens = state.get("tokens")
        if tokens is None:
            tokens = data.get("tokens")
        if isinstance(tokens, dict) and tokens.get("access_token"):
            return str(tokens["access_token"])
    raise RuntimeError("No Codex access token found. Run `codex login` first.")


def _codex_headers(token: str) -> dict[str, str]:
    headers: dict[str, str] = {
        "User-Agent": "codex_cli_rs/0.0.0",
        "originator": "codex_cli_rs",
    }
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        account_id = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
        if account_id:
            headers["ChatGPT-Account-ID"] = str(account_id)
    except Exception:
        pass
    return headers


def _to_responses_input(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    instructions = ""
    items: list[dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content") or ""

        if role == "system":
            instructions = content if isinstance(content, str) else str(content)
            continue
        if role == "user":
            text = content if isinstance(content, str) else str(content)
            items.append({"role": "user", "content": [{"type": "input_text", "text": text}]})
            continue
        if role == "assistant":
            if content:
                items.append({"role": "assistant", "content": [{"type": "output_text", "text": content}]})
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    function = tc.get("function") or {}
                    items.append(
                        {
                            "type": "function_call",
                            "call_id": tc.get("id", ""),
                            "name": function.get("name", ""),
                            "arguments": function.get("arguments", "{}"),
                        }
                    )
            continue
        if role == "tool":
            output = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            items.append(
                {
                    "type": "function_call_output",
                    "call_id": msg.get("tool_call_id", ""),
                    "output": output,
                }
            )

    return instructions, items


def _convert_tools_for_responses(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for tool in tools:
        if tool.get("type") == "function" and isinstance(tool.get("function"), dict):
            function = tool["function"]
            converted.append(
                {
                    "type": "function",
                    "name": function.get("name", ""),
                    "description": function.get("description", ""),
                    "parameters": function.get("parameters", {}),
                    "strict": False,
                }
            )
        else:
            converted.append(tool)
    return converted


def _attr(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _make_tool_call(call_id: str, name: str, arguments: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments or "{}"),
    )


def _chat_completion_like(content: str | None, tool_calls: list[SimpleNamespace], usage: Any = None) -> SimpleNamespace:
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


# Models that should be silently upgraded to deepseek-v4-flash
_DEEPSEEK_LEGACY_ALIASES = {"deepseek-chat", "deepseek-v3", "deepseek-v3-0324"}


class LLMClient:
    def __init__(self, model: str | None = None, provider: str | None = None):
        self.provider = _provider(provider)
        raw = model or _default_model(self.provider)
        # Upgrade legacy deepseek aliases → v4-flash
        if self.provider == "deepseek" and raw in _DEEPSEEK_LEGACY_ALIASES:
            raw = "deepseek-v4-flash"
        self.model = raw
        self._codex_token: str | None = None
        self._client: OpenAI | None = None

    def _client_or_create(self) -> OpenAI:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> OpenAI:
        if self.provider == "codex":
            self._codex_token = _read_codex_access_token()
            return OpenAI(
                api_key=self._codex_token,
                base_url=get_env("CODEX_BASE_URL", CODEX_BASE_URL),
                default_headers=_codex_headers(self._codex_token),
                max_retries=0,
                timeout=120.0,
            )
        if self.provider == "deepseek":
            return OpenAI(
                api_key=get_env("DEEPSEEK_API_KEY"),
                base_url=get_env("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL),
                timeout=120.0,
                max_retries=0,
            )
        return OpenAI(
            api_key=get_env("OPENAI_API_KEY"),
            base_url=get_env("OPENAI_BASE_URL") or None,
            timeout=120.0,
            max_retries=0,
        )

    @staticmethod
    def _is_transient(exc: Exception) -> bool:
        """True for timeout / connection / 5xx errors that are worth retrying."""
        name = type(exc).__name__
        if any(k in name for k in ("Timeout", "Connection", "ServiceUnavailable")):
            return True
        status = getattr(exc, "status_code", None) or getattr(
            getattr(exc, "response", None), "status_code", None
        )
        return status in (429, 500, 502, 503, 504)

    _MAX_RETRIES = 5

    @classmethod
    def _retry_wait(cls, attempt: int) -> float:
        """Exponential backoff (5s, 10s, 20s, 40s, capped at 60s) plus up to 3s of
        random jitter. The jitter matters more than usual here: callers like
        Agent-Meeting fire several participants' LLM calls concurrently, so without
        jitter every one of them would retry in lockstep on the same schedule -- if a
        shared rate/concurrency limit caused the failures in the first place, retrying
        in lockstep just recreates the same burst that tripped it."""
        base = min(5 * (2 ** attempt), 60)
        return base + random.uniform(0, 3)

    def _with_retry(self, fn: Callable[[], Any]) -> Any:
        max_retries = self._MAX_RETRIES
        for attempt in range(max_retries + 1):
            try:
                return fn()
            except Exception as exc:
                if attempt < max_retries and self._is_transient(exc):
                    wait = self._retry_wait(attempt)
                    print(
                        f"[LLM] transient error ({type(exc).__name__}), "
                        f"retry {attempt + 1}/{max_retries} in {wait:.1f}s…",
                        flush=True,
                    )
                    time.sleep(wait)
                else:
                    raise

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        if self.provider == "codex":
            return self._codex_chat(messages, tools)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": "auto" if tools else None,
        }
        if self.provider == "deepseek":
            extra_body = _deepseek_extra_body()
            if extra_body:
                kwargs["extra_body"] = extra_body

        return self._with_retry(lambda: self._client_or_create().chat.completions.create(**kwargs))

    def complete_text(self, prompt: str) -> str:
        if self.provider == "codex":
            model = get_env("CODEX_COMPACTION_MODEL") or get_env("COMPACTION_MODEL") or self.model
            return self._codex_complete(prompt, model=model)

        kwargs: dict[str, Any] = {
            "model": get_env("COMPACTION_MODEL", self.model),
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.provider == "deepseek":
            extra_body = _deepseek_extra_body()
            if extra_body:
                kwargs["extra_body"] = extra_body

        response = self._with_retry(lambda: self._client_or_create().chat.completions.create(**kwargs))
        return response.choices[0].message.content or ""

    def _codex_session_kwargs(self) -> dict[str, Any]:
        session_id = uuid.uuid4().hex
        return {
            "store": False,
            "prompt_cache_key": session_id,
            "extra_headers": {"session_id": session_id, "x-client-request-id": session_id},
        }

    def _codex_is_rate_limit(self, exc: Exception) -> bool:
        status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
        return status == 429 or "rate limit" in str(exc).lower()

    def _codex_retry(self, fn):
        # The Codex/ChatGPT backend intermittently drops the streaming connection
        # mid-request ("Server disconnected without sending a response"), especially
        # on turns carrying a bulky tool result (browser snapshots, search results).
        # Without retrying those the same way _with_retry does for every other
        # provider, a transient disconnect crashes the whole agent run.
        max_retries = int(get_env("CODEX_MAX_RETRIES", "8"))
        retry_sleep = float(get_env("CODEX_RETRY_SLEEP", "3.5"))
        for attempt in range(max_retries + 1):
            try:
                return fn()
            except Exception as exc:
                if attempt >= max_retries:
                    raise
                if self._codex_is_rate_limit(exc):
                    print(f"[Codex] 429 rate limit; retrying in {retry_sleep}s ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_sleep)
                    continue
                if self._is_transient(exc):
                    print(f"[Codex] transient error ({type(exc).__name__}); retrying in {retry_sleep}s ({attempt + 1}/{max_retries})...")
                    time.sleep(retry_sleep)
                    continue
                raise

    def _codex_complete(self, prompt: str, *, model: str) -> str:
        def run_once() -> str:
            text_parts: list[str] = []
            with self._client_or_create().responses.stream(
                model=model,
                input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
                **self._codex_session_kwargs(),
            ) as stream:
                for event in stream:
                    if event.type == "response.output_text.delta" and event.delta:
                        text_parts.append(event.delta)
                final = stream.get_final_response()
            return "".join(text_parts) or getattr(final, "output_text", "") or ""

        return self._codex_retry(run_once)

    def _codex_chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        def run_once() -> Any:
            instructions, input_items = _to_responses_input(messages)
            kwargs: dict[str, Any] = {
                "model": self.model,
                "input": input_items,
                **self._codex_session_kwargs(),
            }
            if instructions:
                kwargs["instructions"] = instructions
            if tools:
                kwargs["tools"] = _convert_tools_for_responses(tools)
                kwargs["tool_choice"] = "auto"
                kwargs["parallel_tool_calls"] = True

            text_parts: list[str] = []
            collected: list[Any] = []
            with self._client_or_create().responses.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "response.output_text.delta" and event.delta:
                        text_parts.append(event.delta)
                    elif event.type == "response.output_item.done":
                        item = getattr(event, "item", None)
                        if item is not None:
                            collected.append(item)
                final = stream.get_final_response()

            output = getattr(final, "output", None)
            if isinstance(output, list) and not output and collected:
                output = collected

            tool_calls: list[SimpleNamespace] = []
            for item in output or []:
                if _attr(item, "type") == "function_call":
                    tool_calls.append(
                        _make_tool_call(
                            _attr(item, "call_id", ""),
                            _attr(item, "name", ""),
                            _attr(item, "arguments", "{}"),
                        )
                    )

            content = "".join(text_parts) or getattr(final, "output_text", "") or None
            return _chat_completion_like(content, tool_calls, usage=getattr(final, "usage", None))

        return self._codex_retry(run_once)
