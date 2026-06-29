"""
LiveDashboard — parallel agent status panel.

Maintains a fixed status strip at the bottom of the terminal showing every
active agent's current tool and elapsed time.  All other output scrolls above
it normally.
"""
from __future__ import annotations

import os
import sys
import threading
import time

_ENABLED = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

_R  = "\033[0m"
_B  = "\033[1m"
_GR = "\033[90m"
_CY = "\033[96m"
_GN = "\033[92m"
_YL = "\033[93m"


class _Slot:
    __slots__ = ("label", "iteration", "tool", "args_preview", "start", "done")

    def __init__(self, label: str) -> None:
        self.label        = label
        self.iteration    = 0
        self.tool         = ""
        self.args_preview = ""
        self.start        = time.monotonic()
        self.done         = False


class LiveDashboard:
    """Thread-safe live status panel rendered at the bottom of the terminal."""

    _instance: LiveDashboard | None = None
    _init_lock = threading.Lock()

    @classmethod
    def get(cls) -> LiveDashboard:
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._lock        = threading.Lock()
        self._slots:  dict[str, _Slot] = {}
        self._order:  list[str]        = []
        self._drawn   = 0
        self._enabled = _ENABLED
        self._stop    = threading.Event()
        if self._enabled:
            t = threading.Thread(target=self._run, daemon=True)
            t.start()

    def register(self, label: str) -> None:
        with self._lock:
            if label not in self._slots:
                self._slots[label] = _Slot(label)
                self._order.append(label)

    def reset(self, label: str) -> None:
        """Re-activate a slot at the start of a new turn (resets timer and done flag)."""
        with self._lock:
            if label in self._slots:
                s = self._slots[label]
                s.done = False
                s.start = time.monotonic()
                s.tool = ""
                s.args_preview = ""
                s.iteration = 0
            else:
                self._slots[label] = _Slot(label)
                self._order.append(label)

    def update(self, label: str, **kwargs) -> None:
        with self._lock:
            s = self._slots.get(label)
            if s:
                for k, v in kwargs.items():
                    setattr(s, k, v)

    def mark_done(self, label: str) -> None:
        with self._lock:
            s = self._slots.get(label)
            if s:
                s.done = True
                s.tool = "✓"

    def println(self, line: str) -> None:
        """Print a line above the status panel (thread-safe)."""
        if not self._enabled:
            sys.__stdout__.write(line + "\n")
            sys.__stdout__.flush()
            return
        with self._lock:
            self._erase()
            sys.__stdout__.write(line + "\n")
            self._draw()
            sys.__stdout__.flush()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            self._erase()
            sys.__stdout__.flush()

    def _erase(self) -> None:
        if self._drawn:
            sys.__stdout__.write(f"\033[{self._drawn}A\033[J")
            self._drawn = 0

    def _draw(self) -> None:
        active = [self._slots[l] for l in self._order if not self._slots[l].done]
        if not active:
            return
        try:
            W = os.get_terminal_size().columns
        except OSError:
            W = 100

        import re as _re
        divider = f"{_GR}  {'─' * min(W - 4, 72)}{_R}"
        lines = [divider]
        now = time.monotonic()
        for s in active:
            elapsed = now - s.start
            tool    = (s.tool or "—")[:24]
            preview = s.args_preview
            tool_visible = tool + (f"  {preview}" if preview else "")
            pad = max(0, 30 - len(tool_visible))
            tool_part  = f"{_CY}{tool}{_R}" + (f"  {_GR}{preview}{_R}" if preview else "") + " " * pad
            time_str   = f"{_YL}⏱{elapsed:6.1f}s{_R}"
            label_part = f"{_B}[{s.label:<18}]{_R}"
            iter_part  = f"{_GR}#{s.iteration:<3}{_R}"
            raw = f"  {label_part} {iter_part} {tool_part} {time_str}"
            visible = _re.sub(r"\x1b\[[0-9;]*m", "", raw)
            if len(visible) > W:
                raw = raw[:W + (len(raw) - len(visible))]
            lines.append(raw)

        sys.__stdout__.write("\n".join(lines) + "\n")
        self._drawn = len(lines)

    def _run(self) -> None:
        while not self._stop.wait(0.25):
            with self._lock:
                self._erase()
                self._draw()
            sys.__stdout__.flush()
