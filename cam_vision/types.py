from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


@dataclass(frozen=True)
class FaceObservation:
    """Face detection observation for UI overlays."""

    detection: "Detection"
    person_id: Optional[str] = None
    similarity: Optional[float] = None
    matched: bool = False

    @property
    def label(self) -> str:
        """Human-readable label for overlays."""
        if self.matched and self.person_id:
            if self.similarity is not None:
                return f"{self.person_id} ({self.similarity:.2f})"
            return self.person_id
        return "Unknown face"


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
    """License plate recognition result."""

    text_raw: str  # Raw OCR output before cleaning
    text_clean: str  # Cleaned text (uppercase, regex, substitutions)
    confidence: float  # OCR confidence proxy (0.0-100.0)
    detection: Detection  # YOLO detection (bbox, score)
    matched_list: Optional[Literal["whitelist", "blacklist"]] = None
    preprocessing_used: str = ""  # e.g., "grayscale,bilateral" for debugging


PlateObservationStatus = Literal[
    "candidate",
    "read",
    "ocr_low_confidence",
    "ocr_short_text",
    "ocr_error",
    "rejected_aspect_ratio",
    "rejected_size",
]


@dataclass(frozen=True)
class PlateObservation:
    """Plate detection observation for UI overlays and diagnostics."""

    detection: Detection
    text_raw: str = ""
    text_clean: str = ""
    confidence: float = 0.0
    matched_list: Optional[Literal["whitelist", "blacklist"]] = None
    status: PlateObservationStatus = "candidate"
    reason: Optional[str] = None
    preprocessing_used: str = ""

    @property
    def label(self) -> str:
        """Human-readable label for overlays."""
        if self.text_clean:
            label = self.text_clean
        elif self.text_raw:
            label = self.text_raw
        else:
            label = "Plate"

        if self.status == "ocr_low_confidence":
            return f"{label} (?)"
        if self.status == "ocr_short_text":
            return f"{label} (short)"
        if self.status == "ocr_error":
            return f"{label} (error)"
        return label

    def is_rejected(self) -> bool:
        """Return True if the observation was rejected before display."""
        return self.status in {"rejected_aspect_ratio", "rejected_size"}

    def is_displayable(self) -> bool:
        """Return True if the observation should be rendered on preview overlays."""
        return not self.is_rejected()


@dataclass(frozen=True)
class Event:
    """Unified event emitted by pipelines."""

    type: Literal["face_match", "plate_read"]
    payload: FaceMatch | PlateRead
    ts_ms: int
    frame_source_id: str
