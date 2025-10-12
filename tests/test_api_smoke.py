"""Smoke tests for FastAPI events API."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cam_vision.api.app import create_app
from cam_vision.config import APISettings, AppSettings, EventsSettings
from cam_vision.events.store import EventStore
from cam_vision.types import BBox, Detection, Event, FaceMatch, PlateRead


@pytest.fixture
def temp_db_url():
    """Create temporary database URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_api.db"
        yield f"sqlite:///{db_path}"


@pytest.fixture
def test_settings(temp_db_url):
    """Create test settings."""
    return AppSettings(
        events=EventsSettings(
            db_url=temp_db_url,
            retention_days=30,
        ),
        api=APISettings(
            host="127.0.0.1",
            port=8000,
            ws_enabled=True,
            auth_token=None,  # No auth for basic tests
        ),
    )


@pytest.fixture
def test_settings_with_auth(temp_db_url):
    """Create test settings with authentication."""
    return AppSettings(
        events=EventsSettings(
            db_url=temp_db_url,
            retention_days=30,
        ),
        api=APISettings(
            host="127.0.0.1",
            port=8000,
            ws_enabled=True,
            auth_token="test-secret-token",
        ),
    )


@pytest.fixture
def client(test_settings):
    """Create FastAPI test client."""
    app = create_app(test_settings)
    return TestClient(app)


@pytest.fixture
def client_with_auth(test_settings_with_auth):
    """Create FastAPI test client with authentication."""
    app = create_app(test_settings_with_auth)
    return TestClient(app)


@pytest.fixture
def sample_face_event():
    """Sample face match event."""
    return Event(
        type="face_match",
        payload=FaceMatch(
            person_id="alice",
            similarity=0.92,
            detection=Detection(
                kind="face",
                bbox=BBox(x1=50, y1=100, x2=250, y2=300),
                score=0.97,
                track_id=1,
            ),
        ),
        ts_ms=1700000000000,
        frame_source_id="cam_front",
    )


@pytest.fixture
def sample_plate_event():
    """Sample plate read event."""
    return Event(
        type="plate_read",
        payload=PlateRead(
            text_raw="XYZ 789",
            text_clean="XYZ789",
            confidence=92.3,
            detection=Detection(
                kind="plate",
                bbox=BBox(x1=100, y1=200, x2=400, y2=300),
                score=0.91,
                track_id=2,
            ),
            matched_list="blacklist",
            preprocessing_used="grayscale,adaptive",
        ),
        ts_ms=1700000001000,
        frame_source_id="cam_front",
    )


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    def test_root_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "SecureVision Events API"
        assert data["ws_enabled"] is True
        assert data["auth_enabled"] is False

    def test_get_events_empty(self, client):
        """Test GET /events with empty database."""
        response = client.get("/events")
        assert response.status_code == 200

        events = response.json()
        assert events == []

    def test_get_events_with_data(
        self, client, test_settings, sample_face_event, sample_plate_event
    ):
        """Test GET /events after adding events."""
        # Add events directly to store
        store = EventStore(test_settings.events.db_url)
        store.save_event(sample_face_event)
        store.save_event(sample_plate_event)

        response = client.get("/events")
        assert response.status_code == 200

        events = response.json()
        assert len(events) == 2

        # Most recent first
        assert events[0]["type"] == "plate_read"
        assert events[1]["type"] == "face_match"

    def test_get_events_filter_by_type(
        self, client, test_settings, sample_face_event, sample_plate_event
    ):
        """Test GET /events with type filter."""
        store = EventStore(test_settings.events.db_url)
        store.save_event(sample_face_event)
        store.save_event(sample_plate_event)

        # Filter face matches
        response = client.get("/events?type=face_match")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["type"] == "face_match"

        # Filter plate reads
        response = client.get("/events?type=plate_read")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["type"] == "plate_read"

    def test_get_events_filter_by_since(
        self, client, test_settings, sample_face_event, sample_plate_event
    ):
        """Test GET /events with since filter."""
        store = EventStore(test_settings.events.db_url)
        store.save_event(sample_face_event)
        store.save_event(sample_plate_event)

        # Query events after face event
        response = client.get("/events?since=1700000000500")
        assert response.status_code == 200

        events = response.json()
        assert len(events) == 1
        assert events[0]["type"] == "plate_read"

    def test_get_events_limit(self, client, test_settings):
        """Test GET /events with limit."""
        store = EventStore(test_settings.events.db_url)

        # Create 5 events
        for i in range(5):
            event = Event(
                type="face_match",
                payload=FaceMatch(
                    person_id=f"person_{i}",
                    similarity=0.8,
                    detection=Detection(
                        kind="face",
                        bbox=BBox(x1=0, y1=0, x2=10, y2=10),
                        score=0.9,
                    ),
                ),
                ts_ms=1700000000000 + i * 1000,
                frame_source_id="cam",
            )
            store.save_event(event)

        response = client.get("/events?limit=3")
        assert response.status_code == 200

        events = response.json()
        assert len(events) == 3

    def test_get_face_match_by_id(self, client, test_settings, sample_face_event):
        """Test GET /faces/{id}."""
        store = EventStore(test_settings.events.db_url)
        event_id = store.save_event(sample_face_event)

        response = client.get(f"/faces/{event_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "face_match"
        assert data["payload"]["person_id"] == "alice"
        assert data["payload"]["similarity"] == 0.92

    def test_get_face_match_not_found(self, client):
        """Test GET /faces/{id} with non-existent ID."""
        response = client.get("/faces/9999")
        assert response.status_code == 404

    def test_get_plate_read_by_id(self, client, test_settings, sample_plate_event):
        """Test GET /plates/{id}."""
        store = EventStore(test_settings.events.db_url)
        event_id = store.save_event(sample_plate_event)

        response = client.get(f"/plates/{event_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "plate_read"
        assert data["payload"]["text_clean"] == "XYZ789"
        assert data["payload"]["ocr_confidence"] == 92.3
        assert data["payload"]["detector_score"] == 0.91

    def test_get_plate_read_not_found(self, client):
        """Test GET /plates/{id} with non-existent ID."""
        response = client.get("/plates/9999")
        assert response.status_code == 404

    def test_cleanup_endpoint(self, client):
        """Test POST /cleanup."""
        response = client.post("/cleanup")
        assert response.status_code == 200

        data = response.json()
        assert "deleted" in data
        assert "retention_days" in data
        assert data["retention_days"] == 30


class TestAuthentication:
    """Test suite for API authentication."""

    def test_auth_required_get_events(self, client_with_auth):
        """Test GET /events requires auth when enabled."""
        response = client_with_auth.get("/events")
        assert response.status_code == 401

    def test_auth_valid_token(self, client_with_auth):
        """Test GET /events with valid token."""
        headers = {"Authorization": "Bearer test-secret-token"}
        response = client_with_auth.get("/events", headers=headers)
        assert response.status_code == 200

    def test_auth_invalid_token(self, client_with_auth):
        """Test GET /events with invalid token."""
        headers = {"Authorization": "Bearer wrong-token"}
        response = client_with_auth.get("/events", headers=headers)
        assert response.status_code == 401

    def test_auth_required_cleanup(self, client_with_auth):
        """Test POST /cleanup requires auth."""
        response = client_with_auth.post("/cleanup")
        assert response.status_code == 401

        headers = {"Authorization": "Bearer test-secret-token"}
        response = client_with_auth.post("/cleanup", headers=headers)
        assert response.status_code == 200


class TestWebSocket:
    """Test suite for WebSocket streaming."""

    def test_websocket_disabled(self, temp_db_url):
        """Test WebSocket when disabled in settings."""
        from starlette.websockets import WebSocketDisconnect

        settings = AppSettings(
            events=EventsSettings(db_url=temp_db_url),
            api=APISettings(ws_enabled=False),
        )
        app = create_app(settings)
        client = TestClient(app)

        # Expect WebSocketDisconnect when WS is disabled
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/stream") as _:
                pass  # Should not reach here

    def test_websocket_connection(self, client):
        """Test basic WebSocket connection."""
        with client.websocket_connect("/stream") as websocket:
            # Send ping
            websocket.send_text("ping")

            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert data["data"] == "ping"
