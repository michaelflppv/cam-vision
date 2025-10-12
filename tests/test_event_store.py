"""Tests for event storage (SQLite backend)."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cam_vision.events.store import EventStore
from cam_vision.types import BBox, Detection, Event, FaceMatch, PlateRead


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_events.db"
        db_url = f"sqlite:///{db_path}"
        yield db_url


@pytest.fixture
def event_store(temp_db):
    """Create EventStore instance with temporary database."""
    return EventStore(db_url=temp_db, retention_days=30)


@pytest.fixture
def sample_face_event():
    """Create a sample face match event."""
    return Event(
        type="face_match",
        payload=FaceMatch(
            person_id="john_doe",
            similarity=0.87,
            detection=Detection(
                kind="face",
                bbox=BBox(x1=100, y1=150, x2=300, y2=350),
                score=0.95,
                track_id=42,
            ),
        ),
        ts_ms=1234567890000,
        frame_source_id="camera_1",
    )


@pytest.fixture
def sample_plate_event():
    """Create a sample plate read event."""
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
                track_id=None,
            ),
            matched_list="whitelist",
            preprocessing_used="grayscale,bilateral",
        ),
        ts_ms=1234567891000,
        frame_source_id="camera_1",
    )


class TestEventStore:
    """Test suite for EventStore."""

    def test_save_face_match_event(self, event_store, sample_face_event):
        """Test saving a face match event."""
        event_id = event_store.save_event(sample_face_event)

        assert event_id > 0

        # Retrieve and verify
        event_dict = event_store.get_face_match(event_id)
        assert event_dict is not None
        assert event_dict["type"] == "face_match"
        assert event_dict["ts_ms"] == 1234567890000
        assert event_dict["frame_source_id"] == "camera_1"

        payload = event_dict["payload"]
        assert payload["person_id"] == "john_doe"
        assert payload["similarity"] == 0.87
        assert payload["detection_score"] == 0.95
        assert payload["track_id"] == 42
        assert payload["bbox"] == {"x1": 100, "y1": 150, "x2": 300, "y2": 350}

    def test_save_plate_read_event(self, event_store, sample_plate_event):
        """Test saving a plate read event."""
        event_id = event_store.save_event(sample_plate_event)

        assert event_id > 0

        # Retrieve and verify
        event_dict = event_store.get_plate_read(event_id)
        assert event_dict is not None
        assert event_dict["type"] == "plate_read"

        payload = event_dict["payload"]
        assert payload["text_raw"] == " ABC 123 "
        assert payload["text_clean"] == "ABC123"
        assert payload["ocr_confidence"] == 85.5
        assert payload["detector_score"] == 0.88
        assert payload["matched_list"] == "whitelist"
        assert payload["preprocessing_used"] == "grayscale,bilateral"
        assert payload["track_id"] is None

    def test_get_events_no_filter(self, event_store, sample_face_event, sample_plate_event):
        """Test querying all events without filters."""
        event_store.save_event(sample_face_event)
        event_store.save_event(sample_plate_event)

        events = event_store.get_events(limit=100)

        assert len(events) == 2
        # Most recent first (descending order)
        assert events[0]["type"] == "plate_read"
        assert events[1]["type"] == "face_match"

    def test_get_events_filter_by_type(self, event_store, sample_face_event, sample_plate_event):
        """Test filtering events by type."""
        event_store.save_event(sample_face_event)
        event_store.save_event(sample_plate_event)

        face_events = event_store.get_events(event_type="face_match", limit=100)
        assert len(face_events) == 1
        assert face_events[0]["type"] == "face_match"

        plate_events = event_store.get_events(event_type="plate_read", limit=100)
        assert len(plate_events) == 1
        assert plate_events[0]["type"] == "plate_read"

    def test_get_events_filter_by_since(self, event_store, sample_face_event, sample_plate_event):
        """Test filtering events by timestamp."""
        event_store.save_event(sample_face_event)
        event_store.save_event(sample_plate_event)

        # Query events after face event
        events = event_store.get_events(since_ms=1234567890500, limit=100)
        assert len(events) == 1
        assert events[0]["type"] == "plate_read"

    def test_get_events_limit(self, event_store, sample_face_event):
        """Test limit parameter."""
        # Create 5 events
        for i in range(5):
            event = Event(
                type="face_match",
                payload=sample_face_event.payload,
                ts_ms=1234567890000 + i * 1000,
                frame_source_id="camera_1",
            )
            event_store.save_event(event)

        events = event_store.get_events(limit=3)
        assert len(events) == 3

    def test_get_face_match_not_found(self, event_store):
        """Test getting non-existent face match."""
        result = event_store.get_face_match(9999)
        assert result is None

    def test_get_plate_read_not_found(self, event_store):
        """Test getting non-existent plate read."""
        result = event_store.get_plate_read(9999)
        assert result is None

    def test_cleanup_old_events(self, event_store):
        """Test cleanup of old events."""
        # Create event with old timestamp
        old_event = Event(
            type="face_match",
            payload=FaceMatch(
                person_id="test",
                similarity=0.5,
                detection=Detection(
                    kind="face",
                    bbox=BBox(x1=0, y1=0, x2=10, y2=10),
                    score=0.9,
                ),
            ),
            ts_ms=1234567890000,
            frame_source_id="camera_1",
        )

        event_id = event_store.save_event(old_event)

        # Manually update created_at to be old (hack for testing)
        from sqlmodel import Session

        from cam_vision.events.store import EventRecord

        with Session(event_store.engine) as session:
            event_record = session.get(EventRecord, event_id)
            event_record.created_at = datetime.utcnow() - timedelta(days=40)
            session.add(event_record)
            session.commit()

        # Run cleanup
        deleted = event_store.cleanup_old_events()
        assert deleted == 1

        # Verify event is gone
        result = event_store.get_face_match(event_id)
        assert result is None

    def test_multiple_events_same_type(self, event_store):
        """Test saving multiple events of the same type."""
        for i in range(3):
            event = Event(
                type="plate_read",
                payload=PlateRead(
                    text_raw=f"PLATE{i}",
                    text_clean=f"PLATE{i}",
                    confidence=80.0 + i,
                    detection=Detection(
                        kind="plate",
                        bbox=BBox(x1=0, y1=0, x2=100, y2=50),
                        score=0.9,
                    ),
                ),
                ts_ms=1234567890000 + i * 1000,
                frame_source_id="camera_1",
            )
            event_store.save_event(event)

        events = event_store.get_events(event_type="plate_read", limit=100)
        assert len(events) == 3

        # Verify descending order
        assert events[0]["payload"]["text_clean"] == "PLATE2"
        assert events[1]["payload"]["text_clean"] == "PLATE1"
        assert events[2]["payload"]["text_clean"] == "PLATE0"
