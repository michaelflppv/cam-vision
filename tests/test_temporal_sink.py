"""Tests for TemporalFilterSink."""

import time
from unittest.mock import Mock

import pytest

from cam_vision.pipeline.temporal_sink import TemporalFilterSink
from cam_vision.types import BBox, Detection, Event, FaceMatch, PlateRead


@pytest.fixture
def mock_sink():
    """Create mock wrapped sink."""
    sink = Mock()
    sink.get_stats.return_value = {}
    return sink


@pytest.fixture
def temporal_sink(mock_sink):
    """Create temporal filter sink with short cooldown for testing."""
    return TemporalFilterSink(
        wrapped_sink=mock_sink,
        cooldown_seconds=1.0,  # Short cooldown for testing
        cleanup_interval=5.0,
    )


@pytest.fixture
def sample_face_event():
    """Create sample face match event."""
    return Event(
        type="face_match",
        payload=FaceMatch(
            person_id="john_doe",
            similarity=0.87,
            detection=Detection(
                kind="face",
                bbox=BBox(x1=100, y1=150, x2=300, y2=350),
                score=0.95,
            ),
        ),
        ts_ms=1234567890000,
        frame_source_id="camera_1",
    )


@pytest.fixture
def sample_plate_event():
    """Create sample plate read event."""
    return Event(
        type="plate_read",
        payload=PlateRead(
            text_raw=" ABC 123 ",
            text_clean="ABC123",
            confidence=85.5,
            detection=Detection(
                kind="plate",
                bbox=BBox(x1=200, y1=400, x2=500, y2=500),
                score=0.88,
            ),
            matched_list="whitelist",
            preprocessing_used="grayscale,bilateral",
        ),
        ts_ms=1234567891000,
        frame_source_id="camera_1",
    )


class TestTemporalFilterSinkBasics:
    """Basic temporal filter sink tests."""

    def test_initialization(self, temporal_sink, mock_sink):
        """Test sink initializes correctly."""
        assert temporal_sink.wrapped_sink == mock_sink
        assert temporal_sink.cooldown_seconds == 1.0
        assert len(temporal_sink._last_emit_ts) == 0

    def test_open_calls_wrapped_sink(self, temporal_sink, mock_sink):
        """Test open() calls wrapped sink."""
        temporal_sink.open()
        mock_sink.open.assert_called_once()

    def test_close_calls_wrapped_sink(self, temporal_sink, mock_sink):
        """Test close() calls wrapped sink."""
        temporal_sink.close()
        mock_sink.close.assert_called_once()

    def test_first_event_always_forwarded(self, temporal_sink, mock_sink, sample_face_event):
        """Test first event for an entity is always forwarded."""
        temporal_sink.consume(sample_face_event)

        mock_sink.consume.assert_called_once_with(sample_face_event)
        assert temporal_sink._stats["events_received"] == 1
        assert temporal_sink._stats["events_forwarded"] == 1
        assert temporal_sink._stats["events_suppressed"] == 0


class TestFaceEventFiltering:
    """Test face event filtering."""

    def test_duplicate_face_within_cooldown_suppressed(
        self, temporal_sink, mock_sink, sample_face_event
    ):
        """Test duplicate face event within cooldown is suppressed."""
        # First event: forwarded
        temporal_sink.consume(sample_face_event)
        assert mock_sink.consume.call_count == 1

        # Second event immediately after: suppressed
        temporal_sink.consume(sample_face_event)
        assert mock_sink.consume.call_count == 1  # Still 1
        assert temporal_sink._stats["events_suppressed"] == 1

    def test_duplicate_face_after_cooldown_forwarded(
        self, temporal_sink, mock_sink, sample_face_event
    ):
        """Test duplicate face event after cooldown is forwarded."""
        # First event
        temporal_sink.consume(sample_face_event)
        assert mock_sink.consume.call_count == 1

        # Wait for cooldown
        time.sleep(1.1)

        # Second event after cooldown: forwarded
        temporal_sink.consume(sample_face_event)
        assert mock_sink.consume.call_count == 2
        assert temporal_sink._stats["events_suppressed"] == 0

    def test_different_faces_both_forwarded(self, temporal_sink, mock_sink):
        """Test events for different faces are both forwarded."""
        event1 = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="john_doe",
                similarity=0.87,
                detection=Detection(
                    kind="face", bbox=BBox(x1=100, y1=100, x2=200, y2=200), score=0.95
                ),
            ),
            ts_ms=1000,
            frame_source_id="camera_1",
        )

        event2 = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="jane_smith",
                similarity=0.92,
                detection=Detection(
                    kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.98
                ),
            ),
            ts_ms=1100,
            frame_source_id="camera_1",
        )

        temporal_sink.consume(event1)
        temporal_sink.consume(event2)

        assert mock_sink.consume.call_count == 2
        assert temporal_sink._stats["events_forwarded"] == 2


class TestPlateEventFiltering:
    """Test plate event filtering."""

    def test_duplicate_plate_within_cooldown_suppressed(
        self, temporal_sink, mock_sink, sample_plate_event
    ):
        """Test duplicate plate event within cooldown is suppressed."""
        # First event: forwarded
        temporal_sink.consume(sample_plate_event)
        assert mock_sink.consume.call_count == 1

        # Second event immediately after: suppressed
        temporal_sink.consume(sample_plate_event)
        assert mock_sink.consume.call_count == 1  # Still 1
        assert temporal_sink._stats["events_suppressed"] == 1

    def test_duplicate_plate_after_cooldown_forwarded(
        self, temporal_sink, mock_sink, sample_plate_event
    ):
        """Test duplicate plate event after cooldown is forwarded."""
        # First event
        temporal_sink.consume(sample_plate_event)
        assert mock_sink.consume.call_count == 1

        # Wait for cooldown
        time.sleep(1.1)

        # Second event after cooldown: forwarded
        temporal_sink.consume(sample_plate_event)
        assert mock_sink.consume.call_count == 2

    def test_different_plates_both_forwarded(self, temporal_sink, mock_sink):
        """Test events for different plates are both forwarded."""
        event1 = Event(
            type="plate_read",
            payload=PlateRead(
                text_raw="ABC123",
                text_clean="ABC123",
                confidence=85.0,
                detection=Detection(
                    kind="plate", bbox=BBox(x1=100, y1=100, x2=200, y2=150), score=0.9
                ),
            ),
            ts_ms=1000,
            frame_source_id="camera_1",
        )

        event2 = Event(
            type="plate_read",
            payload=PlateRead(
                text_raw="XYZ789",
                text_clean="XYZ789",
                confidence=88.0,
                detection=Detection(
                    kind="plate", bbox=BBox(x1=300, y1=300, x2=400, y2=350), score=0.92
                ),
            ),
            ts_ms=1100,
            frame_source_id="camera_1",
        )

        temporal_sink.consume(event1)
        temporal_sink.consume(event2)

        assert mock_sink.consume.call_count == 2


class TestCacheManagement:
    """Test cache cleanup and management."""

    def test_cleanup_removes_expired_entries(self, temporal_sink, mock_sink, sample_face_event):
        """Test cleanup removes expired entries."""
        # Add event
        temporal_sink.consume(sample_face_event)
        assert len(temporal_sink._last_emit_ts) == 1

        # Manually set timestamp to be old
        entity_key = f"face:{sample_face_event.payload.person_id}"
        temporal_sink._last_emit_ts[entity_key] = time.time() - 100  # 100 seconds ago

        # Force cleanup
        temporal_sink.force_cleanup()

        # Should be removed (older than 2x cooldown)
        assert len(temporal_sink._last_emit_ts) == 0

    def test_cleanup_keeps_recent_entries(self, temporal_sink, mock_sink, sample_face_event):
        """Test cleanup keeps recent entries."""
        # Add event
        temporal_sink.consume(sample_face_event)
        assert len(temporal_sink._last_emit_ts) == 1

        # Force cleanup (entry is recent)
        temporal_sink.force_cleanup()

        # Should still be there
        assert len(temporal_sink._last_emit_ts) == 1

    def test_cleanup_runs_automatically(self, temporal_sink, mock_sink, sample_face_event):
        """Test cleanup runs automatically after interval."""
        # Add event
        temporal_sink.consume(sample_face_event)

        # Manually trigger cleanup by setting last cleanup time to old
        temporal_sink._last_cleanup_ts = time.time() - 10  # 10 seconds ago

        # Consume another event (should trigger cleanup)
        event2 = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="jane_smith",
                similarity=0.92,
                detection=Detection(
                    kind="face", bbox=BBox(x1=300, y1=300, x2=400, y2=400), score=0.98
                ),
            ),
            ts_ms=2000,
            frame_source_id="camera_1",
        )
        temporal_sink.consume(event2)

        # Cleanup should have run
        assert temporal_sink._stats["cleanup_runs"] >= 1


class TestStatistics:
    """Test statistics tracking."""

    def test_stats_track_received_events(self, temporal_sink, mock_sink, sample_face_event):
        """Test stats correctly track received events."""
        temporal_sink.consume(sample_face_event)
        temporal_sink.consume(sample_face_event)
        temporal_sink.consume(sample_face_event)

        stats = temporal_sink.get_stats()
        assert stats["events_received"] == 3

    def test_stats_track_forwarded_events(
        self, temporal_sink, mock_sink, sample_face_event, sample_plate_event
    ):
        """Test stats correctly track forwarded events."""
        temporal_sink.consume(sample_face_event)
        temporal_sink.consume(sample_plate_event)

        stats = temporal_sink.get_stats()
        assert stats["events_forwarded"] == 2

    def test_stats_track_suppressed_events(self, temporal_sink, mock_sink, sample_face_event):
        """Test stats correctly track suppressed events."""
        temporal_sink.consume(sample_face_event)
        temporal_sink.consume(sample_face_event)  # Suppressed
        temporal_sink.consume(sample_face_event)  # Suppressed

        stats = temporal_sink.get_stats()
        assert stats["events_suppressed"] == 2

    def test_stats_include_cache_size(self, temporal_sink, mock_sink):
        """Test stats include cache size."""
        event1 = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="person1",
                similarity=0.9,
                detection=Detection(kind="face", bbox=BBox(x1=0, y1=0, x2=100, y2=100), score=0.9),
            ),
            ts_ms=1000,
            frame_source_id="camera_1",
        )

        event2 = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="person2",
                similarity=0.9,
                detection=Detection(
                    kind="face", bbox=BBox(x1=200, y1=200, x2=300, y2=300), score=0.9
                ),
            ),
            ts_ms=1100,
            frame_source_id="camera_1",
        )

        temporal_sink.consume(event1)
        temporal_sink.consume(event2)

        stats = temporal_sink.get_stats()
        assert stats["cache_size"] == 2


class TestEdgeCases:
    """Test edge cases."""

    def test_unknown_event_type_handled(self, temporal_sink, mock_sink):
        """Test unknown event types are handled gracefully."""
        # Create event with unknown type
        unknown_event = Event(
            type="unknown_type",
            payload=None,
            ts_ms=1000,
            frame_source_id="camera_1",
        )

        # Should not crash
        temporal_sink.consume(unknown_event)

        # Should be forwarded (can't deduplicate unknown types)
        assert mock_sink.consume.call_count == 1

    def test_multiple_events_same_person_different_timing(
        self, temporal_sink, mock_sink, sample_face_event
    ):
        """Test multiple events for same person with different timing."""
        # Event 1: forwarded
        temporal_sink.consume(sample_face_event)

        # Event 2: suppressed (within cooldown)
        temporal_sink.consume(sample_face_event)

        # Wait for cooldown
        time.sleep(1.1)

        # Event 3: forwarded (after cooldown)
        temporal_sink.consume(sample_face_event)

        # Event 4: suppressed (within cooldown again)
        temporal_sink.consume(sample_face_event)

        assert mock_sink.consume.call_count == 2
        assert temporal_sink._stats["events_suppressed"] == 2
