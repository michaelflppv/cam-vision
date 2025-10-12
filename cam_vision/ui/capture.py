"""Background capture manager for Streamlit dashboard."""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np

from cam_vision.face.loader import FaceModels  # Add this import
from cam_vision.io.capture import OpenCVCapture
from cam_vision.types import Frame, PlateRead

logger = logging.getLogger(__name__)


@dataclass
class FaceDetection:
    """Simple face detection result for UI."""

    bbox: tuple[int, int, int, int]
    score: float


@dataclass
class FrameResult:
    """Frame with detection results."""

    frame: Frame
    detections: List[PlateRead]
    preview_image: np.ndarray
    faces: list[FaceDetection] = None  # Add faces field


class CaptureManager:
    """Thread-safe capture manager for UI."""

    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=10)
        self.stop_event: threading.Event = threading.Event()
        self.capture: Optional[OpenCVCapture] = None
        self.plate_processor = None
        self.face_models = None  # Add for face detection
        self._stats = {"fps": 0.0, "frame_count": 0}
        self._running = False

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

        # Load face detection model if not loaded
        if self.face_models is None:
            self.face_models = FaceModels.get_models(det_size=(640, 640))

        # Start background thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        self._running = True
        logger.info(f"Capture started: {source_config.type}")

    def stop(self):
        """Stop capture thread gracefully."""
        if not self._running:
            return

        self.stop_event.set()

        if self.thread:
            self.thread.join(timeout=2.0)

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
        """Background capture loop."""
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

                # --- Face detection ---
                faces = []
                try:
                    detected = self.face_models.get(frame.image)
                    for face in detected:
                        bbox = face.bbox.astype(int)
                        faces.append(
                            FaceDetection(
                                bbox=(
                                    int(bbox[0]),
                                    int(bbox[1]),
                                    int(bbox[2]),
                                    int(bbox[3]),
                                ),
                                score=float(face.det_score),
                            )
                        )
                except Exception as e:
                    logger.debug(f"Face detection failed: {e}")

                # Draw face boxes on preview image
                preview_img = frame.image.copy()
                for face in faces:
                    x1, y1, x2, y2 = face.bbox
                    cv2.rectangle(preview_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        preview_img,
                        f"{face.score:.2f}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )

                # Create result
                result = FrameResult(
                    frame=frame,
                    detections=[],
                    preview_image=preview_img,
                    faces=faces,
                )

                # Put in queue (non-blocking)
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
