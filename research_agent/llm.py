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


_REASONING_EFFORTS = {"minimal", "low", "medium", "high"}


def _reasoning_effort_for_model(provider: str, model: str) -> str | None:
    """Per-model thinking effort, independent of caller-supplied overrides.

    Looks up <PROVIDER>_REASONING_EFFORT_<MODEL> first (e.g. deepseek + deepseek-v4-pro ->
    DEEPSEEK_REASONING_EFFORT_DEEPSEEK_V4_PRO, codex + gpt-5.6-sol -> CODEX_REASONING_EFFORT_GPT_5_6_SOL)
    so different models can run at different effort levels even under the same provider,
    then falls back to the provider-generic <PROVIDER>_REASONING_EFFORT. Returns None (no
    override, backend default) if neither is set or the value isn't a recognized effort.
    """
    slug = model.strip().upper().replace("-", "_").replace(".", "_")
    prefix = provider.strip().upper()
    effort = get_env(f"{prefix}_REASONING_EFFORT_{slug}") or get_env(f"{prefix}_REASONING_EFFORT")
    effort = effort.strip().lower()
    return effort if effort in _REASONING_EFFORTS else None


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


def _flatten_text_content(content: Any) -> str:
    """Best-effort plain-text rendering of chat-completions-style content, for spots
    (system instructions) where the Responses API only accepts a string -- any image
    parts are dropped rather than stringified into garbage."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") in ("text", "input_text")
        ]
        if texts:
            return "\n".join(texts)
    return str(content)


def _to_responses_content_parts(content: Any) -> list[dict[str, Any]]:
    """Converts chat-completions-style content (a plain string, or a list of
    {"type": "text", "text": ...} / {"type": "image_url", "image_url": {"url": ...}}
    parts -- the format every other call site in this codebase already builds
    messages in) into Responses API input parts (input_text / input_image).

    Previously this always stringified non-str content with str(content), which for
    a multimodal list silently turned an image part into an unusable Python repr
    instead of an image the model could actually see."""
    if isinstance(content, str):
        return [{"type": "input_text", "text": content}]
    if not isinstance(content, list):
        return [{"type": "input_text", "text": str(content)}]

    parts: list[dict[str, Any]] = []
    for part in content:
        if not isinstance(part, dict):
            parts.append({"type": "input_text", "text": str(part)})
            continue
        part_type = part.get("type")
        if part_type in ("text", "input_text"):
            parts.append({"type": "input_text", "text": part.get("text", "")})
            continue
        if part_type in ("image_url", "input_image"):
            image_url = part.get("image_url")
            url = image_url.get("url") if isinstance(image_url, dict) else (image_url or part.get("url"))
            if not url:
                continue
            image_part: dict[str, Any] = {"type": "input_image", "image_url": url}
            detail = image_url.get("detail") if isinstance(image_url, dict) else part.get("detail")
            if detail:
                image_part["detail"] = detail
            parts.append(image_part)
            continue
        # Unknown part shape -- render it as readable text rather than silently
        # dropping it, same fallback spirit as the old str(content) behavior.
        parts.append({"type": "input_text", "text": json.dumps(part, ensure_ascii=False)})
    return parts or [{"type": "input_text", "text": ""}]


def _to_responses_input(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    instructions = ""
    items: list[dict[str, Any]] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content") or ""

        if role == "system":
            instructions = _flatten_text_content(content)
            continue
        if role == "user":
            items.append({"role": "user", "content": _to_responses_content_parts(content)})
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


class Cancelled(Exception):
    """Raised by _with_retry/_codex_retry when cancel_check() flips true while a
    call is between attempts (queued for its next request or mid-backoff-sleep) --
    NOT while an attempt is actually in flight (a blocking HTTP call can't be
    interrupted from here without a bigger async/threading rework). Callers that
    care about a clean "user cancelled" outcome (GeneralAgent.run()) should catch
    this the same way they already catch KeyboardInterrupt, rather than treating it
    as a normal API failure worth retrying or reporting as an error."""


class LLMClient:
    def __init__(
        self,
        model: str | None = None,
        provider: str | None = None,
        reasoning_effort: str | None = None,
        cancel_check: Callable[[], bool] | None = None,
    ):
        self.provider = _provider(provider)
        raw = model or _default_model(self.provider)
        # Upgrade legacy deepseek aliases → v4-flash
        if self.provider == "deepseek" and raw in _DEEPSEEK_LEGACY_ALIASES:
            raw = "deepseek-v4-flash"
        self.model = raw
        self.reasoning_effort = reasoning_effort or _reasoning_effort_for_model(self.provider, raw)
        self._cancel_check = cancel_check
        self._codex_token: str | None = None
        self._client: OpenAI | None = None

    def _check_cancelled(self) -> None:
        if self._cancel_check is not None and self._cancel_check():
            raise Cancelled("Cancelled between LLM call attempts.")

    def _sleep_cancellable(self, seconds: float) -> None:
        """time.sleep(seconds), but checked in small slices so a cancel_check() flip
        mid-backoff takes effect within ~0.5s instead of only after the full sleep
        (which, at this class's own 60s-cap backoff, was the dominant reason a
        cancel button would feel unresponsive for a real turn stuck retrying)."""
        deadline = time.monotonic() + seconds
        while True:
            self._check_cancelled()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(0.5, remaining))

    def _client_or_create(self) -> OpenAI:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self) -> OpenAI:
        if self.provider == "codex":
            self._codex_token = _read_codex_access_token()
            # A single float here sets connect/read/write/pool all to the same
            # value. 120s is fine for a normal tool-calling turn, but gpt-5.6-sol
            # at high reasoning effort on a large prompt (e.g. synthesizing a full
            # meeting transcript in one call) can go well over two minutes before
            # its first streamed byte -- that showed up as httpx.ReadTimeout with
            # zero deltas ever yielded, not as a slow-but-working response.
            # CODEX_TIMEOUT_SECONDS lets a caller raise this further for other
            # long-reasoning workloads without editing this file.
            codex_timeout = float(get_env("CODEX_TIMEOUT_SECONDS", "600"))
            return OpenAI(
                api_key=self._codex_token,
                base_url=get_env("CODEX_BASE_URL", CODEX_BASE_URL),
                default_headers=_codex_headers(self._codex_token),
                max_retries=0,
                timeout=codex_timeout,
            )
        if self.provider == "deepseek":
            # Same reasoning as the codex branch above: a large prompt at high
            # reasoning effort can go quiet past 120s before the first streamed
            # byte, which surfaces as httpx.ReadTimeout with zero content ever
            # received, not as a slow-but-working response.
            deepseek_timeout = float(get_env("DEEPSEEK_TIMEOUT_SECONDS", "600"))
            return OpenAI(
                api_key=get_env("DEEPSEEK_API_KEY"),
                base_url=get_env("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL),
                timeout=deepseek_timeout,
                max_retries=0,
            )
        # Same reasoning as the codex/deepseek branches above.
        openai_timeout = float(get_env("OPENAI_TIMEOUT_SECONDS", "600"))
        return OpenAI(
            api_key=get_env("OPENAI_API_KEY"),
            base_url=get_env("OPENAI_BASE_URL") or None,
            timeout=openai_timeout,
            max_retries=0,
        )

    @staticmethod
    def _is_transient(exc: Exception) -> bool:
        """True for timeout / connection / protocol / 5xx errors that are worth
        retrying. "ProtocolError" covers httpx.RemoteProtocolError /
        httpcore.RemoteProtocolError ("peer closed connection without sending
        complete message body") -- the mid-stream disconnect _codex_retry's own
        docstring already describes, which has no status_code (it's a transport-
        level break, not an HTTP response) so it fell through this check entirely
        until this was added, meaning the retry loop built for exactly this case
        never actually caught it."""
        name = type(exc).__name__
        if any(k in name for k in ("Timeout", "Connection", "ServiceUnavailable", "ProtocolError")):
            return True
        status = getattr(exc, "status_code", None) or getattr(
            getattr(exc, "response", None), "status_code", None
        )
        if status == 429:
            return True
        # Any 5xx, not just the standard handful -- Cloudflare-fronted backends (e.g.
        # chatgpt.com/backend-api/codex) also return their own extended codes like 520
        # ("unknown error")/521/522/524/etc. for transient origin/proxy hiccups, and
        # those are just as safe to retry as a plain 502/503.
        return isinstance(status, int) and 500 <= status < 600

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
            self._check_cancelled()
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
                    self._sleep_cancellable(wait)
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
            extra_body = self._deepseek_reasoning_kwargs()
            if extra_body:
                kwargs["extra_body"] = extra_body
            if self.reasoning_effort:
                kwargs["reasoning_effort"] = self.reasoning_effort

        return self._with_retry(lambda: self._client_or_create().chat.completions.create(**kwargs))

    def chat_stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):
        """Yields text deltas as they arrive instead of blocking until the full
        response is ready like chat() does -- useful for a long, slow call (e.g. a
        big synthesis prompt at high reasoning effort) where a caller wants live
        proof the connection is still alive rather than a silent multi-minute wait
        that's indistinguishable from a hang until it either finishes or times out.

        Deliberately no automatic retry here, unlike chat()/_with_retry: retrying a
        partially-yielded stream would either duplicate text already handed to the
        caller or require buffering everything anyway, which defeats the point of
        streaming. A failure (including on the very first byte) propagates as an
        exception; callers that want retry semantics should use chat() instead."""
        if self.provider == "codex":
            instructions, input_items = _to_responses_input(messages)
            kwargs: dict[str, Any] = {
                "model": self.model,
                "input": input_items,
                **({"reasoning": {"effort": self.reasoning_effort}} if self.reasoning_effort else {}),
                **self._codex_session_kwargs(),
            }
            if instructions:
                kwargs["instructions"] = instructions
            if tools:
                kwargs["tools"] = _convert_tools_for_responses(tools)
                kwargs["tool_choice"] = "auto"
                kwargs["parallel_tool_calls"] = True
            with self._client_or_create().responses.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "response.output_text.delta" and event.delta:
                        yield event.delta
            return

        kwargs = {
            "model": self.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": "auto" if tools else None,
            "stream": True,
        }
        if self.provider == "deepseek":
            extra_body = self._deepseek_reasoning_kwargs()
            if extra_body:
                kwargs["extra_body"] = extra_body
            if self.reasoning_effort:
                kwargs["reasoning_effort"] = self.reasoning_effort
        for chunk in self._client_or_create().chat.completions.create(**kwargs):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def _deepseek_reasoning_kwargs(self) -> dict[str, Any] | None:
        extra_body = _deepseek_extra_body()
        # A caller-supplied reasoning_effort always implies thinking must be on --
        # DEEPSEEK_THINKING=disabled (the default) would otherwise silently discard
        # the effort level the caller explicitly asked for.
        if self.reasoning_effort:
            extra_body = {**(extra_body or {}), "thinking": {"type": "enabled"}}
        return extra_body

    def complete_text(self, prompt: str) -> str:
        if self.provider == "codex":
            model = get_env("CODEX_COMPACTION_MODEL") or get_env("COMPACTION_MODEL") or self.model
            return self._codex_complete(prompt, model=model)

        kwargs: dict[str, Any] = {
            "model": get_env("COMPACTION_MODEL", self.model),
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.provider == "deepseek":
            extra_body = self._deepseek_reasoning_kwargs()
            if extra_body:
                kwargs["extra_body"] = extra_body
            if self.reasoning_effort:
                kwargs["reasoning_effort"] = self.reasoning_effort

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
            self._check_cancelled()
            try:
                return fn()
            except Exception as exc:
                if attempt >= max_retries:
                    raise
                if self._codex_is_rate_limit(exc):
                    print(f"[Codex] 429 rate limit; retrying in {retry_sleep}s ({attempt + 1}/{max_retries})...")
                    self._sleep_cancellable(retry_sleep)
                    continue
                if self._is_transient(exc):
                    print(f"[Codex] transient error ({type(exc).__name__}); retrying in {retry_sleep}s ({attempt + 1}/{max_retries})...")
                    self._sleep_cancellable(retry_sleep)
                    continue
                raise

    def _codex_complete(self, prompt: str, *, model: str) -> str:
        def run_once() -> str:
            text_parts: list[str] = []
            # A caller-supplied reasoning_effort (e.g. judge.py's LLMClient(...,
            # reasoning_effort="medium")) must win over the env-var lookup, mirroring
            # _codex_chat's behavior below -- otherwise an explicit constructor value
            # is silently discarded whenever the CODEX_REASONING_EFFORT* env vars
            # aren't set (the common case), and the call runs at whatever the backend's
            # own default happens to be instead of what the caller asked for.
            effort = self.reasoning_effort or _reasoning_effort_for_model(self.provider, model)
            with self._client_or_create().responses.stream(
                model=model,
                input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
                **({"reasoning": {"effort": effort}} if effort else {}),
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
                **({"reasoning": {"effort": self.reasoning_effort}} if self.reasoning_effort else {}),
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
