"""Background worker for video capture and processing.

Wraps CaptureManager in a QThread to keep UI responsive.
"""

import logging
import time
from typing import Optional

from PySide6.QtCore import QThread, Signal

from cam_vision.ui.capture import CaptureManager

logger = logging.getLogger(__name__)


class CaptureWorker(QThread):
    """Background worker for video capture and frame processing.

    Wraps CaptureManager and runs it in a separate thread,
    emitting signals for UI updates.

    Signals:
        frame_ready: Emitted when new frame is available (FrameResult)
        stats_updated: Emitted periodically with capture stats (dict)
        error_occurred: Emitted on capture errors (str)
        started: Emitted when capture starts successfully
        stopped: Emitted when capture stops
        feature_status_ready: Emitted with feature initialization status (dict)
    """

    frame_ready = Signal(object)  # FrameResult
    stats_updated = Signal(dict)  # {"fps": float, "frame_count": int}
    error_occurred = Signal(str)
    started = Signal()
    stopped = Signal()
    feature_status_ready = Signal(dict)

    def __init__(
        self,
        enable_faces: bool = True,
        enable_plates: bool = True,
        enable_tracking: bool = True,
    ):
        """Initialize the capture worker.

        Args:
            enable_faces: Enable face recognition
            enable_plates: Enable plate detection and OCR
            enable_tracking: Enable multi-frame tracking/confirmation
        """
        super().__init__()
        self.capture_manager = CaptureManager(
            enable_faces=enable_faces,
            enable_plates=enable_plates,
            enable_tracking=enable_tracking,
        )
        self._should_stop = False
        self._config = None
        self._fps_target = 15
        self._frame_resize = None
        self._face_similarity_threshold = None
        self._tracking_params = {}

    def configure(
        self,
        source_config,
        fps_target: int = 15,
        frame_resize: Optional[tuple[int, int]] = None,
        face_similarity_threshold: Optional[float] = None,
        tracking_enabled: Optional[bool] = None,
        frames_required: Optional[int] = None,
        iou_threshold: Optional[float] = None,
        max_age_frames: Optional[int] = None,
        ocr_agreement_threshold: Optional[float] = None,
    ):
        """Configure capture parameters before starting.

        Args:
            source_config: Video source configuration
            fps_target: Target FPS for capture
            frame_resize: Optional (width, height) to resize frames
            face_similarity_threshold: Face similarity threshold (0.0-1.0)
            tracking_enabled: Enable tracking
            frames_required: Frames required for confirmation
            iou_threshold: IoU threshold for tracking
            max_age_frames: Max age for tracks
            ocr_agreement_threshold: OCR agreement threshold
        """
        self._config = source_config
        self._fps_target = fps_target
        self._frame_resize = frame_resize
        self._face_similarity_threshold = face_similarity_threshold
        self._tracking_params = {
            "tracking_enabled": tracking_enabled,
            "frames_required": frames_required,
            "iou_threshold": iou_threshold,
            "max_age_frames": max_age_frames,
            "ocr_agreement_threshold": ocr_agreement_threshold,
        }

    def run(self):
        """Main worker loop - runs in background thread.

        Starts capture, polls for frames, and emits signals.
        """
        if not self._config:
            self.error_occurred.emit("Capture not configured. Call configure() first.")
            return

        self._should_stop = False

        try:
            # Start CaptureManager
            logger.info("Starting CaptureManager...")
            self.capture_manager.start(
                source_config=self._config,
                fps_target=self._fps_target,
                frame_resize=self._frame_resize,
                face_similarity_threshold=self._face_similarity_threshold,
                **self._tracking_params,
            )

            # Emit feature status
            feature_status = self.capture_manager.get_init_status()
            self.feature_status_ready.emit(feature_status)

            self.started.emit()
            logger.info("CaptureWorker started successfully")

            # Main polling loop
            last_stats_time = time.time()
            stats_interval = 0.5  # Update stats every 500ms

            while not self._should_stop:
                # Poll for new frame
                frame_result = self.capture_manager.get_latest_frame()

                if frame_result:
                    self.frame_ready.emit(frame_result)

                # Emit stats periodically
                now = time.time()
                if now - last_stats_time >= stats_interval:
                    stats = self.capture_manager.get_stats()
                    self.stats_updated.emit(stats)
                    last_stats_time = now

                # Small sleep to prevent busy-waiting
                time.sleep(0.01)

        except Exception as e:
            logger.error(f"CaptureWorker error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            # Stop capture manager
            logger.info("Stopping CaptureManager...")
            self.capture_manager.stop()
            self.stopped.emit()
            logger.info("CaptureWorker stopped")

    def stop(self):
        """Request worker to stop gracefully."""
        logger.info("Stop requested for CaptureWorker")
        self._should_stop = True
