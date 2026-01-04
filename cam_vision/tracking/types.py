"""Type definitions for tracking module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ..types import BBox, DetectionKind


class TrackState(Enum):
    """
    Track lifecycle states.

    TENTATIVE: Recently created, not yet confirmed (< K consecutive detections)
    CONFIRMED: Stable track with K+ consecutive detections
    LOST: Track not matched for N+ frames, scheduled for removal
    """

    TENTATIVE = "tentative"
    CONFIRMED = "confirmed"
    LOST = "lost"


@dataclass
class Track:
    """
    A track represents a detected object tracked across multiple frames.

    For faces: Tracks are matched by bbox IoU only.
    For plates: Tracks require both bbox IoU AND OCR text agreement.

    Attributes:
        track_id: Unique track identifier
        detection_kind: Type of detection ("face" or "plate")
        bbox: Current bounding box (updated each frame)
        score: Detection confidence score (updated each frame)
        state: Current lifecycle state
        first_seen_ts: Timestamp of first detection (ms)
        last_seen_ts: Timestamp of most recent detection (ms)
        consecutive_hits: Number of consecutive frames matched
        consecutive_misses: Number of consecutive frames not matched
        total_hits: Total number of times matched (for debugging)

        # Plate-specific fields
        ocr_text_history: List of (text_clean, confidence) tuples for OCR agreement
    """

    track_id: int
    detection_kind: DetectionKind
    bbox: BBox
    score: float
    state: TrackState = TrackState.TENTATIVE
    first_seen_ts: int = 0
    last_seen_ts: int = 0
    consecutive_hits: int = 1
    consecutive_misses: int = 0
    total_hits: int = 1

    # Plate-specific tracking
    ocr_text_history: list[tuple[str, float]] = field(default_factory=list)

    def update(self, bbox: BBox, score: float, ts_ms: int) -> None:
        """
        Update track with new detection.

        Args:
            bbox: New bounding box
            score: New detection score
            ts_ms: Timestamp of detection
        """
        self.bbox = bbox
        self.score = score
        self.last_seen_ts = ts_ms
        self.consecutive_hits += 1
        self.consecutive_misses = 0
        self.total_hits += 1

    def mark_missed(self) -> None:
        """Mark track as not matched in current frame."""
        self.consecutive_hits = 0
        self.consecutive_misses += 1

    def add_ocr_text(self, text_clean: str, confidence: float, max_history: int = 10) -> None:
        """
        Add OCR text to history for plate tracking.

        Args:
            text_clean: Cleaned OCR text
            confidence: OCR confidence (0-100)
            max_history: Maximum history length (older entries removed)
        """
        self.ocr_text_history.append((text_clean, confidence))

        # Keep only most recent entries
        if len(self.ocr_text_history) > max_history:
            self.ocr_text_history = self.ocr_text_history[-max_history:]

    def get_majority_ocr_text(self, min_agreement: float = 0.6) -> Optional[str]:
        """
        Get majority OCR text from history.

        For plate tracking, we require OCR text agreement across multiple frames
        to confirm a track. This reduces false positives from OCR errors.

        Args:
            min_agreement: Minimum fraction of history that must agree (0.0-1.0)

        Returns:
            Most common text if agreement threshold met, else None
        """
        if not self.ocr_text_history:
            return None

        # Count occurrences of each text
        text_counts: dict[str, int] = {}
        for text, _ in self.ocr_text_history:
            text_counts[text] = text_counts.get(text, 0) + 1

        # Find most common text
        most_common_text = max(text_counts, key=text_counts.get)
        most_common_count = text_counts[most_common_text]

        # Check if agreement threshold met
        total_count = len(self.ocr_text_history)
        agreement_ratio = most_common_count / total_count

        if agreement_ratio >= min_agreement:
            return most_common_text

        return None

    def is_confirmed(self, frames_required: int) -> bool:
        """
        Check if track has enough consecutive hits to be confirmed.

        Args:
            frames_required: Number of consecutive frames required (K)

        Returns:
            True if track is confirmed
        """
        return self.consecutive_hits >= frames_required

    def is_lost(self, max_age: int) -> bool:
        """
        Check if track has been missed too many times and should be removed.

        Args:
            max_age: Maximum consecutive misses before removal

        Returns:
            True if track should be removed
        """
        return self.consecutive_misses >= max_age

    def age_ms(self, current_ts: int) -> int:
        """
        Get track age in milliseconds.

        Args:
            current_ts: Current timestamp (ms)

        Returns:
            Age in milliseconds since first detection
        """
        return current_ts - self.first_seen_ts
