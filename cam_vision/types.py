from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass(frozen=True)
class Frame:
    """Raw frame container used by the pipeline."""

    image: Any  # numpy ndarray (H,W,C) BGR in PR3
    ts_ms: int
    source_id: str


@dataclass(frozen=True)
class BBox:
    """Axis-aligned bounding box."""

    x1: int
    y1: int
    x2: int
    y2: int

    def width(self) -> int:
        return max(0, self.x2 - self.x1)

    def height(self) -> int:
        return max(0, self.y2 - self.y1)

    def area(self) -> int:
        return self.width() * self.height()


DetectionKind = Literal["face", "plate", "vehicle"]


@dataclass(frozen=True)
class Detection:
    kind: DetectionKind
    bbox: BBox
    score: float
    track_id: Optional[int] = None


@dataclass(frozen=True)
class FaceMatch:
    person_id: str
    similarity: float
    detection: Detection


@dataclass(frozen=True)
class PlateRead:
    text: str
    confidence: float
    detection: Detection


@dataclass(frozen=True)
class Event:
    """Unified event emitted by pipelines."""

    type: Literal["face_match", "plate_read"]
    payload: FaceMatch | PlateRead
    ts_ms: int
    frame_source_id: str
