from __future__ import annotations

import time
from collections import deque


class FPSMeter:
    """Simple rolling FPS meter."""

    def __init__(self, window: int = 60):
        self.window = max(2, window)
        self.ts = deque(maxlen=self.window)

    def tick(self) -> None:
        self.ts.append(time.time())

    def fps(self) -> float:
        if len(self.ts) < 2:
            return 0.0
        dt = self.ts[-1] - self.ts[0]
        if dt <= 0:
            return 0.0
        return (len(self.ts) - 1) / dt


class RateLimiter:
    """Sleep-based rate limiter targeting a given FPS."""

    def __init__(self, fps_target: float):
        self.period = 1.0 / max(0.1, fps_target)
        self._next_ts = time.time()

    def wait(self) -> None:
        now = time.time()
        sleep_s = self._next_ts - now
        if sleep_s > 0:
            time.sleep(sleep_s)
        self._next_ts = max(self._next_ts + self.period, time.time())
