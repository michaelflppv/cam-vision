"""Event sink for persisting events to database."""

from __future__ import annotations

import logging
from typing import Optional

from ..pipeline.base import Sink
from ..types import Event
from .emit import WebSocketManager, persist_and_broadcast
from .store import EventStore

logger = logging.getLogger(__name__)


class EventStoreSink(Sink):
    """
    Sink that persists events to SQLite database.

    Optionally broadcasts events to WebSocket clients if manager is provided.
    Designed to be robust: DB failures are logged but don't crash the pipeline.
    """

    def __init__(
        self,
        store: EventStore,
        ws_manager: Optional[WebSocketManager] = None,
    ):
        """
        Initialize event store sink.

        Args:
            store: EventStore instance for persistence
            ws_manager: Optional WebSocket manager for broadcasting
        """
        self.store = store
        self.ws_manager = ws_manager
        self._event_count = 0
        self._error_count = 0

    def open(self) -> None:
        """Initialize sink (store already initialized)."""
        logger.info(
            f"EventStoreSink opened: db={self.store.db_url}, "
            f"ws_enabled={self.ws_manager is not None}"
        )

    def consume(self, event: Event) -> None:
        """
        Persist event to database and optionally broadcast.

        Args:
            event: Event to consume

        Note: Errors are logged but don't raise exceptions to avoid
              breaking the pipeline. This is intentional per CLAUDE.md.
        """
        try:
            event_id = persist_and_broadcast(event, self.store, self.ws_manager)

            if event_id:
                self._event_count += 1
                logger.debug(f"Event {event_id} persisted: type={event.type}")
            else:
                self._error_count += 1
                logger.error("Failed to persist event (no exception raised)")

        except Exception as e:
            self._error_count += 1
            logger.error(f"Error consuming event: {e}", exc_info=True)

    def close(self) -> None:
        """Clean up resources and log statistics."""
        logger.info(
            f"EventStoreSink closing: total_events={self._event_count}, "
            f"errors={self._error_count}"
        )

        # Note: EventStore engine is not explicitly closed to allow
        # API server to continue using it. In production, use connection pooling.

    def get_stats(self) -> dict:
        """Get sink statistics."""
        return {
            "events_persisted": self._event_count,
            "errors": self._error_count,
        }
