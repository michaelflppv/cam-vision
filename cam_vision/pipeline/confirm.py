"""
Multi-frame confirmation processor for reducing false positives.

This module provides a wrapper processor that adds multi-frame confirmation
logic to existing processors (FaceRecognizer, PlateRecognizer). It ensures
that events are only emitted after K consecutive frame detections, dramatically
reducing false positives from single-frame errors.

Key features:
- Wraps existing processors (decorator pattern)
- Maintains tracker per detection kind
- Only emits events for CONFIRMED tracks
- Enriches events with track_id
- Configurable confirmation thresholds

Design rationale:
- Processors remain stateless (as per CLAUDE.md)
- Tracking logic is isolated in this wrapper
- Easy to enable/disable confirmation without code changes
"""

from __future__ import annotations

import logging
from typing import Iterable

from ..tracking.tracker import SimpleTracker
from ..types import Detection, DetectionKind, Event, FaceMatch, PlateRead
from .base import Processor

logger = logging.getLogger(__name__)


class ConfirmationProcessor(Processor):
    """
    Wrapper processor that adds multi-frame confirmation logic.

    This processor wraps an existing processor (e.g., FaceRecognizer or
    PlateRecognizer) and adds tracking-based confirmation. Events are only
    emitted after a track has been confirmed (K consecutive frame matches).

    For face tracking: Confirmation based on bbox IoU only.
    For plate tracking: Confirmation requires both bbox IoU AND OCR text agreement.

    The wrapped processor operates normally and emits events immediately, but
    this wrapper intercepts those events and only forwards confirmed ones.

    Args:
        wrapped_processor: Underlying processor (FaceRecognizer or PlateRecognizer)
        detection_kind: Kind of detection ("face" or "plate")
        frames_required: Consecutive frames required for confirmation (default: 3)
        iou_threshold: Minimum IoU for track matching (default: 0.5)
        max_age: Maximum frames without match before track removal (default: 30)
        ocr_agreement_threshold: Minimum OCR agreement ratio for plates (default: 0.6)
    """

    def __init__(
        self,
        wrapped_processor: Processor,
        detection_kind: DetectionKind,
        frames_required: int = 3,
        iou_threshold: float = 0.5,
        max_age: int = 30,
        ocr_agreement_threshold: float = 0.6,
    ):
        self.wrapped_processor = wrapped_processor
        self.detection_kind = detection_kind
        self.frames_required = frames_required

        # Create tracker for this detection kind
        self.tracker = SimpleTracker(
            detection_kind=detection_kind,
            iou_threshold=iou_threshold,
            frames_required=frames_required,
            max_age=max_age,
            ocr_agreement_threshold=ocr_agreement_threshold,
        )

        # Track which events we've already emitted to avoid duplicates
        self._emitted_track_ids: set[int] = set()

        self._stats = {
            "frames_processed": 0,
            "events_from_wrapped": 0,
            "events_buffered": 0,
            "events_emitted": 0,
        }

    def open(self) -> None:
        """Open wrapped processor."""
        logger.info(
            f"Opening ConfirmationProcessor: kind={self.detection_kind}, "
            f"frames_required={self.frames_required}, "
            f"iou_threshold={self.tracker.iou_threshold}"
        )
        self.wrapped_processor.open()

    def process_frame(self, frame) -> Iterable[Event]:
        """
        Process frame with multi-frame confirmation.

        This method:
        1. Calls wrapped processor to get initial events
        2. Extracts detections from events
        3. Updates tracker with detections
        4. Only emits events for CONFIRMED tracks
        5. Enriches events with track_id

        Args:
            frame: Input frame

        Yields:
            Event objects (only for confirmed tracks)
        """
        self._stats["frames_processed"] += 1

        # Step 1: Get events from wrapped processor
        events = list(self.wrapped_processor.process_frame(frame))
        self._stats["events_from_wrapped"] += len(events)

        if not events:
            # Still need to update tracker for aging out old tracks
            self.tracker.update([], frame.ts_ms)
            return

        # Step 2: Extract detections and OCR texts (for plates)
        detections: list[Detection] = []
        ocr_texts: list[tuple[str, float]] = [] if self.detection_kind == "plate" else None

        for event in events:
            if self.detection_kind == "face":
                face_match: FaceMatch = event.payload
                detections.append(face_match.detection)
            elif self.detection_kind == "plate":
                plate_read: PlateRead = event.payload
                detections.append(plate_read.detection)
                ocr_texts.append((plate_read.text_clean, plate_read.confidence))

        # Step 3: Update tracker
        self.tracker.update(detections, frame.ts_ms, ocr_texts)

        # Step 4: Get confirmed tracks
        confirmed_tracks = self.tracker.get_confirmed_tracks()

        # Step 5: Match original events to confirmed tracks and emit
        for event in events:
            # Extract detection from event
            if self.detection_kind == "face":
                detection = event.payload.detection
            else:
                detection = event.payload.detection

            # Find matching confirmed track
            matched_track = None
            for track in confirmed_tracks:
                # Check if track was just confirmed and hasn't been emitted yet
                if track.track_id in self._emitted_track_ids:
                    continue

                # Match by bbox (tracks update bbox each frame, so check IoU)
                from ..tracking.iou import compute_iou

                iou = compute_iou(track.bbox, detection.bbox)
                if iou > self.tracker.iou_threshold:
                    matched_track = track
                    break

            if matched_track:
                # Enrich event with track_id
                enriched_event = self._enrich_event_with_track_id(event, matched_track.track_id)

                # Mark as emitted
                self._emitted_track_ids.add(matched_track.track_id)
                self._stats["events_emitted"] += 1

                logger.debug(
                    f"Emitting confirmed event: track_id={matched_track.track_id}, "
                    f"consecutive_hits={matched_track.consecutive_hits}, "
                    f"type={event.type}"
                )

                yield enriched_event
            else:
                # Event is buffered (track not yet confirmed)
                self._stats["events_buffered"] += 1

        # Cleanup emitted track IDs for tracks that no longer exist
        active_track_ids = {t.track_id for t in self.tracker.get_active_tracks()}
        self._emitted_track_ids = self._emitted_track_ids.intersection(active_track_ids)

    def _enrich_event_with_track_id(self, event: Event, track_id: int) -> Event:
        """
        Enrich event with track_id.

        Args:
            event: Original event
            track_id: Track ID to add

        Returns:
            New event with track_id in detection
        """
        # Create new detection with track_id
        if event.type == "face_match":
            face_match: FaceMatch = event.payload
            enriched_detection = Detection(
                kind=face_match.detection.kind,
                bbox=face_match.detection.bbox,
                score=face_match.detection.score,
                track_id=track_id,
            )
            enriched_payload = FaceMatch(
                person_id=face_match.person_id,
                similarity=face_match.similarity,
                detection=enriched_detection,
            )
        elif event.type == "plate_read":
            plate_read: PlateRead = event.payload
            enriched_detection = Detection(
                kind=plate_read.detection.kind,
                bbox=plate_read.detection.bbox,
                score=plate_read.detection.score,
                track_id=track_id,
            )
            enriched_payload = PlateRead(
                text_raw=plate_read.text_raw,
                text_clean=plate_read.text_clean,
                confidence=plate_read.confidence,
                detection=enriched_detection,
                matched_list=plate_read.matched_list,
                preprocessing_used=plate_read.preprocessing_used,
            )
        else:
            raise ValueError(f"Unknown event type: {event.type}")

        return Event(
            type=event.type,
            payload=enriched_payload,
            ts_ms=event.ts_ms,
            frame_source_id=event.frame_source_id,
        )

    def close(self) -> None:
        """Close wrapped processor and log statistics."""
        logger.info(
            f"Closing ConfirmationProcessor: {self.detection_kind}, "
            f"stats={self._format_stats()}"
        )
        self.wrapped_processor.close()

    def get_latest_observations(self) -> list:
        """Expose latest observations if wrapped processor provides them."""
        if hasattr(self.wrapped_processor, "get_latest_observations"):
            try:
                return self.wrapped_processor.get_latest_observations()  # type: ignore[attr-defined]
            except Exception as exc:
                logger.error(
                    "Failed to retrieve latest observations from wrapped processor: %s", exc
                )
        return []

    def _format_stats(self) -> str:
        """Format statistics as human-readable string."""
        stats = self._stats
        tracker_stats = self.tracker.get_stats()

        frames = stats["frames_processed"]
        events_in = stats["events_from_wrapped"]
        events_out = stats["events_emitted"]
        buffered = stats["events_buffered"]

        reduction_pct = 0.0
        if events_in > 0:
            reduction_pct = 100.0 * (1 - events_out / events_in)

        return (
            f"frames={frames}, "
            f"events_in={events_in}, events_out={events_out}, "
            f"buffered={buffered}, reduction={reduction_pct:.1f}%, "
            f"tracks_created={tracker_stats['tracks_created']}, "
            f"tracks_confirmed={tracker_stats['tracks_confirmed']}"
        )

    def get_stats(self) -> dict:
        """Get processor statistics."""
        return {
            **self._stats,
            "tracker": self.tracker.get_stats(),
            "wrapped_processor": (
                self.wrapped_processor.get_stats()
                if hasattr(self.wrapped_processor, "get_stats")
                else {}
            ),
        }
