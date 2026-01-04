"""
Simple IoU-based tracker for faces and plates.

This tracker implements a lightweight tracking algorithm suitable for
real-time video processing. It uses Intersection over Union (IoU) to
match detections across frames and maintains track lifecycle states.

Key features:
- Greedy IoU-based assignment (fast, no Hungarian algorithm needed)
- Per-detection-kind tracking (separate trackers for faces, plates)
- Track lifecycle: TENTATIVE → CONFIRMED → LOST
- Plate-specific: OCR text agreement for confirmation
- Configurable thresholds for matching and aging
"""

from __future__ import annotations

import logging
from typing import Optional

from ..types import Detection, DetectionKind
from .iou import compute_iou
from .types import Track, TrackState

logger = logging.getLogger(__name__)


class SimpleTracker:
    """
    Simple IoU-based tracker for a single detection kind.

    This tracker maintains a list of active tracks and matches new detections
    to existing tracks using IoU. Tracks progress through lifecycle states:

    1. TENTATIVE: Newly created, needs K consecutive matches to confirm
    2. CONFIRMED: Stable track with K+ consecutive matches
    3. LOST: Not matched for N frames, will be removed

    For plate tracking, we additionally require OCR text agreement across
    multiple frames before confirming a track. This dramatically reduces
    false positives from OCR errors.

    Args:
        detection_kind: Kind of detection to track ("face" or "plate")
        iou_threshold: Minimum IoU for matching (default: 0.5)
        frames_required: Consecutive frames required for confirmation (default: 3)
        max_age: Maximum frames without match before removal (default: 30)
        ocr_agreement_threshold: Minimum OCR agreement ratio for plates (default: 0.6)
    """

    def __init__(
        self,
        detection_kind: DetectionKind,
        iou_threshold: float = 0.5,
        frames_required: int = 3,
        max_age: int = 30,
        ocr_agreement_threshold: float = 0.6,
    ):
        self.detection_kind = detection_kind
        self.iou_threshold = iou_threshold
        self.frames_required = frames_required
        self.max_age = max_age
        self.ocr_agreement_threshold = ocr_agreement_threshold

        self.tracks: list[Track] = []
        self._next_track_id = 1
        self._stats = {
            "total_detections": 0,
            "tracks_created": 0,
            "tracks_confirmed": 0,
            "tracks_lost": 0,
        }

    def update(
        self,
        detections: list[Detection],
        ts_ms: int,
        ocr_texts: Optional[list[tuple[str, float]]] = None,
    ) -> list[Track]:
        """
        Update tracker with new detections from current frame.

        This method:
        1. Matches detections to existing tracks (greedy IoU matching)
        2. Updates matched tracks
        3. Creates new tracks for unmatched detections
        4. Ages out tracks that weren't matched
        5. Updates track states (TENTATIVE → CONFIRMED → LOST)

        For plates: Also checks OCR text agreement before confirming tracks.

        Args:
            detections: List of detections from current frame
            ts_ms: Frame timestamp (milliseconds)
            ocr_texts: Optional list of (text_clean, confidence) for plate detections
                      Must be same length as detections if provided

        Returns:
            List of all currently active tracks (TENTATIVE + CONFIRMED)
        """
        self._stats["total_detections"] += len(detections)

        # Validate OCR texts for plate tracking
        if self.detection_kind == "plate" and ocr_texts is not None:
            if len(ocr_texts) != len(detections):
                raise ValueError(
                    f"ocr_texts length ({len(ocr_texts)}) must match "
                    f"detections length ({len(detections)})"
                )

        # Step 1: Match detections to existing tracks (greedy)
        matched_track_indices: set[int] = set()
        matched_detection_indices: set[int] = set()

        # Sort tracks by state (CONFIRMED first) for better matching
        sorted_track_indices = sorted(
            range(len(self.tracks)),
            key=lambda i: (
                self.tracks[i].state != TrackState.CONFIRMED,  # CONFIRMED first
                -self.tracks[i].consecutive_hits,  # Then by consecutive hits
            ),
        )

        for track_idx in sorted_track_indices:
            track = self.tracks[track_idx]

            # Find best matching detection for this track
            best_detection_idx: Optional[int] = None
            best_iou = self.iou_threshold

            for det_idx, detection in enumerate(detections):
                if det_idx in matched_detection_indices:
                    continue

                iou = compute_iou(track.bbox, detection.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_detection_idx = det_idx

            # Update track if match found
            if best_detection_idx is not None:
                detection = detections[best_detection_idx]
                track.update(detection.bbox, detection.score, ts_ms)

                # Add OCR text for plate tracking
                if self.detection_kind == "plate" and ocr_texts is not None:
                    text_clean, ocr_conf = ocr_texts[best_detection_idx]
                    track.add_ocr_text(text_clean, ocr_conf)

                matched_track_indices.add(track_idx)
                matched_detection_indices.add(best_detection_idx)

                logger.debug(
                    f"Matched detection to track {track.track_id} (IoU={best_iou:.3f}, "
                    f"consecutive_hits={track.consecutive_hits})"
                )

        # Step 2: Mark unmatched tracks as missed
        for track_idx, track in enumerate(self.tracks):
            if track_idx not in matched_track_indices:
                track.mark_missed()

        # Step 3: Create new tracks for unmatched detections
        for det_idx, detection in enumerate(detections):
            if det_idx not in matched_detection_indices:
                track = Track(
                    track_id=self._next_track_id,
                    detection_kind=self.detection_kind,
                    bbox=detection.bbox,
                    score=detection.score,
                    state=TrackState.TENTATIVE,
                    first_seen_ts=ts_ms,
                    last_seen_ts=ts_ms,
                )

                # Add OCR text for plate tracking
                if self.detection_kind == "plate" and ocr_texts is not None:
                    text_clean, ocr_conf = ocr_texts[det_idx]
                    track.add_ocr_text(text_clean, ocr_conf)

                self.tracks.append(track)
                self._next_track_id += 1
                self._stats["tracks_created"] += 1

                logger.debug(f"Created new track {track.track_id} at {ts_ms}ms")

        # Step 4: Update track states
        self._update_track_states()

        # Step 5: Remove lost tracks
        self._prune_lost_tracks()

        return self.get_active_tracks()

    def _update_track_states(self) -> None:
        """
        Update track states based on consecutive hits/misses.

        State transitions:
        - TENTATIVE → CONFIRMED: After K consecutive hits
        - CONFIRMED → LOST: After N consecutive misses
        - TENTATIVE → LOST: After N consecutive misses

        For plates: Also checks OCR text agreement before confirming.
        """
        for track in self.tracks:
            # Check if track should be marked as LOST
            if track.is_lost(self.max_age):
                if track.state != TrackState.LOST:
                    track.state = TrackState.LOST
                    self._stats["tracks_lost"] += 1
                    logger.debug(
                        f"Track {track.track_id} lost after "
                        f"{track.consecutive_misses} consecutive misses"
                    )
                continue

            # Check if tentative track should be confirmed
            if track.state == TrackState.TENTATIVE:
                if track.is_confirmed(self.frames_required):
                    # For plates, also check OCR text agreement
                    if self.detection_kind == "plate":
                        majority_text = track.get_majority_ocr_text(self.ocr_agreement_threshold)
                        if majority_text is not None:
                            track.state = TrackState.CONFIRMED
                            self._stats["tracks_confirmed"] += 1
                            logger.info(
                                f"Track {track.track_id} confirmed: "
                                f"plate='{majority_text}', "
                                f"consecutive_hits={track.consecutive_hits}, "
                                f"ocr_agreement={self._get_ocr_agreement(track):.1%}"
                            )
                        else:
                            logger.debug(
                                f"Track {track.track_id} has {track.consecutive_hits} hits "
                                f"but insufficient OCR agreement "
                                f"({self._get_ocr_agreement(track):.1%} < "
                                f"{self.ocr_agreement_threshold:.1%})"
                            )
                    else:
                        # For faces, just check consecutive hits
                        track.state = TrackState.CONFIRMED
                        self._stats["tracks_confirmed"] += 1
                        logger.info(
                            f"Track {track.track_id} confirmed: "
                            f"consecutive_hits={track.consecutive_hits}"
                        )

    def _get_ocr_agreement(self, track: Track) -> float:
        """
        Calculate OCR agreement ratio for plate track.

        Args:
            track: Plate track

        Returns:
            Agreement ratio (0.0-1.0)
        """
        if not track.ocr_text_history:
            return 0.0

        # Count occurrences of each text
        text_counts: dict[str, int] = {}
        for text, _ in track.ocr_text_history:
            text_counts[text] = text_counts.get(text, 0) + 1

        # Get most common count
        most_common_count = max(text_counts.values())
        total_count = len(track.ocr_text_history)

        return most_common_count / total_count

    def _prune_lost_tracks(self) -> None:
        """Remove tracks in LOST state."""
        before_count = len(self.tracks)
        self.tracks = [t for t in self.tracks if t.state != TrackState.LOST]
        after_count = len(self.tracks)

        if after_count < before_count:
            logger.debug(f"Pruned {before_count - after_count} lost tracks")

    def get_active_tracks(self) -> list[Track]:
        """
        Get all active tracks (TENTATIVE + CONFIRMED).

        Returns:
            List of active tracks
        """
        return [t for t in self.tracks if t.state != TrackState.LOST]

    def get_confirmed_tracks(self) -> list[Track]:
        """
        Get only confirmed tracks.

        Returns:
            List of confirmed tracks
        """
        return [t for t in self.tracks if t.state == TrackState.CONFIRMED]

    def get_track_by_id(self, track_id: int) -> Optional[Track]:
        """
        Get track by ID.

        Args:
            track_id: Track ID to search for

        Returns:
            Track if found, else None
        """
        for track in self.tracks:
            if track.track_id == track_id:
                return track
        return None

    def get_stats(self) -> dict:
        """
        Get tracker statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            **self._stats,
            "active_tracks": len(self.get_active_tracks()),
            "confirmed_tracks": len(self.get_confirmed_tracks()),
            "tentative_tracks": len([t for t in self.tracks if t.state == TrackState.TENTATIVE]),
        }

    def reset(self) -> None:
        """Reset tracker state (useful for testing)."""
        self.tracks.clear()
        self._next_track_id = 1
        self._stats = {
            "total_detections": 0,
            "tracks_created": 0,
            "tracks_confirmed": 0,
            "tracks_lost": 0,
        }
