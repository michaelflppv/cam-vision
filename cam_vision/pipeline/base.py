from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..types import Event, Frame


class Processor(ABC):
    """A processing stage that consumes frames and yields zero or more events."""

    @abstractmethod
    def open(self) -> None:
        """Allocate resources."""
        raise NotImplementedError

    @abstractmethod
    def process_frame(self, frame: Frame) -> Iterable[Event]:
        """Process a single frame and return zero or more events."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Release resources."""
        raise NotImplementedError


class Sink(ABC):
    """A sink that consumes events (e.g., DB, API, WS)."""

    @abstractmethod
    def open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def consume(self, event: Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class FrameSource(ABC):
    """Abstract frame source. Concrete implementation will arrive in PR3."""

    @abstractmethod
    def open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> Optional[Frame]:
        """Return next frame or None if stream ended (or on timeout)."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
