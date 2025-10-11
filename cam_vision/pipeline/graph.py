from __future__ import annotations

from typing import List

from .base import FrameSource, Processor, Sink


class GraphRunner:
    """
    Minimal synchronous graph runner:
      FrameSource -> [Processors...] -> Sinks
    """

    def __init__(self, source: FrameSource, processors: List[Processor], sinks: List[Sink]):
        self.source = source
        self.processors = processors
        self.sinks = sinks
        self._opened = False

    def open(self) -> None:
        if self._opened:
            return
        self.source.open()
        for p in self.processors:
            p.open()
        for s in self.sinks:
            s.open()
        self._opened = True

    def run_once(self) -> bool:
        """
        Process a single frame through the graph.
        Returns False if there was no frame (e.g., timeout/end). True otherwise.
        """
        frame = self.source.read()
        if frame is None:
            return False

        for p in self.processors:
            for event in p.process_frame(frame):
                for s in self.sinks:
                    s.consume(event)
        return True

    def close(self) -> None:
        if not self._opened:
            return
        try:
            for p in self.processors:
                p.close()
        finally:
            try:
                for s in self.sinks:
                    s.close()
            finally:
                self.source.close()
                self._opened = False
