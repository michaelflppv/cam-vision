"""Background capture manager for Streamlit dashboard."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from cam_vision.config import load_settings
from cam_vision.face.gallery import FaceGallery
from cam_vision.face.recognizer import FaceRecognizer
from cam_vision.io.capture import OpenCVCapture
from cam_vision.pipeline.confirm import ConfirmationProcessor
from cam_vision.plates.detector import YOLOPlateDetector
from cam_vision.plates.lists import PlateListLoader
from cam_vision.plates.ocr import TesseractOCR
from cam_vision.plates.pipeline import PlateRecognizer
from cam_vision.types import Detection, FaceMatch, FaceObservation, Frame, PlateRead

logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    """Frame with detection results."""

    frame: Frame
    face_matches: List[FaceMatch]
    face_observations: List[FaceObservation]
    plate_reads: List[PlateRead]
    preview_image: np.ndarray


class CaptureManager:
    """Thread-safe capture manager for UI."""

    def __init__(
        self,
        enable_faces: bool = True,
        enable_plates: bool = True,
        enable_tracking: bool = True,
    ):
        """
        Initialize capture manager.

        Args:
            enable_faces: Enable face recognition (requires gallery)
            enable_plates: Enable plate detection + OCR (requires YOLO model)
            enable_tracking: Enable multi-frame tracking and confirmation (reduces false positives)
        """
        self.thread: Optional[threading.Thread] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=10)
        self.stop_event: threading.Event = threading.Event()
        self.capture: Optional[OpenCVCapture] = None

        # Feature flags
        self.enable_faces = enable_faces
        self.enable_plates = enable_plates
        self.enable_tracking = enable_tracking

        # Processors
        self.face_recognizer: Optional[FaceRecognizer] = None
        self.plate_recognizer: Optional[PlateRecognizer] = None

        # Initialization status tracking
        self.face_init_error: Optional[str] = None
        self.plate_init_error: Optional[str] = None
        self.gallery_person_count: int = 0

        self._stats = {"fps": 0.0, "frame_count": 0}
        self._running = False
        self._tracking_params = {}  # Will be populated in start()

        # Load config for default settings
        try:
            self.settings = load_settings()
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}. Using defaults.")
            self.settings = None

    def start(
        self,
        source_config,
        fps_target=15,
        frame_resize=None,
        face_similarity_threshold=None,
        tracking_enabled=None,
        frames_required=None,
        iou_threshold=None,
        max_age_frames=None,
        ocr_agreement_threshold=None,
    ):
        """Start capture with given config.

        Args:
            source_config: Video source configuration
            fps_target: Target FPS for capture
            frame_resize: Optional frame resize tuple (width, height)
            face_similarity_threshold: Optional face similarity threshold override (0.0-1.0)
            tracking_enabled: Optional tracking enabled override (default from config or self.enable_tracking)
            frames_required: Optional frames required override (default from config)
            iou_threshold: Optional IoU threshold override (default from config)
            max_age_frames: Optional max age override (default from config)
            ocr_agreement_threshold: Optional OCR agreement threshold override (default from config)
        """
        if self._running:
            logger.warning("Capture already running")
            return

        self.stop_event.clear()

        # Override tracking settings if provided
        if tracking_enabled is not None:
            self.enable_tracking = tracking_enabled

        # Store tracking parameters for processor initialization
        self._tracking_params = {
            "frames_required": frames_required,
            "iou_threshold": iou_threshold,
            "max_age_frames": max_age_frames,
            "ocr_agreement_threshold": ocr_agreement_threshold,
        }

        # Create capture
        self.capture = OpenCVCapture(
            source_config=source_config,
            fps_target=fps_target,
            frame_resize=frame_resize,
            source_id="ui",
        )

        # Initialize face recognition if enabled
        if self.enable_faces:
            try:
                self._init_face_recognizer(similarity_threshold=face_similarity_threshold)
                self.face_init_error = None  # Success
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Failed to initialize face recognizer: {error_msg}")
                self.enable_faces = False
                self.face_recognizer = None
                self.face_init_error = error_msg

        # Initialize plate recognition if enabled
        if self.enable_plates:
            try:
                self._init_plate_recognizer()
                self.plate_init_error = None  # Success
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Failed to initialize plate recognizer: {error_msg}")
                self.enable_plates = False
                self.plate_recognizer = None
                self.plate_init_error = error_msg

        # Start background thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        self._running = True
        logger.info(
            f"Capture started: {source_config.type} "
            f"(faces={'on' if self.enable_faces else 'off'}, "
            f"plates={'on' if self.enable_plates else 'off'})"
        )

    def _init_face_recognizer(self, similarity_threshold=None) -> None:
        """Initialize face recognizer with gallery.

        Args:
            similarity_threshold: Optional threshold override (0.0-1.0). If None, uses config default.
        """
        if self.settings is None or not self.settings.face.enabled:
            raise RuntimeError("Face recognition not enabled in config")

        # Load gallery
        gallery = FaceGallery(
            gallery_path=self.settings.face.gallery_path,
            cache_path=self.settings.face.gallery_cache,
        )

        if not Path(self.settings.face.gallery_cache).exists():
            raise FileNotFoundError(
                f"Gallery cache not found at {self.settings.face.gallery_cache}. "
                "Run 'securevision-face-enroll' first."
            )

        gallery.load()
        self.gallery_person_count = gallery.size()

        # Use provided threshold or fall back to config
        threshold_to_use = (
            similarity_threshold
            if similarity_threshold is not None
            else self.settings.face.similarity_threshold
        )

        # Create recognizer with custom threshold
        base_recognizer = FaceRecognizer(
            gallery=gallery,
            similarity_threshold=threshold_to_use,
            min_face_size=self.settings.face.min_face_size,
        )

        # Wrap with ConfirmationProcessor if tracking enabled
        if self.enable_tracking:
            # Get tracking parameters (from overrides or config)
            frames_req = self._get_tracking_param("frames_required", 3)
            iou_thresh = self._get_tracking_param("iou_threshold", 0.5)
            max_age = self._get_tracking_param("max_age_frames", 30)

            self.face_recognizer = ConfirmationProcessor(
                wrapped_processor=base_recognizer,
                detection_kind="face",
                frames_required=frames_req,
                iou_threshold=iou_thresh,
                max_age=max_age,
            )
            logger.info(
                f"Face recognizer initialized with tracking: {self.gallery_person_count} persons, "
                f"threshold={threshold_to_use}, "
                f"frames_required={frames_req}, iou_threshold={iou_thresh}"
            )
        else:
            self.face_recognizer = base_recognizer
            logger.info(
                f"Face recognizer initialized (no tracking): {self.gallery_person_count} persons, "
                f"threshold={threshold_to_use}"
            )

        self.face_recognizer.open()

    def _get_tracking_param(self, param_name: str, default_value):
        """Get tracking parameter from override or config."""
        # Check if override was provided
        override_value = self._tracking_params.get(param_name)
        if override_value is not None:
            return override_value

        # Fall back to config
        if self.settings and hasattr(self.settings, "tracking"):
            return getattr(self.settings.tracking, param_name, default_value)

        return default_value

    def _init_plate_recognizer(self) -> None:
        """Initialize plate recognizer with YOLO + OCR."""
        if self.settings is None or not self.settings.plates.enabled:
            raise RuntimeError("Plate recognition not enabled in config")

        # Check if model exists
        model_path = Path(self.settings.plates.detector.model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"YOLO model not found at {model_path}. "
                "Download or train a YOLOv8 plate detection model."
            )

        # Create detector
        detector = YOLOPlateDetector(
            model_path=str(model_path),
            conf_threshold=self.settings.plates.detector.conf_threshold,
            iou_threshold=self.settings.plates.detector.iou_threshold,
            max_det=self.settings.plates.detector.max_det,
            input_size=self.settings.plates.detector.input_size,
        )

        # Create OCR
        ocr = TesseractOCR(self.settings.plates.ocr)

        # Load plate lists
        lists = PlateListLoader(
            whitelist_path=self.settings.plates.whitelist_path,
            blacklist_path=self.settings.plates.blacklist_path,
        )

        # Create recognizer
        base_recognizer = PlateRecognizer.from_config(self.settings.plates, detector, ocr, lists)

        # Wrap with ConfirmationProcessor if tracking enabled
        if self.enable_tracking:
            # Get tracking parameters (from overrides or config)
            frames_req = self._get_tracking_param("frames_required", 3)
            iou_thresh = self._get_tracking_param("iou_threshold", 0.5)
            max_age = self._get_tracking_param("max_age_frames", 30)
            ocr_agreement = self._get_tracking_param("ocr_agreement_threshold", 0.6)

            self.plate_recognizer = ConfirmationProcessor(
                wrapped_processor=base_recognizer,
                detection_kind="plate",
                frames_required=frames_req,
                iou_threshold=iou_thresh,
                max_age=max_age,
                ocr_agreement_threshold=ocr_agreement,
            )
            logger.info(
                f"Plate recognizer initialized with tracking: model={model_path.name}, "
                f"lists={lists.size()} plates, threshold={self.settings.plates.min_confidence}, "
                f"frames_required={frames_req}, ocr_agreement={ocr_agreement}"
            )
        else:
            self.plate_recognizer = base_recognizer
            logger.info(
                f"Plate recognizer initialized (no tracking): model={model_path.name}, "
                f"lists={lists.size()} plates, threshold={self.settings.plates.min_confidence}"
            )

        self.plate_recognizer.open()

    def stop(self):
        """Stop capture thread gracefully."""
        if not self._running:
            return

        self.stop_event.set()

        if self.thread:
            self.thread.join(timeout=2.0)

        # Close processors
        if self.face_recognizer:
            try:
                self.face_recognizer.close()
            except Exception as e:
                logger.error(f"Error closing face recognizer: {e}")
            self.face_recognizer = None

        if self.plate_recognizer:
            try:
                self.plate_recognizer.close()
            except Exception as e:
                logger.error(f"Error closing plate recognizer: {e}")
            self.plate_recognizer = None

        # Close capture
        if self.capture:
            self.capture.close()
            self.capture = None

        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        self._running = False
        logger.info("Capture stopped")

    def get_latest_frame(self) -> Optional[FrameResult]:
        """Non-blocking frame retrieval."""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def get_stats(self) -> dict:
        """Get FPS and detection stats."""
        return self._stats.copy()

    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._running

    def get_init_status(self) -> dict:
        """Get initialization status for features."""
        return {
            "faces_enabled": self.enable_faces,
            "plates_enabled": self.enable_plates,
            "face_error": self.face_init_error,
            "plate_error": self.plate_init_error,
            "gallery_persons": self.gallery_person_count,
        }

    def _collect_face_observations(self, face_matches: List[FaceMatch]) -> List[FaceObservation]:
        """Retrieve face observations from the active recognizer (wrapper-safe)."""
        processor = self.face_recognizer
        if processor is None:
            return []

        observations: List[FaceObservation] = []

        candidate_processors = [processor]
        wrapped = getattr(processor, "wrapped_processor", None)
        if wrapped is not None:
            candidate_processors.append(wrapped)

        for candidate in candidate_processors:
            if hasattr(candidate, "get_latest_observations"):
                try:
                    observations = candidate.get_latest_observations()  # type: ignore[attr-defined]
                except Exception as exc:
                    logger.error(f"Failed to fetch face observations: {exc}")
                    observations = []
                break

        if not observations:
            return []

        # Enrich observations with confirmed track IDs when available
        track_lookup: dict[tuple[int, int, int, int], int] = {}
        for match in face_matches:
            if match.detection.track_id is None:
                continue
            bbox = match.detection.bbox
            track_lookup[(bbox.x1, bbox.y1, bbox.x2, bbox.y2)] = match.detection.track_id

        if not track_lookup:
            return list(observations)

        enriched: List[FaceObservation] = []
        for observation in observations:
            bbox = observation.detection.bbox
            track_id = track_lookup.get((bbox.x1, bbox.y1, bbox.x2, bbox.y2))
            if track_id is None or observation.detection.track_id == track_id:
                enriched.append(observation)
                continue

            enriched_detection = Detection(
                kind=observation.detection.kind,
                bbox=observation.detection.bbox,
                score=observation.detection.score,
                track_id=track_id,
            )

            enriched.append(
                FaceObservation(
                    detection=enriched_detection,
                    person_id=observation.person_id,
                    similarity=observation.similarity,
                    matched=observation.matched,
                )
            )

        return enriched

    def _capture_loop(self):
        """Background capture loop with face and plate recognition."""
        try:
            self.capture.open()

            while not self.stop_event.is_set():
                frame = self.capture.read()

                if frame is None:
                    time.sleep(0.01)
                    continue

                # Update stats
                self._stats["frame_count"] += 1
                self._stats["fps"] = self.capture.get_fps()

                # Process face matches and collect observations
                face_matches: List[FaceMatch] = []
                if self.enable_faces and self.face_recognizer:
                    try:
                        for event in self.face_recognizer.process_frame(frame):
                            face_matches.append(event.payload)
                    except Exception as e:
                        logger.error(f"Face recognition failed: {e}")
                face_observations: List[FaceObservation] = (
                    self._collect_face_observations(face_matches)
                    if self.enable_faces and self.face_recognizer
                    else []
                )

                # Process plate reads
                plate_reads: List[PlateRead] = []
                if self.enable_plates and self.plate_recognizer:
                    try:
                        for event in self.plate_recognizer.process_frame(frame):
                            plate_reads.append(event.payload)
                    except Exception as e:
                        logger.error(f"Plate recognition failed: {e}")

                # Create preview image with annotations
                preview_img = frame.image.copy()

                # Draw face detections (green for matches, amber for unknown)
                for observation in face_observations:
                    bbox = observation.detection.bbox
                    color = (0, 255, 0) if observation.matched else (0, 165, 255)
                    cv2.rectangle(preview_img, (bbox.x1, bbox.y1), (bbox.x2, bbox.y2), color, 2)
                    label = observation.label
                    if observation.detection.track_id is not None:
                        label += f" T{observation.detection.track_id}"
                    cv2.putText(
                        preview_img,
                        label,
                        (bbox.x1, max(0, bbox.y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2,
                    )

                # Draw plate detection boxes (blue for plates)
                for plate in plate_reads:
                    bbox = plate.detection.bbox
                    cv2.rectangle(
                        preview_img, (bbox.x1, bbox.y1), (bbox.x2, bbox.y2), (255, 0, 0), 2
                    )
                    # Draw plate text with track ID if available
                    label = plate.text_clean
                    if plate.detection.track_id is not None:
                        label += f" T{plate.detection.track_id}"
                    cv2.putText(
                        preview_img,
                        label,
                        (bbox.x1, bbox.y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 0, 0),
                        2,
                    )

                # Create result
                result = FrameResult(
                    frame=frame,
                    face_matches=face_matches,
                    face_observations=face_observations,
                    plate_reads=plate_reads,
                    preview_image=preview_img,
                )

                # Put in queue (non-blocking, drop old frames if full)
                try:
                    self.frame_queue.put_nowait(result)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(result)
                    except queue.Empty:
                        pass

        except Exception as e:
            logger.error(f"Capture loop error: {e}", exc_info=True)
        finally:
            if self.capture:
                self.capture.close()
