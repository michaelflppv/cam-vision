"""
Temporal filtering sink for event deduplication and cooldown management.

This module provides a sink wrapper that prevents duplicate event emissions
within a configurable cooldown window. This is essential for reducing alert
fatigue in production deployments.

Example scenario:
- Same person detected 20 times in 60 seconds while walking past camera
- Without temporal filter: 20 events emitted → alert fatigue
- With temporal filter (30s cooldown): 2 events emitted → manageable

Key features:
- Configurable cooldown period (default: 30 seconds)
- Per-entity tracking (person_id for faces, text_clean for plates)
- TTL-based expiration (automatic cleanup)
- Logs suppressed events for debugging
- Wraps existing sinks (decorator pattern)

Design rationale:
- Temporal filtering is a sink concern, not a processor concern
- Keeps processors stateless (as per CLAUDE.md)
- Easy to enable/disable without code changes
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from ..types import Event, FaceMatch, PlateRead
from .base import Sink

logger = logging.getLogger(__name__)


class TemporalFilterSink(Sink):
    """
    Sink wrapper that prevents duplicate event emissions within cooldown window.

    This sink wraps an existing sink (e.g., EventStoreSink) and adds temporal
    deduplication. Events for the same entity (person/plate) are only forwarded
    if the cooldown period has elapsed since the last emission.

    For faces: Deduplication by person_id
    For plates: Deduplication by text_clean (cleaned OCR text)

    Args:
        wrapped_sink: Underlying sink to forward events to
        cooldown_seconds: Cooldown period in seconds (default: 30.0)
        cleanup_interval: Seconds between TTL cleanup runs (default: 60.0)
    """

    def __init__(
        self,
        wrapped_sink: Sink,
        cooldown_seconds: float = 30.0,
        cleanup_interval: float = 60.0,
    ):
        self.wrapped_sink = wrapped_sink
        self.cooldown_seconds = cooldown_seconds
        self.cleanup_interval = cleanup_interval

        # Cache: entity_key -> last_emit_timestamp
        self._last_emit_ts: dict[str, float] = {}

        # Tracking for cleanup
        self._last_cleanup_ts = time.time()

        self._stats = {
            "events_received": 0,
            "events_forwarded": 0,
            "events_suppressed": 0,
            "cleanup_runs": 0,
        }

    def open(self) -> None:
        """Open wrapped sink."""
        logger.info(
            f"Opening TemporalFilterSink: cooldown={self.cooldown_seconds}s, "
            f"cleanup_interval={self.cleanup_interval}s"
        )
        self.wrapped_sink.open()

    def consume(self, event: Event) -> None:
        """
        Consume event with temporal filtering.

        This method:
        1. Extracts entity key from event (person_id or text_clean)
        2. Checks if cooldown period has elapsed since last emission
        3. Forwards event to wrapped sink if cooldown elapsed
        4. Updates last emission timestamp
        5. Logs suppressed events for debugging

        Args:
            event: Event to consume
        """
        self._stats["events_received"] += 1

        # Extract entity key
        entity_key = self._get_entity_key(event)

        # Check if we should emit
        current_ts = time.time()
        last_emit_ts = self._last_emit_ts.get(entity_key)

        should_emit = True
        time_since_last_emit: Optional[float] = None

        if last_emit_ts is not None:
            time_since_last_emit = current_ts - last_emit_ts
            if time_since_last_emit < self.cooldown_seconds:
                should_emit = False

        if should_emit:
            # Forward to wrapped sink
            self.wrapped_sink.consume(event)

            # Update cache
            self._last_emit_ts[entity_key] = current_ts
            self._stats["events_forwarded"] += 1

            if last_emit_ts is not None:
                logger.debug(
                    f"Event forwarded: {entity_key} "
                    f"(time_since_last={time_since_last_emit:.1f}s, "
                    f"cooldown={self.cooldown_seconds}s)"
                )
        else:
            # Suppress duplicate
            self._stats["events_suppressed"] += 1
            logger.debug(
                f"Event suppressed: {entity_key} "
                f"(time_since_last={time_since_last_emit:.1f}s < "
                f"cooldown={self.cooldown_seconds}s)"
            )

        # Periodic cleanup of old entries
        if current_ts - self._last_cleanup_ts > self.cleanup_interval:
            self._cleanup_expired_entries(current_ts)

    def _get_entity_key(self, event: Event) -> str:
        """
        Extract entity key from event for deduplication.

        For faces: person_id
        For plates: text_clean

        Args:
            event: Event to extract key from

        Returns:
            Entity key string
        """
        if event.type == "face_match":
            face_match: FaceMatch = event.payload
            return f"face:{face_match.person_id}"
        elif event.type == "plate_read":
            plate_read: PlateRead = event.payload
            return f"plate:{plate_read.text_clean}"
        else:
            # Unknown event type - use type as key (will not deduplicate)
            logger.warning(f"Unknown event type for deduplication: {event.type}")
            return f"unknown:{event.type}:{event.ts_ms}"

    def _cleanup_expired_entries(self, current_ts: float) -> None:
        """
        Remove expired entries from cache.

        Entries are expired if they're older than cooldown period + safety margin.
        This prevents unbounded memory growth.

        Args:
            current_ts: Current timestamp
        """
        expiry_threshold = current_ts - (self.cooldown_seconds * 2)  # 2x safety margin

        before_count = len(self._last_emit_ts)
        self._last_emit_ts = {
            key: ts for key, ts in self._last_emit_ts.items() if ts > expiry_threshold
        }
        after_count = len(self._last_emit_ts)

        self._last_cleanup_ts = current_ts
        self._stats["cleanup_runs"] += 1

        if after_count < before_count:
            logger.debug(
                f"Cleaned up {before_count - after_count} expired cache entries "
                f"(remaining={after_count})"
            )

    def close(self) -> None:
        """Close wrapped sink and log statistics."""
        logger.info(f"Closing TemporalFilterSink: {self._format_stats()}")
        self.wrapped_sink.close()

    def _format_stats(self) -> str:
        """Format statistics as human-readable string."""
        stats = self._stats
        received = stats["events_received"]
        forwarded = stats["events_forwarded"]
        suppressed = stats["events_suppressed"]

        suppression_pct = 0.0
        if received > 0:
            suppression_pct = 100.0 * suppressed / received

        return (
            f"events_received={received}, "
            f"events_forwarded={forwarded}, "
            f"events_suppressed={suppressed} ({suppression_pct:.1f}%), "
            f"cleanup_runs={stats['cleanup_runs']}, "
            f"cache_size={len(self._last_emit_ts)}"
        )

    def get_stats(self) -> dict:
        """Get sink statistics."""
        return {
            **self._stats,
            "cache_size": len(self._last_emit_ts),
            "wrapped_sink": (
                self.wrapped_sink.get_stats() if hasattr(self.wrapped_sink, "get_stats") else {}
            ),
        }

    def force_cleanup(self) -> None:
        """
        Force immediate cleanup of expired entries.

        Useful for testing or manual memory management.
        """
        current_ts = time.time()
        self._cleanup_expired_entries(current_ts)
