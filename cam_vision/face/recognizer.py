"""Face recognition processor implementing the Processor interface."""

from __future__ import annotations

import logging
from typing import Iterable, List

import cv2
import numpy as np

from ..pipeline.base import Processor
from ..types import BBox, Detection, Event, FaceMatch, FaceObservation, Frame
from .gallery import FaceGallery
from .loader import FaceModels

logger = logging.getLogger(__name__)


class FaceRecognizer(Processor):
    """
    Face recognition processor using InsightFace.

    Pipeline:
    1. Detect faces in frame (RetinaFace)
    2. Apply quality gates (size, blur)
    3. Extract embeddings (ArcFace)
    4. Match against gallery (cosine similarity)
    5. Emit FaceMatch events

    Note: This processor is stateless per CLAUDE.md guidance.
          Multi-frame confirmation should be in Sink layer (PR8).
    """

    def __init__(
        self,
        gallery: FaceGallery,
        similarity_threshold: float = 0.35,
        min_face_size: int = 40,
        detect_blur: bool = False,
        blur_threshold: float = 100.0,
        det_size: tuple[int, int] = (640, 640),
    ):
        """
        Initialize face recognizer.

        Args:
            gallery: FaceGallery instance with loaded embeddings
            similarity_threshold: Minimum cosine similarity for match (0.0-1.0)
                                 Higher = stricter matching
            min_face_size: Minimum face size in pixels (width or height)
            detect_blur: Enable blur detection quality gate
            blur_threshold: Laplacian variance threshold for blur (higher = sharper)
            det_size: Detection input size (width, height)
        """
        self.gallery = gallery
        self.similarity_threshold = similarity_threshold
        self.min_face_size = min_face_size
        self.detect_blur = detect_blur
        self.blur_threshold = blur_threshold
        self.det_size = det_size

        self.models = None
        self._stats = {
            "total_frames": 0,
            "total_detections": 0,
            "matched": 0,
            "rejected_size": 0,
            "rejected_blur": 0,
            "rejected_threshold": 0,
        }
        self._latest_observations: List[FaceObservation] = []

    def open(self) -> None:
        """Load models and gallery."""
        logger.info(f"Opening FaceRecognizer (threshold={self.similarity_threshold})")

        # Load models
        self.models = FaceModels.get_models(det_size=self.det_size)

        # Ensure gallery is loaded
        if not self.gallery._loaded:
            self.gallery.load()

        logger.info(
            f"FaceRecognizer ready: {self.gallery.size()} persons in gallery, "
            f"min_size={self.min_face_size}px, "
            f"blur_detection={'on' if self.detect_blur else 'off'}"
        )

    def process_frame(self, frame: Frame) -> Iterable[Event]:
        """
        Process frame and emit FaceMatch events.

        Args:
            frame: Input frame with BGR image

        Yields:
            Event with FaceMatch payload for each matched face
        """
        self._stats["total_frames"] += 1

        # Detect faces
        try:
            faces = self.models.get(frame.image)
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            self._latest_observations = []
            return

        if len(faces) == 0:
            logger.debug(f"No faces detected in frame {frame.ts_ms}")
            self._latest_observations = []
            return

        self._stats["total_detections"] += len(faces)
        observations: List[FaceObservation] = []

        # Process each detected face
        for face in faces:
            # Extract bounding box
            bbox_array = face.bbox.astype(int)
            bbox = BBox(
                x1=bbox_array[0],
                y1=bbox_array[1],
                x2=bbox_array[2],
                y2=bbox_array[3],
            )

            # Quality gate: minimum size
            if bbox.width() < self.min_face_size or bbox.height() < self.min_face_size:
                self._stats["rejected_size"] += 1
                logger.debug(
                    f"Face too small: {bbox.width()}x{bbox.height()}px "
                    f"(min={self.min_face_size}px)"
                )
                continue

            # Quality gate: blur detection
            if self.detect_blur:
                face_crop = self._crop_face(frame.image, bbox)
                if self._is_blurry(face_crop):
                    self._stats["rejected_blur"] += 1
                    logger.debug(f"Face too blurry (Laplacian variance < {self.blur_threshold})")
                    continue

            # Get embedding (512-dim vector, already computed by InsightFace)
            embedding = face.embedding

            # Match against gallery
            match = self.gallery.match(embedding, self.similarity_threshold)

            # Create Detection
            detection = Detection(
                kind="face",
                bbox=bbox,
                score=float(face.det_score),  # Detection confidence
            )

            if match is None:
                self._stats["rejected_threshold"] += 1
                observations.append(
                    FaceObservation(
                        detection=detection,
                        matched=False,
                    )
                )
                continue

            # Unpack match
            person_id, similarity = match
            self._stats["matched"] += 1

            # Create FaceMatch
            face_match = FaceMatch(
                person_id=person_id,
                similarity=similarity,
                detection=detection,
            )

            observations.append(
                FaceObservation(
                    detection=detection,
                    person_id=person_id,
                    similarity=similarity,
                    matched=True,
                )
            )

            # Emit Event
            event = Event(
                type="face_match",
                payload=face_match,
                ts_ms=frame.ts_ms,
                frame_source_id=frame.source_id,
            )

            logger.info(
                f"Face matched: {person_id} "
                f"(similarity={similarity:.3f}, det_score={face.det_score:.3f})"
            )

            yield event

        self._latest_observations = observations

    def close(self) -> None:
        """Clean up resources and log statistics."""
        logger.info("Closing FaceRecognizer")
        logger.info(f"Statistics: {self._format_stats()}")

        # Models are cached globally, no explicit cleanup needed
        self.models = None

    def _crop_face(self, image: np.ndarray, bbox: BBox) -> np.ndarray:
        """Crop face region from image."""
        # Ensure coordinates are within image bounds
        h, w = image.shape[:2]
        x1 = max(0, bbox.x1)
        y1 = max(0, bbox.y1)
        x2 = min(w, bbox.x2)
        y2 = min(h, bbox.y2)

        return image[y1:y2, x1:x2]

    def _is_blurry(self, face_crop: np.ndarray) -> bool:
        """
        Detect if face is blurry using Laplacian variance.

        Args:
            face_crop: Face region (BGR image)

        Returns:
            True if blurry (variance < threshold)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)

        # Compute Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        return variance < self.blur_threshold

    def get_latest_observations(self) -> List[FaceObservation]:
        """Return face detections (matched and unknown) from the latest processed frame."""
        return list(self._latest_observations)

    def _format_stats(self) -> str:
        """Format statistics as human-readable string."""
        stats = self._stats
        total_det = stats["total_detections"]

        if total_det == 0:
            return "No faces detected"

        reject_size = stats["rejected_size"]
        reject_blur = stats["rejected_blur"]
        reject_thresh = stats["rejected_threshold"]
        matched = stats["matched"]

        return (
            f"frames={stats['total_frames']}, "
            f"detections={total_det}, "
            f"matched={matched} ({100*matched/total_det:.1f}%), "
            f"rejected: size={reject_size}, blur={reject_blur}, threshold={reject_thresh}"
        )

    def get_stats(self) -> dict:
        """Get statistics dictionary."""
        return self._stats.copy()

    @classmethod
    def from_config(cls, face_settings, gallery: FaceGallery) -> FaceRecognizer:
        """
        Factory method to create FaceRecognizer from FaceSettings.

        Args:
            face_settings: FaceSettings from AppSettings
            gallery: Loaded FaceGallery instance

        Returns:
            FaceRecognizer instance
        """
        return cls(
            gallery=gallery,
            similarity_threshold=face_settings.similarity_threshold,
            min_face_size=face_settings.min_face_size,
        )
