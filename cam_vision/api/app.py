"""FastAPI application for SecureVision events API."""

from __future__ import annotations

import logging
import time
from typing import Any, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..config import AppSettings
from ..events.emit import WebSocketManager
from ..events.store import EventStore

logger = logging.getLogger(__name__)

# Global state (initialized in create_app)
_store: Optional[EventStore] = None
_ws_manager: Optional[WebSocketManager] = None
_auth_token: Optional[str] = None

# Security
security = HTTPBearer(auto_error=False)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> None:
    """
    Verify bearer token if authentication is enabled.

    Raises:
        HTTPException: If token is invalid or missing
    """
    if _auth_token is None:
        # No auth configured, allow all
        return

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    if credentials.credentials != _auth_token:
        raise HTTPException(status_code=401, detail="Invalid token")


# Request/Response models
class EventCreateRequest(BaseModel):
    """Request model for creating events (internal use)."""

    type: Literal["face_match", "plate_read"]
    ts_ms: int
    frame_source_id: str
    payload: dict[str, Any]


class EventResponse(BaseModel):
    """Response model for event queries."""

    id: int
    type: str
    ts_ms: int
    frame_source_id: str
    created_at: str
    payload: dict[str, Any]


def create_app(settings: Optional[AppSettings] = None) -> FastAPI:
    """
    Create FastAPI application.

    Args:
        settings: Application settings (loads from env if None)

    Returns:
        FastAPI application instance
    """
    global _store, _ws_manager, _auth_token

    # Load settings
    if settings is None:
        from ..config import load_settings

        settings = load_settings()

    # Initialize event store
    _store = EventStore(
        db_url=settings.events.db_url,
        retention_days=settings.events.retention_days,
    )

    # Initialize WebSocket manager if enabled
    if settings.api.ws_enabled:
        _ws_manager = WebSocketManager()
    else:
        _ws_manager = None

    # Set auth token if configured
    _auth_token = settings.api.auth_token

    # Create FastAPI app
    app = FastAPI(
        title="SecureVision Events API",
        description="REST API and WebSocket for face recognition and license plate events",
        version="0.1.0",
    )

    # CORS middleware (for dashboard in PR7)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Customize in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Endpoints ---

    @app.get("/")
    async def root():
        """Basic info endpoint."""
        return {
            "service": "SecureVision Events API",
            "version": "0.1.0",
            "ws_enabled": _ws_manager is not None,
            "auth_enabled": _auth_token is not None,
        }

    @app.get("/health")
    async def health():
        """
        Detailed health check with metrics.

        Returns system status including FPS metrics and connection info.
        This endpoint is always public (no auth required).
        """
        health_data = {
            "ok": True,
            "timestamp": int(time.time() * 1000),
            "service": "SecureVision Events API",
            "version": "0.1.0",
        }

        # WebSocket client count
        if _ws_manager is not None:
            health_data["ws_clients"] = len(_ws_manager.connections)
        else:
            health_data["ws_clients"] = 0

        # Database stats
        if _store is not None:
            try:
                # Get recent event counts (last 5 minutes)
                five_min_ago = int((time.time() - 300) * 1000)
                recent_events = _store.get_events(since_ms=five_min_ago, limit=1000)

                health_data["recent_events"] = {
                    "total": len(recent_events),
                    "face_matches": sum(1 for e in recent_events if e["type"] == "face_match"),
                    "plate_reads": sum(1 for e in recent_events if e["type"] == "plate_read"),
                }

                # Calculate approximate FPS (events per second over last 5 min)
                if len(recent_events) > 0:
                    # Get time span
                    oldest_ts = min(e["ts_ms"] for e in recent_events)
                    newest_ts = max(e["ts_ms"] for e in recent_events)
                    span_seconds = (newest_ts - oldest_ts) / 1000.0

                    if span_seconds > 0:
                        health_data["event_rate"] = {
                            "events_per_second": len(recent_events) / span_seconds,
                            "sample_duration_seconds": span_seconds,
                        }

            except Exception as e:
                logger.error(f"Error getting health stats from store: {e}")
                health_data["db_error"] = str(e)

        # Note: FPS metrics from pipeline would require passing a reference
        # to the pipeline/processors. For now, we derive FPS from event rate.
        # In full production, you'd inject processor references into app state.

        return health_data

    @app.post("/events", dependencies=[Depends(verify_token)])
    async def create_event(request: EventCreateRequest) -> dict:
        """
        Create a new event (internal use by pipeline).

        This endpoint is primarily for testing. In production, events
        are created by EventStoreSink in the pipeline.

        Args:
            request: Event data

        Returns:
            Created event with ID
        """
        # Note: This is a simplified version. In production, we'd validate
        # the payload against the event type and use the actual Event dataclass.
        # For now, we just store the raw data.

        logger.warning("POST /events called - this is for testing only, use EventStoreSink")
        raise HTTPException(
            status_code=501,
            detail="Direct event creation not implemented. Use EventStoreSink in pipeline.",
        )

    @app.get("/events", response_model=list[EventResponse], dependencies=[Depends(verify_token)])
    async def get_events(
        type: Optional[Literal["face_match", "plate_read"]] = Query(None),
        since: Optional[int] = Query(None, description="Timestamp in milliseconds"),
        limit: int = Query(100, ge=1, le=1000),
    ) -> list[EventResponse]:
        """
        Query events with optional filters.

        Args:
            type: Filter by event type (face_match or plate_read)
            since: Only return events after this timestamp (milliseconds)
            limit: Maximum number of events to return (1-1000, default 100)

        Returns:
            List of events with payloads
        """
        if _store is None:
            raise HTTPException(status_code=500, detail="Event store not initialized")

        events = _store.get_events(event_type=type, since_ms=since, limit=limit)

        return [
            EventResponse(
                id=e["id"],
                type=e["type"],
                ts_ms=e["ts_ms"],
                frame_source_id=e["frame_source_id"],
                created_at=e["created_at"],
                payload=e.get("payload", {}),
            )
            for e in events
        ]

    @app.get(
        "/faces/{event_id}", response_model=EventResponse, dependencies=[Depends(verify_token)]
    )
    async def get_face_match(event_id: int) -> EventResponse:
        """
        Get face match event by ID.

        Args:
            event_id: Event ID

        Returns:
            Face match event with payload
        """
        if _store is None:
            raise HTTPException(status_code=500, detail="Event store not initialized")

        event = _store.get_face_match(event_id)

        if event is None:
            raise HTTPException(status_code=404, detail="Face match event not found")

        return EventResponse(
            id=event["id"],
            type=event["type"],
            ts_ms=event["ts_ms"],
            frame_source_id=event["frame_source_id"],
            created_at=event["created_at"],
            payload=event.get("payload", {}),
        )

    @app.get(
        "/plates/{event_id}", response_model=EventResponse, dependencies=[Depends(verify_token)]
    )
    async def get_plate_read(event_id: int) -> EventResponse:
        """
        Get plate read event by ID.

        Args:
            event_id: Event ID

        Returns:
            Plate read event with payload including OCR fields
        """
        if _store is None:
            raise HTTPException(status_code=500, detail="Event store not initialized")

        event = _store.get_plate_read(event_id)

        if event is None:
            raise HTTPException(status_code=404, detail="Plate read event not found")

        return EventResponse(
            id=event["id"],
            type=event["type"],
            ts_ms=event["ts_ms"],
            frame_source_id=event["frame_source_id"],
            created_at=event["created_at"],
            payload=event.get("payload", {}),
        )

    @app.websocket("/stream")
    async def websocket_stream(websocket: WebSocket):
        """
        WebSocket endpoint for live event streaming.

        Clients connect here to receive real-time event notifications.
        No authentication for WebSocket (can be added if needed).

        Example client (JavaScript):
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/stream');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Event received:', data);
        };
        ```
        """
        if _ws_manager is None:
            await websocket.close(code=1008, reason="WebSocket not enabled")
            return

        await websocket.accept()
        await _ws_manager.connect(websocket)

        try:
            # Keep connection alive
            while True:
                # Wait for client messages (ping/pong)
                data = await websocket.receive_text()
                # Echo back for keep-alive
                await websocket.send_json({"type": "pong", "data": data})

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await _ws_manager.disconnect(websocket)

    @app.post("/cleanup", dependencies=[Depends(verify_token)])
    async def cleanup_old_events() -> dict:
        """
        Manually trigger cleanup of old events.

        Deletes events older than retention period (configured in settings).
        This is typically run periodically by a background task, but can be
        triggered manually for testing.

        Returns:
            Number of events deleted
        """
        if _store is None:
            raise HTTPException(status_code=500, detail="Event store not initialized")

        deleted = _store.cleanup_old_events()
        return {"deleted": deleted, "retention_days": _store.retention_days}

    # Expose global state for external access (used by Sink)
    app.state.store = _store
    app.state.ws_manager = _ws_manager

    logger.info(f"FastAPI app created: ws_enabled={_ws_manager is not None}")
    return app


def get_store() -> EventStore:
    """Get the global event store instance."""
    if _store is None:
        raise RuntimeError("Event store not initialized. Call create_app() first.")
    return _store


def get_ws_manager() -> Optional[WebSocketManager]:
    """Get the global WebSocket manager instance."""
    return _ws_manager
