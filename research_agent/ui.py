"""Agent UI — pretty terminal output with color, timers, and LiveDashboard."""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_COLOR   = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
_DYNAMIC = sys.stdout.isatty()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible_len(s: str) -> int:
    return len(_ANSI_RE.sub("", s))


class _C:
    RESET   = "\033[0m"  if _COLOR else ""
    BOLD    = "\033[1m"  if _COLOR else ""
    CYAN    = "\033[96m" if _COLOR else ""
    GREEN   = "\033[92m" if _COLOR else ""
    RED     = "\033[91m" if _COLOR else ""
    YELLOW  = "\033[93m" if _COLOR else ""
    GREY    = "\033[90m" if _COLOR else ""
    MAGENTA = "\033[95m" if _COLOR else ""
    BLUE    = "\033[94m" if _COLOR else ""


class ConsoleUI:
    """
    Pretty-prints agent loop steps.

    When a TTY is available, integrates with LiveDashboard to show all
    parallel agents in a shared status panel.  Each completed tool call
    is printed as a compact one-liner above the panel.

    When no TTY is available (CI, log files), falls back to Unicode box format.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        width: int = 76,
        label: str = "agent",
        error_log_path: Path | str | None = None,
    ) -> None:
        self.enabled = enabled
        self.W       = width
        self.label   = label
        self._error_log_path: Path | None = Path(error_log_path) if error_log_path else None
        self._cur_args: dict[str, Any] = {}

        self._timer_thread: threading.Thread | None = None
        self._timer_stop:   threading.Event  | None = None
        self._timer_start:  float = 0.0
        self._cur_iter: int = 0
        self._cur_tool: str = ""

        # Dashboard integration (TTY only) — slot is registered lazily on first model_start
        self._db = None
        if enabled and _DYNAMIC:
            try:
                from .tui import LiveDashboard
                self._db = LiveDashboard.get()
            except Exception:
                pass  # non-fatal — fall back to box mode

    # ── public API (agent.py calls these) ────────────────────────────────

    def session_start(self, session_id: str, task_id: str) -> None:
        if not self.enabled:
            return
        line = (
            f"{_C.BOLD}{_C.BLUE}▶ session{_C.RESET}"
            f"  {_C.GREY}id={session_id}  task={task_id}{_C.RESET}"
        )
        if self._db:
            self._db.println(line)
        else:
            print(line, flush=True)

    def model_start(self, iteration: int) -> None:
        if not self.enabled:
            return
        self._cur_iter = iteration
        if self._db:
            if iteration == 1:
                self._db.reset(self.label)   # register or re-activate; resets timer
            self._db.update(self.label, iteration=iteration, tool="🤔 model")
        else:
            self._rule(f"step {iteration} | model")

    def tool_start(self, name: str, args: dict[str, Any]) -> None:
        if not self.enabled:
            return
        self._timer_start = time.monotonic()
        self._cur_tool    = name
        self._cur_args    = args

        if self._db:
            self._db.update(self.label, tool=name, args_preview=_fmt_args_preview(args))
        else:
            self._box_tool_start(self._cur_iter, name, args)

    def tool_done(self, name: str, result: str) -> None:
        if not self.enabled:
            return
        elapsed    = time.monotonic() - self._timer_start
        is_success = _parse_success(result)
        mark       = f"{_C.GREEN}✓{_C.RESET}" if is_success else f"{_C.RED}✗{_C.RESET}"
        if not is_success:
            self._record_error(result)

        if self._db:
            self._db.update(self.label, tool="", args_preview="")
            preview = _fmt_result(result, max_len=80)
            line = (
                f"  {_C.GREY}[{self.label}]{_C.RESET}"
                f" {_C.GREY}#{self._cur_iter}{_C.RESET}"
                f" {_C.CYAN}{name}{_C.RESET}"
                f" {_C.GREY}{elapsed:.1f}s{_C.RESET} {mark}"
                f"  {_C.GREY}{preview}{_C.RESET}"
            )
            self._db.println(line)
        else:
            self._box_tool_end(elapsed, result, is_success)

    def llm_thinking(self, iteration: int, content: str) -> None:
        """Called when the model emits a reasoning/thinking block."""
        if not self.enabled or not content:
            return
        self._cur_iter = iteration
        if self._db:
            self._db.update(self.label, tool="💭 thinking")
        else:
            bc = _C.MAGENTA
            self._top(f"[{iteration}] thinking", bc)
            for line in content.splitlines():
                self._row(line or " ", _C.MAGENTA, bc)
            self._bot(bc)

    def compact(self, reason: str) -> None:
        if not self.enabled:
            return
        line = f"  {_C.YELLOW}⚡ compact{_C.RESET}  {_C.GREY}{reason}{_C.RESET}"
        if self._db:
            self._db.println(line)
        else:
            self._rule(f"compact | {reason}")

    def event(self, label: str, detail: str = "") -> None:
        if not self.enabled:
            return
        ts = time.strftime("%H:%M:%S")
        suffix = f"  {_C.GREY}{detail}{_C.RESET}" if detail else ""
        line = f"{_C.GREY}[{ts}]{_C.RESET} {label}{suffix}"
        if self._db:
            self._db.println(line)
        else:
            print(line, flush=True)

    def interrupt(self) -> None:
        self.event("interrupt", "paused — enter correction or /stop")

    def final(self) -> None:
        if not self.enabled:
            return
        if self._db:
            self._db.update(self.label, tool="✍ finalizing")

    def final_answer(self, text: str, iterations: int) -> None:
        if not self.enabled:
            return
        if self._db:
            self._db.mark_done(self.label)
            self._db.println(
                f"  {_C.GREEN}✓{_C.RESET} {_C.GREY}[{self.label}]{_C.RESET}"
                f" {_C.GREY}done — {iterations} iter{'s' if iterations != 1 else ''}{_C.RESET}"
            )
        else:
            bc = _C.GREEN
            label = f"FINAL ANSWER  ({iterations} iteration{'s' if iterations != 1 else ''})"
            self._top(label, bc)
            for line in (text or "(empty)").splitlines():
                self._row(line or " ", _C.GREEN, bc)
            self._bot(bc)

    def saved(self, path: str) -> None:
        if not self.enabled:
            return
        line = f"  {_C.GREEN}💾 saved{_C.RESET}  {_C.GREY}{path}{_C.RESET}"
        if self._db:
            self._db.println(line)
        else:
            print(line, flush=True)

    def self_review_start(self) -> None:
        self.event("self-review", "starting")

    def self_review_done(self) -> None:
        self.event("self-review", "complete")

    # ── error recording ───────────────────────────────────────────────────

    def _record_error(self, result: str) -> None:
        if not self._error_log_path:
            return
        entry = {
            "time":   datetime.now().isoformat(timespec="seconds"),
            "agent":  self.label,
            "iter":   self._cur_iter,
            "tool":   self._cur_tool,
            "args":   _fmt_args(self._cur_args, max_len=300),
            "result": result[:1000] + ("…" if len(result) > 1000 else ""),
        }
        try:
            self._error_log_path.parent.mkdir(parents=True, exist_ok=True)
            existing: list[dict] = []
            if self._error_log_path.exists():
                try:
                    existing = json.loads(self._error_log_path.read_text(encoding="utf-8"))
                except Exception:
                    existing = []
            existing.append(entry)
            self._error_log_path.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            print(f"[Logger] Failed to write error log: {exc}")

    # ── fallback box rendering (non-TTY) ──────────────────────────────────

    def _box_tool_start(self, iteration: int, name: str, args: dict[str, Any]) -> None:
        bc = _C.CYAN
        self._top(f"[{iteration}] {_C.BOLD}{name}{_C.RESET}{bc}", bc)
        self._row(_fmt_args(args), _C.CYAN, bc)
        if _DYNAMIC:
            self._timer_stop   = threading.Event()
            self._timer_thread = threading.Thread(target=self._run_timer, daemon=True)
            self._timer_thread.start()
        else:
            self._mid("running…", _C.GREY)

    def _box_tool_end(self, elapsed: float, result: str, is_success: bool) -> None:
        if self._timer_thread is not None:
            assert self._timer_stop is not None
            self._timer_stop.set()
            self._timer_thread.join()
            self._timer_thread = None
            self._timer_stop   = None
        bc_res = _C.GREEN if is_success else _C.RED
        self._mid(f"result  ({elapsed:.1f}s)", _C.GREY)
        self._row(_fmt_result(result), bc_res, _C.GREY)
        self._bot(_C.GREY)

    def _run_timer(self) -> None:
        assert self._timer_stop is not None
        while not self._timer_stop.wait(0.1):
            elapsed = time.monotonic() - self._timer_start
            label   = f"{_C.YELLOW}⏱{_C.RESET}{_C.GREY}  {elapsed:.1f}s"
            self._mid(label, _C.GREY, end="")

    def _rule(self, title: str) -> None:
        ts = time.strftime("%H:%M:%S")
        label = f" {ts} {title} "
        width = self.W
        if len(label) >= width:
            print(label.strip(), flush=True)
            return
        left = 4
        right = width - len(label) - left
        print(("=" * left) + label + ("=" * right), flush=True)

    # ── box primitives ────────────────────────────────────────────────────

    def _top(self, label: str, bc: str) -> None:
        dashes = max(self.W - 4 - _visible_len(label), 0)
        print(f"{bc}┌─ {label} {'─' * dashes}─┐{_C.RESET}")

    def _mid(self, label: str, bc: str = "", *, end: str = "\n") -> None:
        bc = bc or _C.GREY
        dashes = max(self.W - 4 - _visible_len(label), 0)
        print(f"\r{bc}├─ {label} {'─' * dashes}─┤{_C.RESET}", end=end, flush=True)

    def _bot(self, bc: str) -> None:
        print(f"{bc}└{'─' * (self.W - 2)}┘{_C.RESET}")

    def _row(self, text: str, color: str, bc: str) -> None:
        inner = self.W - 4
        text  = text or " "
        while len(text) > inner:
            chunk, text = text[:inner], text[inner:]
            print(f"{bc}│{_C.RESET} {color}{chunk}{_C.RESET}{' ' * (inner - len(chunk))} {bc}│{_C.RESET}")
        print(f"{bc}│{_C.RESET} {color}{text}{_C.RESET}{' ' * (inner - len(text))} {bc}│{_C.RESET}")


# ── formatting helpers ────────────────────────────────────────────────────

def _parse_success(raw: str) -> bool:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return bool(data.get("success", True))
    except (json.JSONDecodeError, TypeError):
        pass
    return True


def _fmt_args_preview(args: dict[str, Any], max_len: int = 32) -> str:
    if not args:
        return ""
    priority = ("query", "url", "section", "ref", "text", "path", "filename", "name", "command")
    for key in priority:
        if key in args:
            val = str(args[key]).replace("\n", " ")
            return val[:max_len] + "…" if len(val) > max_len else val
    for val in args.values():
        if isinstance(val, str) and val.strip():
            val = val.replace("\n", " ")
            return val[:max_len] + "…" if len(val) > max_len else val
    return ""


def _fmt_args(args: dict[str, Any], max_len: int = 140) -> str:
    if not args:
        return "(no args)"
    parts = []
    for k, v in args.items():
        val = repr(v) if isinstance(v, str) else str(v)
        parts.append(f"{k}={val}")
    text = ", ".join(parts)
    return text if len(text) <= max_len else text[:max_len] + "…"


def _fmt_result(raw: str, max_len: int = 240) -> str:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            display: dict[str, Any] = {}
            for k, v in data.items():
                if isinstance(v, str) and len(v) > 80:
                    display[k] = v[:80] + "…"
                elif isinstance(v, list) and len(v) > 6:
                    display[k] = [*v[:6], f"…+{len(v)-6} more"]
                else:
                    display[k] = v
            text = json.dumps(display, ensure_ascii=False)
            return text if len(text) <= max_len else text[:max_len] + "…"
    except (json.JSONDecodeError, TypeError):
        pass
    return raw[:max_len] + "…" if len(raw) > max_len else raw
