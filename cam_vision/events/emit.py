"""Event emission and broadcast helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Optional

from ..types import Event

if TYPE_CHECKING:
    from .store import EventStore

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for event broadcasting.

    Thread-safe connection pool with broadcast capability.
    """

    def __init__(self):
        self.connections: list = []  # List of WebSocket connections
        self._lock = asyncio.Lock()

    async def connect(self, websocket) -> None:
        """Add a new WebSocket connection."""
        async with self._lock:
            self.connections.append(websocket)
            logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")

    async def disconnect(self, websocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.connections:
                self.connections.remove(websocket)
                logger.info(f"WebSocket disconnected. Total connections: {len(self.connections)}")

    async def broadcast(self, message: dict) -> None:
        """
        Broadcast message to all connected WebSocket clients.

        Args:
            message: Dictionary to send as JSON
        """
        if not self.connections:
            return

        async with self._lock:
            disconnected = []
            for connection in self.connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.connections.remove(conn)

    def size(self) -> int:
        """Get number of active connections."""
        return len(self.connections)


def persist_and_broadcast(
    event: Event,
    store: EventStore,
    ws_manager: Optional[WebSocketManager] = None,
) -> Optional[int]:
    """
    Persist event to database and optionally broadcast via WebSocket.

    This is a synchronous wrapper that can be called from Sink.consume().
    WebSocket broadcast is queued asynchronously if manager is provided.

    Args:
        event: Event to persist
        store: EventStore instance
        ws_manager: Optional WebSocket manager for broadcasting

    Returns:
        Event ID if successful, None if failed
    """
    try:
        # Save to database
        event_id = store.save_event(event)

        # Broadcast to WebSocket clients if enabled
        if ws_manager and ws_manager.size() > 0:
            # Prepare message
            message = {
                "id": event_id,
                "type": event.type,
                "ts_ms": event.ts_ms,
                "frame_source_id": event.frame_source_id,
                "payload": _serialize_payload(event),
            }

            # Queue broadcast (non-blocking)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(ws_manager.broadcast(message))
                else:
                    # Fallback for synchronous context
                    logger.debug("Event loop not running, skipping WebSocket broadcast")
            except RuntimeError:
                logger.debug("No event loop available, skipping WebSocket broadcast")

        return event_id

    except Exception as e:
        logger.error(f"Failed to persist event: {e}", exc_info=True)
        return None


def _serialize_payload(event: Event) -> dict[str, Any]:
    """
    Serialize event payload to JSON-compatible dict.

    Args:
        event: Event with typed payload

    Returns:
        Dictionary representation of payload
    """
    payload = event.payload

    if event.type == "face_match":
        return {
            "person_id": payload.person_id,
            "similarity": payload.similarity,
            "bbox": {
                "x1": payload.detection.bbox.x1,
                "y1": payload.detection.bbox.y1,
                "x2": payload.detection.bbox.x2,
                "y2": payload.detection.bbox.y2,
            },
            "detection_score": payload.detection.score,
            "track_id": payload.detection.track_id,
        }
    elif event.type == "plate_read":
        return {
            "text_raw": payload.text_raw,
            "text_clean": payload.text_clean,
            "ocr_confidence": payload.confidence,
            "detector_score": payload.detection.score,
            "matched_list": payload.matched_list,
            "preprocessing_used": payload.preprocessing_used,
            "bbox": {
                "x1": payload.detection.bbox.x1,
                "y1": payload.detection.bbox.y1,
                "x2": payload.detection.bbox.x2,
                "y2": payload.detection.bbox.y2,
            },
            "track_id": payload.detection.track_id,
        }
    else:
        return {}
