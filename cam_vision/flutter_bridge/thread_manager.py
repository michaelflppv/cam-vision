from __future__ import annotations

import queue
from typing import Any, Optional


class EventQueue:
    def __init__(self, maxsize: int = 200):
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=maxsize)

    def put(self, item: Any) -> None:
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            pass

    def get_nowait(self) -> Optional[Any]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def clear(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def empty(self) -> bool:
        return self._queue.empty()
