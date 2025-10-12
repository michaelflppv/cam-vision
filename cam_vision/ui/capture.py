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
from cam_vision.plates.detector import YOLOPlateDetector
from cam_vision.plates.lists import PlateListLoader
from cam_vision.plates.ocr import TesseractOCR
from cam_vision.plates.pipeline import PlateRecognizer
from cam_vision.types import FaceMatch, Frame, PlateRead

logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    """Frame with detection results."""

    frame: Frame
    face_matches: List[FaceMatch]
    plate_reads: List[PlateRead]
    preview_image: np.ndarray


class CaptureManager:
    """Thread-safe capture manager for UI."""

    def __init__(self, enable_faces: bool = True, enable_plates: bool = True):
        """
        Initialize capture manager.

        Args:
            enable_faces: Enable face recognition (requires gallery)
            enable_plates: Enable plate detection + OCR (requires YOLO model)
        """
        self.thread: Optional[threading.Thread] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=10)
        self.stop_event: threading.Event = threading.Event()
        self.capture: Optional[OpenCVCapture] = None

        # Feature flags
        self.enable_faces = enable_faces
        self.enable_plates = enable_plates

        # Processors
        self.face_recognizer: Optional[FaceRecognizer] = None
        self.plate_recognizer: Optional[PlateRecognizer] = None

        self._stats = {"fps": 0.0, "frame_count": 0}
        self._running = False

        # Load config for default settings
        try:
            self.settings = load_settings()
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}. Using defaults.")
            self.settings = None

    def start(self, source_config, fps_target=15, frame_resize=None):
        """Start capture with given config."""
        if self._running:
            logger.warning("Capture already running")
            return

        self.stop_event.clear()

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
                self._init_face_recognizer()
            except Exception as e:
                logger.warning(f"Failed to initialize face recognizer: {e}. Faces disabled.")
                self.enable_faces = False
                self.face_recognizer = None

        # Initialize plate recognition if enabled
        if self.enable_plates:
            try:
                self._init_plate_recognizer()
            except Exception as e:
                logger.warning(f"Failed to initialize plate recognizer: {e}. Plates disabled.")
                self.enable_plates = False
                self.plate_recognizer = None

        # Start background thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        self._running = True
        logger.info(
            f"Capture started: {source_config.type} "
            f"(faces={'on' if self.enable_faces else 'off'}, "
            f"plates={'on' if self.enable_plates else 'off'})"
        )

    def _init_face_recognizer(self) -> None:
        """Initialize face recognizer with gallery."""
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

        # Create recognizer
        self.face_recognizer = FaceRecognizer.from_config(self.settings.face, gallery)
        self.face_recognizer.open()

        logger.info(
            f"Face recognizer initialized: {gallery.size()} persons, "
            f"threshold={self.settings.face.similarity_threshold}"
        )

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
        ocr = TesseractOCR.from_config(self.settings.plates.ocr)

        # Load plate lists
        lists = PlateListLoader(
            whitelist_path=self.settings.plates.whitelist_path,
            blacklist_path=self.settings.plates.blacklist_path,
        )

        # Create recognizer
        self.plate_recognizer = PlateRecognizer.from_config(
            self.settings.plates, detector, ocr, lists
        )
        self.plate_recognizer.open()

        logger.info(
            f"Plate recognizer initialized: model={model_path.name}, "
            f"lists={lists.size()} plates, threshold={self.settings.plates.min_confidence}"
        )

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

                # Process face matches
                face_matches = []
                if self.enable_faces and self.face_recognizer:
                    try:
                        for event in self.face_recognizer.process_frame(frame):
                            face_matches.append(event.payload)
                    except Exception as e:
                        logger.error(f"Face recognition failed: {e}")

                # Process plate reads
                plate_reads = []
                if self.enable_plates and self.plate_recognizer:
                    try:
                        for event in self.plate_recognizer.process_frame(frame):
                            plate_reads.append(event.payload)
                    except Exception as e:
                        logger.error(f"Plate recognition failed: {e}")

                # Create preview image with annotations
                preview_img = frame.image.copy()

                # Draw face match boxes (green for matches)
                for match in face_matches:
                    bbox = match.detection.bbox
                    cv2.rectangle(
                        preview_img, (bbox.x1, bbox.y1), (bbox.x2, bbox.y2), (0, 255, 0), 2
                    )
                    # Draw person name
                    cv2.putText(
                        preview_img,
                        f"{match.person_id} ({match.similarity:.2f})",
                        (bbox.x1, bbox.y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

                # Draw plate detection boxes (blue for plates)
                for plate in plate_reads:
                    bbox = plate.detection.bbox
                    cv2.rectangle(
                        preview_img, (bbox.x1, bbox.y1), (bbox.x2, bbox.y2), (255, 0, 0), 2
                    )
                    # Draw plate text
                    cv2.putText(
                        preview_img,
                        plate.text_clean,
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
