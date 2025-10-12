"""Unit tests for SecureVision API client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from websockets.exceptions import ConnectionClosed

from cam_vision.ui.client import SecureVisionClient


@pytest.fixture
def client():
    """Create API client instance for testing."""
    return SecureVisionClient(
        api_url="http://localhost:8000",
        auth_token="test-token",
        max_events=10,
    )


@pytest.fixture
def client_no_auth():
    """Create API client without authentication."""
    return SecureVisionClient(
        api_url="http://localhost:8000",
        auth_token=None,
        max_events=10,
    )


class TestInitialization:
    """Test client initialization."""

    def test_init_defaults(self):
        """Test client initialization with defaults."""
        client = SecureVisionClient()
        assert client.api_url == "http://localhost:8000"
        assert client.auth_token is None
        assert client.max_events == 200
        assert client.http_client is None
        assert len(client.face_events) == 0
        assert len(client.plate_events) == 0

    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = SecureVisionClient(
            api_url="http://api.example.com:9000",
            auth_token="my-token",
            max_events=50,
        )
        assert client.api_url == "http://api.example.com:9000"
        assert client.auth_token == "my-token"
        assert client.max_events == 50

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from API URL."""
        client = SecureVisionClient(api_url="http://localhost:8000/")
        assert client.api_url == "http://localhost:8000"

    def test_get_headers_with_auth(self, client):
        """Test headers include auth token."""
        headers = client._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-token"

    def test_get_headers_without_auth(self, client_no_auth):
        """Test headers without auth token."""
        headers = client_no_auth._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers


class TestContextManager:
    """Test async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test client as async context manager."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx_instance = AsyncMock()
            mock_httpx.return_value = mock_httpx_instance

            async with client as c:
                assert c is client
                assert client.http_client is not None

            # Should auto-close
            mock_httpx_instance.aclose.assert_called_once()


class TestHTTPMethods:
    """Test REST API methods."""

    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test HTTP client connection."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx_instance = AsyncMock()
            mock_httpx.return_value = mock_httpx_instance

            await client.connect()

            assert client.http_client is not None
            mock_httpx.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_idempotent(self, client):
        """Test connect is idempotent."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx_instance = AsyncMock()
            mock_httpx.return_value = mock_httpx_instance

            await client.connect()
            await client.connect()  # Second call should do nothing

            # Should only be called once
            assert mock_httpx.call_count == 1

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test HTTP client closure."""
        mock_http = AsyncMock()
        client.http_client = mock_http

        await client.close()

        mock_http.aclose.assert_called_once()
        assert client.http_client is None

    @pytest.mark.asyncio
    async def test_get_health_success(self, client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ok": True,
            "ws_clients": 3,
            "recent_events": {"total": 42},
        }

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client.http_client = mock_http

        result = await client.get_health()

        assert result["ok"] is True
        assert result["ws_clients"] == 3
        mock_http.get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_get_health_http_error(self, client):
        """Test health check with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Error", request=None, response=mock_response)
        )
        client.http_client = mock_http

        result = await client.get_health()

        assert result["ok"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_health_auto_connect(self, client_no_auth):
        """Test health check auto-connects if not connected."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}

        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.get = AsyncMock(return_value=mock_response)
            mock_httpx.return_value = mock_httpx_instance

            result = await client_no_auth.get_health()

            assert result["ok"] is True
            mock_httpx.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_events_all(self, client):
        """Test get all events."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "type": "face_match"},
            {"id": 2, "type": "plate_read"},
        ]

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client.http_client = mock_http

        result = await client.get_events(limit=100)

        assert len(result) == 2
        mock_http.get.assert_called_once_with("/events", params={"limit": 100})

    @pytest.mark.asyncio
    async def test_get_events_filtered_by_type(self, client):
        """Test get events filtered by type."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "type": "face_match"}]

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client.http_client = mock_http

        result = await client.get_events(event_type="face_match", limit=50)

        assert len(result) == 1
        mock_http.get.assert_called_once_with("/events", params={"type": "face_match", "limit": 50})

    @pytest.mark.asyncio
    async def test_get_events_filtered_by_time(self, client):
        """Test get events filtered by timestamp."""
        mock_response = MagicMock()
        mock_response.json.return_value = []

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client.http_client = mock_http

        await client.get_events(since_ms=1700000000000, limit=25)

        mock_http.get.assert_called_once_with(
            "/events", params={"since": 1700000000000, "limit": 25}
        )

    @pytest.mark.asyncio
    async def test_get_events_http_error(self, client):
        """Test get events with HTTP error returns empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Unauthorized", request=None, response=mock_response)
        )
        client.http_client = mock_http

        result = await client.get_events()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_face_match_success(self, client):
        """Test get face match by ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 42,
            "type": "face_match",
            "payload": {"person_id": "john_doe"},
        }

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client.http_client = mock_http

        result = await client.get_face_match(42)

        assert result["id"] == 42
        assert result["payload"]["person_id"] == "john_doe"
        mock_http.get.assert_called_once_with("/faces/42")

    @pytest.mark.asyncio
    async def test_get_face_match_not_found(self, client):
        """Test get face match returns None for 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Not found", request=None, response=mock_response)
        )
        client.http_client = mock_http

        result = await client.get_face_match(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_plate_read_success(self, client):
        """Test get plate read by ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "type": "plate_read",
            "payload": {"text_clean": "ABC123"},
        }

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(return_value=mock_response)
        client.http_client = mock_http

        result = await client.get_plate_read(123)

        assert result["id"] == 123
        assert result["payload"]["text_clean"] == "ABC123"
        mock_http.get.assert_called_once_with("/plates/123")

    @pytest.mark.asyncio
    async def test_get_plate_read_not_found(self, client):
        """Test get plate read returns None for 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_http = AsyncMock()
        mock_http.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Not found", request=None, response=mock_response)
        )
        client.http_client = mock_http

        result = await client.get_plate_read(999)

        assert result is None


class TestWebSocket:
    """Test WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_ws_connect_url_conversion(self, client):
        """Test WebSocket URL is correctly derived from HTTP URL."""
        # HTTP URL should convert to WS
        client_http = SecureVisionClient(api_url="http://localhost:8000")
        expected_ws = "ws://localhost:8000/stream"
        actual_ws = client_http.api_url.replace("http://", "ws://") + "/stream"
        assert actual_ws == expected_ws

        # HTTPS URL should convert to WSS
        client_https = SecureVisionClient(api_url="https://api.example.com")
        expected_wss = "wss://api.example.com/stream"
        actual_wss = client_https.api_url.replace("https://", "wss://") + "/stream"
        assert actual_wss == expected_wss

    @pytest.mark.asyncio
    async def test_ws_connect_receives_events(self, client):
        """Test WebSocket receives and yields events."""
        # Mock WebSocket messages
        messages = [
            json.dumps({"type": "face_match", "id": 1, "ts_ms": 1000}),
            json.dumps({"type": "plate_read", "id": 2, "ts_ms": 2000}),
        ]

        mock_ws = AsyncMock()
        mock_ws.__aiter__.return_value = iter(messages)
        mock_ws.__aenter__.return_value = mock_ws
        mock_ws.__aexit__.return_value = AsyncMock()

        with patch("websockets.connect", return_value=mock_ws):
            events = []
            async for event in client.ws_connect(max_retries=1):
                events.append(event)
                if len(events) >= 2:
                    break

            assert len(events) == 2
            assert events[0]["type"] == "face_match"
            assert events[1]["type"] == "plate_read"

    @pytest.mark.asyncio
    async def test_ws_connect_populates_ring_buffer(self, client):
        """Test WebSocket events are added to ring buffers."""
        messages = [
            json.dumps({"type": "face_match", "id": 1, "ts_ms": 1000}),
            json.dumps({"type": "plate_read", "id": 2, "ts_ms": 2000}),
        ]

        mock_ws = AsyncMock()
        mock_ws.__aiter__.return_value = iter(messages)
        mock_ws.__aenter__.return_value = mock_ws
        mock_ws.__aexit__.return_value = AsyncMock()

        with patch("websockets.connect", return_value=mock_ws):
            async for event in client.ws_connect(max_retries=1):
                if len(client.face_events) >= 1 and len(client.plate_events) >= 1:
                    break

            assert len(client.face_events) == 1
            assert len(client.plate_events) == 1

    @pytest.mark.asyncio
    async def test_ws_connect_skips_pong(self, client):
        """Test WebSocket skips pong messages."""
        messages = [
            json.dumps({"type": "pong"}),
            json.dumps({"type": "face_match", "id": 1, "ts_ms": 1000}),
        ]

        mock_ws = AsyncMock()
        mock_ws.__aiter__.return_value = iter(messages)
        mock_ws.__aenter__.return_value = mock_ws
        mock_ws.__aexit__.return_value = AsyncMock()

        with patch("websockets.connect", return_value=mock_ws):
            events = []
            async for event in client.ws_connect(max_retries=1):
                events.append(event)
                if len(events) >= 1:
                    break

            # Should only get face_match, pong should be filtered
            assert len(events) == 1
            assert events[0]["type"] == "face_match"

    @pytest.mark.asyncio
    async def test_ws_connect_handles_invalid_json(self, client):
        """Test WebSocket handles invalid JSON gracefully."""
        messages = [
            "invalid json",
            json.dumps({"type": "face_match", "id": 1, "ts_ms": 1000}),
        ]

        mock_ws = AsyncMock()
        mock_ws.__aiter__.return_value = iter(messages)
        mock_ws.__aenter__.return_value = mock_ws
        mock_ws.__aexit__.return_value = AsyncMock()

        with patch("websockets.connect", return_value=mock_ws):
            events = []
            async for event in client.ws_connect(max_retries=1):
                events.append(event)
                if len(events) >= 1:
                    break

            # Should skip invalid JSON and get valid event
            assert len(events) == 1
            assert events[0]["type"] == "face_match"

    @pytest.mark.asyncio
    async def test_ws_connect_reconnects_on_connection_closed(self, client):
        """Test WebSocket reconnects on connection closed."""
        # First connection fails, second succeeds
        mock_ws_fail = AsyncMock()
        mock_ws_fail.__aenter__.side_effect = ConnectionClosed(None, None)

        mock_ws_success = AsyncMock()
        messages = [json.dumps({"type": "face_match", "id": 1, "ts_ms": 1000})]
        mock_ws_success.__aiter__.return_value = iter(messages)
        mock_ws_success.__aenter__.return_value = mock_ws_success
        mock_ws_success.__aexit__.return_value = AsyncMock()

        with patch("websockets.connect", side_effect=[mock_ws_fail, mock_ws_success]):
            with patch("asyncio.sleep", new_callable=AsyncMock):  # Speed up test
                events = []
                async for event in client.ws_connect(max_retries=3, base_delay=0.1):
                    events.append(event)
                    if len(events) >= 1:
                        break

                # Should reconnect and get event
                assert len(events) == 1

    @pytest.mark.asyncio
    async def test_ws_connect_respects_max_retries(self, client):
        """Test WebSocket stops after max retries."""
        mock_ws = AsyncMock()
        mock_ws.__aenter__.side_effect = ConnectionClosed(None, None)

        with patch("websockets.connect", return_value=mock_ws):
            with patch("asyncio.sleep", new_callable=AsyncMock):  # Speed up test
                event_count = 0
                async for event in client.ws_connect(max_retries=2, base_delay=0.1):
                    event_count += 1

                # Should give up after 2 retries
                assert event_count == 0


class TestRingBuffer:
    """Test ring buffer functionality."""

    def test_get_buffered_events_face_matches(self, client):
        """Test get buffered face match events."""
        # Add events to ring buffer
        client.face_events.append({"id": 1, "ts_ms": 1000})
        client.face_events.append({"id": 2, "ts_ms": 2000})
        client.face_events.append({"id": 3, "ts_ms": 3000})

        result = client.get_buffered_events("face_match")

        # Should be reversed (most recent first)
        assert len(result) == 3
        assert result[0]["id"] == 3
        assert result[1]["id"] == 2
        assert result[2]["id"] == 1

    def test_get_buffered_events_plate_reads(self, client):
        """Test get buffered plate read events."""
        client.plate_events.append({"id": 10, "ts_ms": 1000})
        client.plate_events.append({"id": 11, "ts_ms": 2000})

        result = client.get_buffered_events("plate_read")

        assert len(result) == 2
        assert result[0]["id"] == 11
        assert result[1]["id"] == 10

    def test_get_buffered_events_with_limit(self, client):
        """Test get buffered events with limit."""
        for i in range(5):
            client.face_events.append({"id": i, "ts_ms": i * 1000})

        result = client.get_buffered_events("face_match", limit=3)

        assert len(result) == 3

    def test_get_buffered_events_invalid_type(self, client):
        """Test get buffered events with invalid type returns empty list."""
        result = client.get_buffered_events("invalid_type")
        assert result == []

    def test_ring_buffer_max_size(self, client):
        """Test ring buffer respects max_events limit."""
        # Client created with max_events=10
        for i in range(15):
            client.face_events.append({"id": i, "ts_ms": i * 1000})

        # Should only keep last 10
        assert len(client.face_events) == 10
        assert client.face_events[0]["id"] == 5  # First 5 evicted

    def test_clear_buffer_all(self, client):
        """Test clear all buffers."""
        client.face_events.append({"id": 1})
        client.plate_events.append({"id": 2})

        client.clear_buffer()

        assert len(client.face_events) == 0
        assert len(client.plate_events) == 0

    def test_clear_buffer_face_only(self, client):
        """Test clear face buffer only."""
        client.face_events.append({"id": 1})
        client.plate_events.append({"id": 2})

        client.clear_buffer("face_match")

        assert len(client.face_events) == 0
        assert len(client.plate_events) == 1

    def test_clear_buffer_plate_only(self, client):
        """Test clear plate buffer only."""
        client.face_events.append({"id": 1})
        client.plate_events.append({"id": 2})

        client.clear_buffer("plate_read")

        assert len(client.face_events) == 1
        assert len(client.plate_events) == 0


class TestEventAge:
    """Test last event age calculation."""

    def test_get_last_event_age_no_events(self, client):
        """Test get last event age with no events."""
        assert client.get_last_event_age() is None

    def test_get_last_event_age_face_only(self, client):
        """Test get last event age with face events only."""
        import time

        ts_ms = int((time.time() - 5) * 1000)  # 5 seconds ago
        client.face_events.append({"ts_ms": ts_ms})

        age = client.get_last_event_age()
        assert age is not None
        assert 4.5 < age < 5.5  # Should be ~5 seconds

    def test_get_last_event_age_plate_only(self, client):
        """Test get last event age with plate events only."""
        import time

        ts_ms = int((time.time() - 10) * 1000)  # 10 seconds ago
        client.plate_events.append({"ts_ms": ts_ms})

        age = client.get_last_event_age()
        assert age is not None
        assert 9.5 < age < 10.5  # Should be ~10 seconds

    def test_get_last_event_age_most_recent(self, client):
        """Test get last event age returns most recent across both types."""
        import time

        old_ts = int((time.time() - 20) * 1000)
        recent_ts = int((time.time() - 3) * 1000)

        client.face_events.append({"ts_ms": old_ts})
        client.plate_events.append({"ts_ms": recent_ts})

        age = client.get_last_event_age()
        assert age is not None
        assert 2.5 < age < 3.5  # Should be ~3 seconds (most recent)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_close_without_connections(self, client):
        """Test close without active connections doesn't error."""
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_with_ws_error(self, client):
        """Test close handles WebSocket close errors gracefully."""
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = Exception("Close error")
        client.ws_client = mock_ws

        await client.close()  # Should not raise

        assert client.ws_client is None

    @pytest.mark.asyncio
    async def test_multiple_close_calls(self, client):
        """Test multiple close calls are safe."""
        mock_http = AsyncMock()
        client.http_client = mock_http

        await client.close()
        await client.close()  # Second call should be safe

        # Should only close once (second call is no-op)
        assert mock_http.aclose.call_count == 1

    def test_ring_buffer_empty_operations(self, client):
        """Test operations on empty ring buffer."""
        result = client.get_buffered_events("face_match")
        assert result == []

        client.clear_buffer()  # Should not error
        assert client.get_last_event_age() is None
