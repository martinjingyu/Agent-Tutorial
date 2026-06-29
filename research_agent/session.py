from __future__ import annotations

import sys
import threading
from typing import Any

from .agent import GeneralAgent
from .kanban_watcher import KanbanWatcher


class ChatSession:
    """Multi-turn session manager for GeneralAgent.

    Maintains conversation history across turns. Two usage modes:

    **Library / batch mode** — caller controls the loop::

        session = ChatSession(agent)
        print(session.run_turn("Research professor X"))
        # ... later, after kanban pipeline finishes ...
        pending = session.drain_pending()
        if pending:
            print(session.run_turn(pending[0]["content"]))

    **Interactive / CLI mode** — session owns the terminal::

        ChatSession(agent).start_interactive()
    """

    def __init__(
        self,
        agent: GeneralAgent,
        history: list[dict[str, Any]] | None = None,
    ) -> None:
        self.agent = agent
        self._history: list[dict[str, Any]] = list(history or [])
        self._pending: list[list[dict[str, Any]]] = []
        self._watcher: KanbanWatcher | None = None

    # ── public API ────────────────────────────────────────────────────────

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history

    def run_turn(self, user_message: str) -> str:
        """Run one agent turn. Updates history. Returns final text."""
        result = self.agent.run(user_message, history=self._history)
        self._history = result["messages"]
        return result["final"]

    def drain_pending(self) -> list[list[dict[str, Any]]]:
        """Return and clear any kanban notifications that arrived since last check.

        Library users call this in their own scheduling loop to decide when to
        trigger the next run_turn().
        """
        items, self._pending = self._pending, []
        return items

    def start_watcher(self, poll_interval: float = 0.5) -> ChatSession:
        """Start background kanban event watcher. Returns self for chaining.

        Pending notifications are queued in self._pending and can be drained
        via drain_pending(), or handled automatically by start_interactive().
        """
        if self._watcher is None:
            self._watcher = KanbanWatcher(
                on_event=self._on_kanban_event,
                poll_interval=poll_interval,
            ).start()
        return self

    def stop_watcher(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def start_interactive(self, *, input_prompt: str = "\nYou> ") -> None:
        """Take over terminal input. Blocks until /exit or EOF.

        Starts the kanban watcher automatically. When a pipeline completes,
        a new agent turn fires without waiting for user input.
        """
        self.start_watcher()
        try:
            self._interactive_loop(input_prompt)
        finally:
            self.stop_watcher()

    # ── internals ─────────────────────────────────────────────────────────

    def _on_kanban_event(self, msgs: list[dict[str, Any]]) -> None:
        self._pending.append(msgs)
        # Print a visible prompt so the user knows something happened;
        # also attempt to interrupt the blocked input() call.
        sys.stdout.write("\n[kanban] Pipeline complete! Press Enter to review...\n")
        sys.stdout.flush()
        _interrupt_input()

    def _interactive_loop(self, input_prompt: str) -> None:
        while True:
            # Drain notifications that arrived while agent was running
            if self._pending:
                msgs = self._pending.pop(0)
                print("\n[kanban] Starting review...")
                print(self.run_turn(msgs[0]["content"]))
                continue

            try:
                user_input = input(input_prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            # Watcher may have deposited events while we were in input()
            if self._pending and not user_input:
                msgs = self._pending.pop(0)
                print("\n[kanban] Starting review...")
                print(self.run_turn(msgs[0]["content"]))
                continue

            if not user_input:
                continue
            if user_input in {"/exit", "/quit"}:
                break

            print(self.run_turn(user_input))


def _interrupt_input() -> None:
    """Best-effort: nudge a blocked input() to return on Windows/Unix.

    Failure is non-fatal — the user just presses Enter manually.
    """
    try:
        if sys.platform == "win32":
            import ctypes

            class _KeyEventRecord(ctypes.Structure):
                _fields_ = [
                    ("bKeyDown",           ctypes.c_long),
                    ("wRepeatCount",       ctypes.c_ushort),
                    ("wVirtualKeyCode",    ctypes.c_ushort),
                    ("wVirtualScanCode",   ctypes.c_ushort),
                    ("uChar",              ctypes.c_ushort),
                    ("dwControlKeyState",  ctypes.c_ulong),
                ]

            class _EventUnion(ctypes.Union):
                _fields_ = [("KeyEvent", _KeyEventRecord)]

            class _InputRecord(ctypes.Structure):
                _fields_ = [
                    ("EventType", ctypes.c_ushort),
                    ("_pad",      ctypes.c_ushort),
                    ("Event",     _EventUnion),
                ]

            records = (_InputRecord * 2)()
            for i, down in enumerate([1, 0]):
                records[i].EventType           = 0x0001  # KEY_EVENT
                records[i].Event.KeyEvent.bKeyDown        = down
                records[i].Event.KeyEvent.wRepeatCount    = 1
                records[i].Event.KeyEvent.wVirtualKeyCode = 0x0D  # VK_RETURN
                records[i].Event.KeyEvent.uChar           = 0x0D  # '\r'
            h = ctypes.windll.kernel32.GetStdHandle(-10)
            written = ctypes.c_ulong(0)
            ctypes.windll.kernel32.WriteConsoleInputW(h, records, 2, ctypes.byref(written))
        else:
            import signal
            if hasattr(signal, "SIGALRM"):
                signal.raise_signal(signal.SIGALRM)
    except Exception:
        pass
