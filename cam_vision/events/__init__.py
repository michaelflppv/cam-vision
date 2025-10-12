"""Event storage and emission for SecureVision."""

from .emit import persist_and_broadcast
from .sink import EventStoreSink
from .store import EventRecord, EventStore, FaceMatchRecord, PlateReadRecord

__all__ = [
    "EventStore",
    "EventRecord",
    "FaceMatchRecord",
    "PlateReadRecord",
    "EventStoreSink",
    "persist_and_broadcast",
]
