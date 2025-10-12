"""SecureVision API client for REST and WebSocket communication."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from collections import deque
from typing import AsyncGenerator, Literal, Optional

import httpx
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class SecureVisionClient:
    """
    Client for SecureVision Events API.

    Features:
    - REST API client for querying events
    - WebSocket client for real-time event streaming
    - Auto-reconnect with exponential backoff
    - Ring buffer for event deduplication
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        max_events: int = 200,
    ):
        """
        Initialize API client.

        Args:
            api_url: Base URL for API (e.g., http://localhost:8000)
            auth_token: Optional bearer token for authentication
            max_events: Maximum events to keep in ring buffer
        """
        self.api_url = api_url.rstrip("/")
        self.auth_token = auth_token
        self.max_events = max_events

        # HTTP client
        self.http_client: Optional[httpx.AsyncClient] = None

        # WebSocket state
        self.ws_client: Optional[websockets.WebSocketClientProtocol] = None
        self.ws_running = False

        # Event buffers (ring buffers)
        self.face_events: deque = deque(maxlen=max_events)
        self.plate_events: deque = deque(maxlen=max_events)

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers with optional auth token."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Initialize HTTP client."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=self._get_headers(),
                timeout=10.0,
            )
            logger.info(f"HTTP client connected to {self.api_url}")

    async def close(self) -> None:
        """Close HTTP and WebSocket clients."""
        # Close WebSocket
        if self.ws_client:
            try:
                await self.ws_client.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            self.ws_client = None
            self.ws_running = False

        # Close HTTP client
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

        logger.info("API client closed")

    async def get_health(self) -> dict:
        """
        Get API health status.

        Returns:
            Health status dict with FPS metrics and connection info
        """
        if not self.http_client:
            await self.connect()

        try:
            response = await self.http_client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Health check failed: {e}")
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"ok": False, "error": str(e)}

    async def get_events(
        self,
        event_type: Optional[Literal["face_match", "plate_read"]] = None,
        since_ms: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Query events with filters.

        Args:
            event_type: Filter by type (face_match or plate_read)
            since_ms: Only return events after this timestamp (milliseconds)
            limit: Maximum number of events to return (1-1000)

        Returns:
            List of event dictionaries
        """
        if not self.http_client:
            await self.connect()

        params = {"limit": limit}
        if event_type:
            params["type"] = event_type
        if since_ms is not None:
            params["since"] = since_ms

        try:
            response = await self.http_client.get("/events", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Get events failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Get events error: {e}")
            return []

    async def get_face_match(self, event_id: int) -> Optional[dict]:
        """
        Get face match event by ID.

        Args:
            event_id: Event ID

        Returns:
            Face match event dict or None
        """
        if not self.http_client:
            await self.connect()

        try:
            response = await self.http_client.get(f"/faces/{event_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Get face match failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Get face match error: {e}")
            return None

    async def get_plate_read(self, event_id: int) -> Optional[dict]:
        """
        Get plate read event by ID.

        Args:
            event_id: Event ID

        Returns:
            Plate read event dict or None
        """
        if not self.http_client:
            await self.connect()

        try:
            response = await self.http_client.get(f"/plates/{event_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Get plate read failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Get plate read error: {e}")
            return None

    async def ws_connect(
        self,
        max_retries: int = 10,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> AsyncGenerator[dict, None]:
        """
        Connect to WebSocket stream with auto-reconnect.

        Yields events from WebSocket with exponential backoff on failures.

        Args:
            max_retries: Maximum reconnection attempts (0 = infinite)
            base_delay: Initial retry delay in seconds
            max_delay: Maximum retry delay in seconds

        Yields:
            Event dictionaries from WebSocket stream
        """
        ws_url = self.api_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/stream"

        retry_count = 0
        delay = base_delay

        while max_retries == 0 or retry_count < max_retries:
            try:
                logger.info(f"Connecting to WebSocket: {ws_url}")

                async with websockets.connect(
                    ws_url,
                    ping_interval=30,  # Send ping every 30s
                    ping_timeout=10,  # Wait 10s for pong
                ) as ws:
                    self.ws_client = ws
                    self.ws_running = True
                    logger.info("WebSocket connected")

                    # Reset retry state on successful connection
                    retry_count = 0
                    delay = base_delay

                    # Receive messages
                    async for message in ws:
                        try:
                            data = json.loads(message)

                            # Skip pong responses
                            if data.get("type") == "pong":
                                continue

                            # Add to ring buffer
                            event_type = data.get("type")
                            if event_type == "face_match":
                                self.face_events.append(data)
                            elif event_type == "plate_read":
                                self.plate_events.append(data)

                            yield data

                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from WebSocket: {e}")
                            continue

            except ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                self.ws_running = False

            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                self.ws_running = False

            except Exception as e:
                logger.error(f"Unexpected WebSocket error: {e}", exc_info=True)
                self.ws_running = False

            # Exponential backoff with jitter
            if max_retries > 0:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) reached, giving up")
                    break

            jitter = random.uniform(0, 0.3 * delay)
            sleep_time = min(delay + jitter, max_delay)
            logger.info(f"Reconnecting in {sleep_time:.1f}s (attempt {retry_count + 1})...")
            await asyncio.sleep(sleep_time)

            # Exponential backoff
            delay = min(delay * 2, max_delay)

        self.ws_running = False
        logger.info("WebSocket stream ended")

    def get_buffered_events(
        self,
        event_type: Literal["face_match", "plate_read"],
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        Get events from ring buffer (WebSocket accumulated events).

        Args:
            event_type: Type of events to retrieve
            limit: Maximum events to return (None = all)

        Returns:
            List of events (most recent first)
        """
        if event_type == "face_match":
            events = list(self.face_events)
        elif event_type == "plate_read":
            events = list(self.plate_events)
        else:
            return []

        # Reverse to get most recent first
        events.reverse()

        if limit is not None:
            return events[:limit]
        return events

    def clear_buffer(self, event_type: Optional[Literal["face_match", "plate_read"]] = None):
        """
        Clear event buffer.

        Args:
            event_type: Type to clear (None = clear all)
        """
        if event_type is None or event_type == "face_match":
            self.face_events.clear()
        if event_type is None or event_type == "plate_read":
            self.plate_events.clear()

        logger.debug(f"Cleared buffer: {event_type or 'all'}")

    def get_last_event_age(self) -> Optional[float]:
        """
        Get time since last event (seconds).

        Returns:
            Seconds since last event, or None if no events
        """
        last_event = None

        if self.face_events:
            last_event = self.face_events[-1]
        if self.plate_events and (
            not last_event or self.plate_events[-1]["ts_ms"] > last_event["ts_ms"]
        ):
            last_event = self.plate_events[-1]

        if not last_event:
            return None

        current_time_ms = int(time.time() * 1000)
        return (current_time_ms - last_event["ts_ms"]) / 1000.0
