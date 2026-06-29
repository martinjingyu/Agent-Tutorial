from __future__ import annotations

import threading
from typing import Callable


class KanbanWatcher:
    """Background thread that polls for kanban pipeline-complete notifications.

    When fire_notifications() writes a pending file, the watcher picks it up
    and calls on_event with the notification messages.  The caller decides
    what to do — typically trigger a new agent.run() turn.

    Usage::

        watcher = KanbanWatcher(on_event=lambda msgs: session.run_turn(msgs[0]["content"]))
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(
        self,
        on_event: Callable[[list[dict]], None],
        poll_interval: float = 0.5,
    ) -> None:
        self._on_event = on_event
        self._poll_interval = poll_interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> KanbanWatcher:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="kanban-watcher"
        )
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        try:
            from .tools.kanban import consume_pending_notifications
        except Exception:
            return
        while not self._stop.wait(self._poll_interval):
            try:
                msgs = consume_pending_notifications()
                if msgs:
                    self._on_event(msgs)
            except Exception:
                pass
