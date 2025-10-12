"""SQLite event storage using SQLModel."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from sqlmodel import Column, Field, Session, SQLModel, String, create_engine, select

from ..types import BBox, Event, FaceMatch, PlateRead

logger = logging.getLogger(__name__)


class EventRecord(SQLModel, table=True):
    """
    Base event record.

    Stores common event metadata. Actual event payloads are in
    FaceMatchRecord and PlateReadRecord tables with FK to this table.
    """

    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(sa_column=Column(String, nullable=False, index=True))
    ts_ms: int = Field(nullable=False, index=True)
    frame_source_id: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)


class FaceMatchRecord(SQLModel, table=True):
    """Face match event details."""

    __tablename__ = "face_matches"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", nullable=False, index=True)

    # FaceMatch fields
    person_id: str = Field(nullable=False, index=True)
    similarity: float = Field(nullable=False)

    # Detection fields (bbox as JSON for flexibility)
    bbox: str = Field(sa_column=Column(String, nullable=False))  # JSON: {x1,y1,x2,y2}
    detection_score: float = Field(nullable=False)
    track_id: Optional[int] = Field(default=None, index=True)

    # Future-proofing: detector metadata
    detector_metadata: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )  # JSON


class PlateReadRecord(SQLModel, table=True):
    """License plate read event details."""

    __tablename__ = "plate_reads"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="events.id", nullable=False, index=True)

    # PlateRead fields
    text_raw: str = Field(nullable=False)
    text_clean: str = Field(nullable=False, index=True)
    ocr_confidence: float = Field(nullable=False)  # Tesseract confidence (0-100)
    detector_score: float = Field(nullable=False)  # YOLO detection score (0-1)
    matched_list: Optional[str] = Field(default=None, index=True)  # whitelist/blacklist/null
    preprocessing_used: str = Field(default="", nullable=False)

    # Detection fields (bbox as JSON for flexibility)
    bbox: str = Field(sa_column=Column(String, nullable=False))  # JSON: {x1,y1,x2,y2}
    track_id: Optional[int] = Field(default=None, index=True)

    # Future-proofing: detector metadata
    detector_metadata: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )  # JSON


class EventStore:
    """
    Event storage with SQLite backend.

    Provides CRUD operations for events and automatic retention cleanup.
    """

    def __init__(self, db_url: str, retention_days: int = 30):
        """
        Initialize event store.

        Args:
            db_url: SQLite database URL (e.g., "sqlite:///./data/events.db")
            retention_days: Auto-delete events older than this (default 30 days)
        """
        self.db_url = db_url
        self.retention_days = retention_days

        # Create engine
        self.engine = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},  # Allow multi-threaded access
        )

        # Create tables
        SQLModel.metadata.create_all(self.engine)
        logger.info(f"EventStore initialized: {db_url}, retention={retention_days} days")

    def save_event(self, event: Event) -> int:
        """
        Save event to database.

        Args:
            event: Event to save

        Returns:
            Event ID (primary key)
        """
        with Session(self.engine) as session:
            # Create base event record
            event_record = EventRecord(
                type=event.type,
                ts_ms=event.ts_ms,
                frame_source_id=event.frame_source_id,
            )
            session.add(event_record)
            session.commit()
            session.refresh(event_record)

            event_id = event_record.id

            # Create type-specific record
            if event.type == "face_match":
                self._save_face_match(session, event_id, event.payload)
            elif event.type == "plate_read":
                self._save_plate_read(session, event_id, event.payload)
            else:
                logger.warning(f"Unknown event type: {event.type}")

            session.commit()
            logger.debug(f"Saved event {event_id}: type={event.type}, ts_ms={event.ts_ms}")
            return event_id

    def _save_face_match(self, session: Session, event_id: int, payload: FaceMatch) -> None:
        """Save FaceMatch payload."""
        bbox_json = self._bbox_to_json(payload.detection.bbox)

        # Extract detector metadata if available
        detector_metadata = json.dumps(
            {
                "model_name": "insightface",  # Currently hardcoded, can be parameterized
                "detector": "retinaface",
                "recognition": "arcface",
            }
        )

        record = FaceMatchRecord(
            event_id=event_id,
            person_id=payload.person_id,
            similarity=payload.similarity,
            bbox=bbox_json,
            detection_score=payload.detection.score,
            track_id=payload.detection.track_id,
            detector_metadata=detector_metadata,
        )
        session.add(record)

    def _save_plate_read(self, session: Session, event_id: int, payload: PlateRead) -> None:
        """Save PlateRead payload."""
        bbox_json = self._bbox_to_json(payload.detection.bbox)

        # Extract detector metadata
        detector_metadata = json.dumps(
            {
                "model_name": "yolov8",
                "detector": "yolov8",
                "ocr_engine": "tesseract",
                "preprocessing": payload.preprocessing_used,
            }
        )

        record = PlateReadRecord(
            event_id=event_id,
            text_raw=payload.text_raw,
            text_clean=payload.text_clean,
            ocr_confidence=payload.confidence,  # Already 0-100 scale
            detector_score=payload.detection.score,
            matched_list=payload.matched_list,
            preprocessing_used=payload.preprocessing_used,
            bbox=bbox_json,
            track_id=payload.detection.track_id,
            detector_metadata=detector_metadata,
        )
        session.add(record)

    def get_events(
        self,
        event_type: Optional[Literal["face_match", "plate_read"]] = None,
        since_ms: Optional[int] = None,
        limit: int = 100,
    ) -> List[dict]:
        """
        Query events with optional filters.

        Args:
            event_type: Filter by event type (face_match or plate_read)
            since_ms: Only return events after this timestamp (milliseconds)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries with full payload
        """
        with Session(self.engine) as session:
            # Build query
            stmt = select(EventRecord)

            if event_type:
                stmt = stmt.where(EventRecord.type == event_type)

            if since_ms is not None:
                stmt = stmt.where(EventRecord.ts_ms >= since_ms)

            stmt = stmt.order_by(EventRecord.ts_ms.desc()).limit(limit)

            # Execute query
            events = session.exec(stmt).all()

            # Enrich with payload
            result = []
            for event in events:
                event_dict = {
                    "id": event.id,
                    "type": event.type,
                    "ts_ms": event.ts_ms,
                    "frame_source_id": event.frame_source_id,
                    "created_at": event.created_at.isoformat(),
                }

                # Fetch payload
                if event.type == "face_match":
                    payload = self._get_face_match_payload(session, event.id)
                elif event.type == "plate_read":
                    payload = self._get_plate_read_payload(session, event.id)
                else:
                    payload = None

                if payload:
                    event_dict["payload"] = payload

                result.append(event_dict)

            return result

    def get_face_match(self, event_id: int) -> Optional[dict]:
        """Get face match event by ID."""
        with Session(self.engine) as session:
            event = session.get(EventRecord, event_id)
            if not event or event.type != "face_match":
                return None

            return {
                "id": event.id,
                "type": event.type,
                "ts_ms": event.ts_ms,
                "frame_source_id": event.frame_source_id,
                "created_at": event.created_at.isoformat(),
                "payload": self._get_face_match_payload(session, event.id),
            }

    def get_plate_read(self, event_id: int) -> Optional[dict]:
        """Get plate read event by ID."""
        with Session(self.engine) as session:
            event = session.get(EventRecord, event_id)
            if not event or event.type != "plate_read":
                return None

            return {
                "id": event.id,
                "type": event.type,
                "ts_ms": event.ts_ms,
                "frame_source_id": event.frame_source_id,
                "created_at": event.created_at.isoformat(),
                "payload": self._get_plate_read_payload(session, event.id),
            }

    def _get_face_match_payload(self, session: Session, event_id: int) -> Optional[dict]:
        """Fetch FaceMatch payload."""
        stmt = select(FaceMatchRecord).where(FaceMatchRecord.event_id == event_id)
        record = session.exec(stmt).first()

        if not record:
            return None

        return {
            "person_id": record.person_id,
            "similarity": record.similarity,
            "bbox": json.loads(record.bbox),
            "detection_score": record.detection_score,
            "track_id": record.track_id,
            "detector_metadata": (
                json.loads(record.detector_metadata) if record.detector_metadata else None
            ),
        }

    def _get_plate_read_payload(self, session: Session, event_id: int) -> Optional[dict]:
        """Fetch PlateRead payload."""
        stmt = select(PlateReadRecord).where(PlateReadRecord.event_id == event_id)
        record = session.exec(stmt).first()

        if not record:
            return None

        return {
            "text_raw": record.text_raw,
            "text_clean": record.text_clean,
            "ocr_confidence": record.ocr_confidence,
            "detector_score": record.detector_score,
            "matched_list": record.matched_list,
            "preprocessing_used": record.preprocessing_used,
            "bbox": json.loads(record.bbox),
            "track_id": record.track_id,
            "detector_metadata": (
                json.loads(record.detector_metadata) if record.detector_metadata else None
            ),
        }

    def cleanup_old_events(self) -> int:
        """
        Delete events older than retention period.

        Returns:
            Number of events deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)

        with Session(self.engine) as session:
            # Get old event IDs
            stmt = select(EventRecord.id).where(EventRecord.created_at < cutoff)
            old_ids = session.exec(stmt).all()

            if not old_ids:
                return 0

            # Delete related records first (FK constraints)
            for event_id in old_ids:
                # Delete face matches
                face_stmt = select(FaceMatchRecord).where(FaceMatchRecord.event_id == event_id)
                for record in session.exec(face_stmt).all():
                    session.delete(record)

                # Delete plate reads
                plate_stmt = select(PlateReadRecord).where(PlateReadRecord.event_id == event_id)
                for record in session.exec(plate_stmt).all():
                    session.delete(record)

            # Delete events
            deleted = len(old_ids)
            for event_id in old_ids:
                event = session.get(EventRecord, event_id)
                if event:
                    session.delete(event)

            session.commit()
            logger.info(f"Deleted {deleted} events older than {cutoff.isoformat()}")
            return deleted

    @staticmethod
    def _bbox_to_json(bbox: BBox) -> str:
        """Convert BBox to JSON string."""
        return json.dumps({"x1": bbox.x1, "y1": bbox.y1, "x2": bbox.x2, "y2": bbox.y2})
