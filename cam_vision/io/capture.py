"""OpenCV-based video capture for device, RTSP, HTTP MJPEG, and file sources."""

from __future__ import annotations

import logging
import platform
import threading
import time
from typing import Optional

import cv2
import numpy as np

from ..config import DeviceSource, FileSource, HTTPMjpegSource, RTSPSource, VideoSettings
from ..pipeline.base import FrameSource
from ..types import Frame
from ..utils.timing import FPSMeter

logger = logging.getLogger(__name__)


def _get_backend_enum(backend_str: Optional[str]) -> int:
    """Convert backend string to OpenCV backend enum."""
    if backend_str is None:
        return cv2.CAP_ANY

    backend_map = {
        "AVFOUNDATION": cv2.CAP_AVFOUNDATION,
        "V4L2": cv2.CAP_V4L2,
        "DSHOW": cv2.CAP_DSHOW,
        "MSMF": cv2.CAP_MSMF,
        "FFMPEG": cv2.CAP_FFMPEG,
        "GSTREAMER": cv2.CAP_GSTREAMER,
        "ANY": cv2.CAP_ANY,
    }

    backend_upper = backend_str.upper()
    if backend_upper not in backend_map:
        raise ValueError(
            f"Unknown backend: {backend_str}. " f"Supported: {', '.join(backend_map.keys())}"
        )
    return backend_map[backend_upper]


def _get_default_device_backend() -> int:
    """Get platform-appropriate default backend for device capture."""
    system = platform.system()
    if system == "Darwin":  # macOS
        return cv2.CAP_AVFOUNDATION
    elif system == "Linux":
        return cv2.CAP_V4L2
    elif system == "Windows":
        return cv2.CAP_DSHOW
    return cv2.CAP_ANY


class OpenCVCapture(FrameSource):
    """
    OpenCV-based frame source supporting device, RTSP, HTTP MJPEG, and file sources.

    Features:
    - Platform-aware backend selection (AVFOUNDATION/V4L2/DSHOW)
    - Automatic reconnection for network sources (RTSP, HTTP MJPEG)
    - Frame preprocessing (resize, rotation)
    - FPS control via frame dropping
    - Context manager support for resource cleanup
    """

    def __init__(
        self,
        source_config: DeviceSource | RTSPSource | HTTPMjpegSource | FileSource,
        fps_target: int,
        frame_resize: Optional[tuple[int, int]] = None,
        rotate_180: bool = False,
        read_timeout_s: float = 5.0,
        reconnect_interval_s: float = 3.0,
        source_id: str = "default",
    ):
        """
        Initialize capture (call open() to start).

        Args:
            source_config: Concrete source configuration
            fps_target: Target FPS (frames will be dropped to achieve this)
            frame_resize: Optional (width, height) to resize frames
            rotate_180: Rotate frames 180 degrees
            read_timeout_s: Timeout for reading frames from network sources
            reconnect_interval_s: Base interval for reconnection attempts
            source_id: Identifier for this source (used in Frame.source_id)
        """
        self.source_config = source_config
        self.fps_target = fps_target
        self.frame_resize = frame_resize
        self.rotate_180 = rotate_180
        self.read_timeout_s = read_timeout_s
        self.reconnect_interval_s = reconnect_interval_s
        self.source_id = source_id

        self.cap: Optional[cv2.VideoCapture] = None
        self._opened = False
        self._last_read_time = -999.0  # Initialize to far past so first frame is not dropped
        self._frame_interval = 1.0 / max(1, fps_target)
        self._fps_meter = FPSMeter(window=60)
        self._consecutive_failures = 0
        self._max_failures_before_reconnect = 5

    @classmethod
    def from_config(
        cls, video_settings: VideoSettings, source_id: str = "default"
    ) -> OpenCVCapture:
        """
        Factory method to create OpenCVCapture from VideoSettings.

        Args:
            video_settings: Video configuration from AppSettings
            source_id: Identifier for this source

        Returns:
            OpenCVCapture instance
        """
        concrete = video_settings.source.to_concrete()
        return cls(
            source_config=concrete,
            fps_target=video_settings.fps_target,
            frame_resize=video_settings.frame_resize,
            rotate_180=video_settings.rotate_180,
            read_timeout_s=video_settings.read_timeout_s,
            reconnect_interval_s=video_settings.reconnect_interval_s,
            source_id=source_id,
        )

    def open(self) -> None:
        """Open the video capture source."""
        if self._opened:
            logger.warning("Capture already opened, skipping")
            return

        self._open_capture()
        self._opened = True
        logger.info(f"Opened {self.source_config.type} source: {self._get_source_description()}")

    def _open_capture(self) -> None:
        """Internal method to open cv2.VideoCapture based on source type."""
        if isinstance(self.source_config, DeviceSource):
            self._open_device()
        elif isinstance(self.source_config, RTSPSource):
            self._open_network(self.source_config.url)
        elif isinstance(self.source_config, HTTPMjpegSource):
            self._open_network(self.source_config.url)
        elif isinstance(self.source_config, FileSource):
            self._open_file()
        else:
            raise ValueError(f"Unknown source type: {type(self.source_config)}")

        # Validate capture opened successfully
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError(
                f"Failed to open {self.source_config.type} source: "
                f"{self._get_source_description()}"
            )

        # Test read one frame to ensure stream is working
        ret, _ = self.cap.read()
        if not ret:
            raise RuntimeError(f"Opened {self.source_config.type} source but cannot read frames")

    def _open_device(self) -> None:
        """Open device (webcam/USB camera) source."""
        device_cfg = self.source_config
        assert isinstance(device_cfg, DeviceSource)

        # Determine backend
        if device_cfg.backend:
            backend = _get_backend_enum(device_cfg.backend)
            backend_name = device_cfg.backend
        else:
            backend = _get_default_device_backend()
            backend_name = "auto-detected"

        # Retry logic for device open (sometimes needs a few attempts)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.cap = cv2.VideoCapture(device_cfg.device_index, backend)
                if self.cap.isOpened():
                    logger.info(
                        f"Device {device_cfg.device_index} opened with " f"{backend_name} backend"
                    )
                    return
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed to open device "
                    f"{device_cfg.device_index}: {e}"
                )

            if attempt < max_retries - 1:
                time.sleep(0.5)

        raise RuntimeError(
            f"Failed to open device {device_cfg.device_index} after {max_retries} attempts"
        )

    def _open_network(self, url: str) -> None:
        """Open network source (RTSP or HTTP MJPEG)."""
        # Use FFMPEG backend for network streams (most reliable)
        self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        logger.info(f"Opened network stream: {url}")

    def _open_file(self) -> None:
        """Open file source."""
        file_cfg = self.source_config
        assert isinstance(file_cfg, FileSource)

        self.cap = cv2.VideoCapture(file_cfg.url)
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Video file not found or cannot be opened: {file_cfg.url}")
        logger.info(f"Opened video file: {file_cfg.url}")

    def read(self) -> Optional[Frame]:
        """
        Read next frame from source.

        Returns:
            Frame object or None if no frame available (timeout/end)
        """
        if not self._opened or not self.cap:
            logger.error("Cannot read: capture not opened")
            return None

        # FPS control: drop frames if reading too fast
        now = time.time()
        time_since_last = now - self._last_read_time
        if time_since_last < self._frame_interval:
            # Skip this frame to maintain target FPS
            return None

        # Read frame with timeout for network sources
        if self._is_network_source():
            frame_data = self._read_with_timeout()
        else:
            ret, frame_data = self.cap.read()
            if not ret:
                frame_data = None

        # Handle read failure
        if frame_data is None:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures_before_reconnect:
                if self._is_network_source():
                    logger.warning(
                        f"Consecutive failures: {self._consecutive_failures}, "
                        "attempting reconnection"
                    )
                    self._reconnect()
                    return None
                else:
                    # File ended or device disconnected
                    logger.info(f"{self.source_config.type} source ended")
                    return None
            return None

        # Reset failure counter on successful read
        self._consecutive_failures = 0
        self._last_read_time = now

        # Preprocess frame
        processed = self._preprocess_frame(frame_data)

        # Update FPS meter
        self._fps_meter.tick()
        if self._fps_meter.ts and len(self._fps_meter.ts) % 60 == 0:
            logger.debug(f"Actual FPS: {self._fps_meter.fps():.1f}")

        # Generate timestamp
        ts_ms = int(time.time() * 1000)

        return Frame(image=processed, ts_ms=ts_ms, source_id=self.source_id)

    def _read_with_timeout(self) -> Optional[np.ndarray]:
        """Read frame with timeout (for network sources)."""
        frame_data = None
        ret = False

        def _read():
            nonlocal ret, frame_data
            ret, frame_data = self.cap.read()

        thread = threading.Thread(target=_read, daemon=True)
        thread.start()
        thread.join(timeout=self.read_timeout_s)

        if thread.is_alive():
            logger.warning(f"Frame read timeout after {self.read_timeout_s}s")
            return None

        return frame_data if ret else None

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply preprocessing: resize and rotation."""
        # Resize if configured
        if self.frame_resize:
            width, height = self.frame_resize
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

        # Rotate 180 degrees if configured
        if self.rotate_180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)

        return frame

    def _is_network_source(self) -> bool:
        """Check if source is a network source (RTSP or HTTP MJPEG)."""
        return isinstance(self.source_config, (RTSPSource, HTTPMjpegSource))

    def _reconnect(self) -> None:
        """Attempt to reconnect to network source."""
        if not self._is_network_source():
            return

        logger.info("Closing failed capture for reconnection")
        if self.cap:
            self.cap.release()
            self.cap = None

        # Exponential backoff with max
        backoff = min(self.reconnect_interval_s * (2 ** (self._consecutive_failures - 5)), 30.0)
        logger.info(f"Waiting {backoff:.1f}s before reconnection attempt")
        time.sleep(backoff)

        try:
            url = (
                self.source_config.url
                if isinstance(self.source_config, (RTSPSource, HTTPMjpegSource))
                else ""
            )
            self._open_network(url)
            self._consecutive_failures = 0
            logger.info("Reconnection successful")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self._consecutive_failures += 1

    def close(self) -> None:
        """Close the video capture and release resources."""
        if not self._opened:
            return

        if self.cap:
            self.cap.release()
            self.cap = None

        self._opened = False
        logger.info(f"Closed {self.source_config.type} source")

    def _get_source_description(self) -> str:
        """Get human-readable description of source."""
        if isinstance(self.source_config, DeviceSource):
            return f"device {self.source_config.device_index}"
        elif isinstance(self.source_config, (RTSPSource, HTTPMjpegSource, FileSource)):
            return self.source_config.url
        return "unknown"

    def __enter__(self) -> OpenCVCapture:
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def get_fps(self) -> float:
        """Get actual capture FPS from meter."""
        return self._fps_meter.fps()
