"""
LiveDashboard — parallel agent status panel with a kanban view.

Layout (bottom of terminal, scrolls up as agents print):
  ── Kanban: board-name ──────────────────────────────────────────
  ✓ task-a title                                    done
  ⟳ task-b title                              running  45.2s
  · task-c title                                   ready

  ── Agents ──────────────────────────────────────────────────────
  [agent]  #3  respond_to_user  ⏱  2.1s
"""
from __future__ import annotations

import json
import os
import re as _re
import sys
import threading
import time
from pathlib import Path
from typing import Any

_ENABLED = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

_R  = "\033[0m"
_B  = "\033[1m"
_GR = "\033[90m"
_CY = "\033[96m"
_GN = "\033[92m"
_YL = "\033[93m"
_RD = "\033[91m"
_MG = "\033[95m"

_ANSI = _re.compile(r"\x1b\[[0-9;]*m")

def _vlen(s: str) -> int:
    return len(_ANSI.sub("", s))

def _pad(s: str, width: int) -> str:
    return s + " " * max(0, width - _vlen(s))


# ── Agent slot ───────────────────────────────────────────────────────────

class _Slot:
    __slots__ = ("label", "iteration", "tool", "args_preview", "start", "done")

    def __init__(self, label: str) -> None:
        self.label        = label
        self.iteration    = 0
        self.tool         = ""
        self.args_preview = ""
        self.start        = time.monotonic()
        self.done         = False


# ── Kanban scanning ───────────────────────────────────────────────────────

_KANBAN_TERMINAL = {"done", "error", "cancelled", "blocked"}
_TASK_ICON = {
    "done":      f"{_GN}✓{_R}",
    "error":     f"{_RD}✗{_R}",
    "running":   f"{_CY}⟳{_R}",
    "ready":     f"{_GR}·{_R}",
    "todo":      f"{_GR}·{_R}",
    "blocked":   f"{_YL}⌛{_R}",
    "cancelled": f"{_GR}✕{_R}",
}

def _scan_kanban(sessions_dir: Path) -> list[dict[str, Any]]:
    """Return active boards that have at least one non-terminal task."""
    kanban_dir = sessions_dir / "kanban"
    boards: list[dict[str, Any]] = []
    if not kanban_dir.exists():
        return boards
    for f in sorted(kanban_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            tasks = list(data.get("tasks", {}).values())
            if not tasks:
                continue
            if all(t.get("status") in _KANBAN_TERMINAL for t in tasks):
                continue   # fully complete — hide
            boards.append({
                "name":  data.get("board", f.stem),
                "tasks": tasks,
            })
        except Exception:
            pass
    return boards


def _task_elapsed(task: dict[str, Any], workers_dir: Path) -> float | None:
    """Return elapsed seconds for a running task by reading its worker cache."""
    if task.get("status") != "running":
        return None
    try:
        cache = workers_dir / f"{task['id']}.json"
        if cache.exists():
            d = json.loads(cache.read_text(encoding="utf-8"))
            started = d.get("started_at") or task.get("created_at")
            if started:
                from datetime import datetime
                t = datetime.fromisoformat(started)
                return (datetime.now() - t).total_seconds()
    except Exception:
        pass
    return None


# ── LiveDashboard ────────────────────────────────────────────────────────

class LiveDashboard:
    """Thread-safe live status panel: kanban boards + agent slots."""

    _instance: "LiveDashboard | None" = None
    _init_lock = threading.Lock()

    @classmethod
    def get(cls) -> "LiveDashboard":
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._lock   = threading.Lock()
        self._slots:  dict[str, _Slot] = {}
        self._order:  list[str]        = []
        self._drawn   = 0
        self._enabled = _ENABLED
        self._stop    = threading.Event()

        # Lazy-loaded sessions dir (avoids import-time side effects)
        self._sessions_dir: Path | None = None
        self._last_scan    = 0.0
        self._scan_interval = 2.0          # seconds between file-system scans
        self._kanban_cache: list[dict] = []

        if self._enabled:
            t = threading.Thread(target=self._run, daemon=True)
            t.start()

    def _get_sessions_dir(self) -> Path | None:
        if self._sessions_dir is None:
            try:
                from .paths import SESSIONS_DIR
                self._sessions_dir = SESSIONS_DIR
            except Exception:
                pass
        return self._sessions_dir

    # ── Agent slot API ────────────────────────────────────────────────────

    def register(self, label: str) -> None:
        with self._lock:
            if label not in self._slots:
                self._slots[label] = _Slot(label)
                self._order.append(label)

    def reset(self, label: str) -> None:
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

    def update(self, label: str, **kwargs: Any) -> None:
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

    # ── Rendering ─────────────────────────────────────────────────────────

    def _erase(self) -> None:
        if self._drawn:
            sys.__stdout__.write(f"\033[{self._drawn}A\033[J")
            self._drawn = 0

    def _draw(self) -> None:
        try:
            W = os.get_terminal_size().columns
        except OSError:
            W = 100

        lines: list[str] = []
        now = time.monotonic()

        # ── Kanban panels ─────────────────────────────────────────────────
        for board in self._kanban_cache:
            name  = board["name"]
            tasks = board["tasks"]
            sd    = self._sessions_dir
            workers_dir = (sd / "kanban" / name / "workers") if sd else None

            hdr = f"{_GR}  ── Kanban: {_B}{name}{_R}{_GR} {'─' * max(0, W - 14 - len(name))}{_R}"
            lines.append(hdr)
            for task in sorted(tasks, key=lambda t: t.get("created_at", "")):
                status = task.get("status", "?")
                icon   = _TASK_ICON.get(status, f"{_GR}?{_R}")
                title  = (task.get("title") or task.get("id") or "")[:40]
                right  = ""
                if status == "running" and workers_dir:
                    elapsed = _task_elapsed(task, workers_dir)
                    right = f"{_YL}{elapsed:6.1f}s{_R}" if elapsed is not None else f"{_GR}running{_R}"
                elif status == "done":
                    right = f"{_GN}done{_R}"
                elif status == "error":
                    right = f"{_RD}error{_R}"
                elif status == "ready":
                    right = f"{_GR}ready{_R}"
                elif status == "blocked":
                    right = f"{_YL}blocked{_R}"

                left  = f"  {icon} {_GR}{title}{_R}"
                gap   = max(2, W - _vlen(left) - _vlen(right) - 2)
                lines.append(left + " " * gap + right)

        # ── Agent strip ───────────────────────────────────────────────────
        active_slots = [self._slots[l] for l in self._order if not self._slots[l].done]
        if active_slots:
            divider = f"{_GR}  {'─' * min(W - 4, 72)}{_R}"
            lines.append(divider)
            for s in active_slots:
                elapsed   = now - s.start
                tool      = (s.tool or "—")[:24]
                preview   = s.args_preview
                tool_vis  = tool + (f"  {preview}" if preview else "")
                pad       = max(0, 30 - len(tool_vis))
                tool_part = f"{_CY}{tool}{_R}" + (f"  {_GR}{preview}{_R}" if preview else "") + " " * pad
                time_str  = f"{_YL}⏱{elapsed:6.1f}s{_R}"
                label_p   = f"{_B}[{s.label:<18}]{_R}"
                iter_p    = f"{_GR}#{s.iteration:<3}{_R}"
                raw = f"  {label_p} {iter_p} {tool_part} {time_str}"
                visible = _ANSI.sub("", raw)
                if len(visible) > W:
                    raw = raw[:W + (len(raw) - len(visible))]
                lines.append(raw)

        if not lines:
            return

        sys.__stdout__.write("\n".join(lines) + "\n")
        self._drawn = len(lines)

    def _maybe_scan(self) -> None:
        now = time.monotonic()
        if now - self._last_scan < self._scan_interval:
            return
        self._last_scan = now
        sd = self._get_sessions_dir()
        if sd:
            self._kanban_cache = _scan_kanban(sd)

    def _run(self) -> None:
        while not self._stop.wait(0.25):
            with self._lock:
                self._maybe_scan()
                self._erase()
                self._draw()
            sys.__stdout__.flush()
