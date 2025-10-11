"""Tests for OpenCV video capture."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from cam_vision.config import DeviceSource, FileSource, HTTPMjpegSource, RTSPSource, VideoSettings
from cam_vision.io.capture import OpenCVCapture, _get_backend_enum, _get_default_device_backend


class TestBackendSelection:
    """Test backend selection and mapping."""

    def test_backend_enum_mapping(self):
        """Test string to OpenCV backend enum conversion."""
        assert _get_backend_enum("AVFOUNDATION") == cv2.CAP_AVFOUNDATION
        assert _get_backend_enum("V4L2") == cv2.CAP_V4L2
        assert _get_backend_enum("DSHOW") == cv2.CAP_DSHOW
        assert _get_backend_enum("MSMF") == cv2.CAP_MSMF
        assert _get_backend_enum("FFMPEG") == cv2.CAP_FFMPEG
        assert _get_backend_enum("ANY") == cv2.CAP_ANY
        assert _get_backend_enum(None) == cv2.CAP_ANY

    def test_backend_case_insensitive(self):
        """Backend strings should be case-insensitive."""
        assert _get_backend_enum("avfoundation") == cv2.CAP_AVFOUNDATION
        assert _get_backend_enum("AvFoundation") == cv2.CAP_AVFOUNDATION

    def test_invalid_backend_raises_error(self):
        """Invalid backend should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            _get_backend_enum("INVALID_BACKEND")

    @patch("platform.system")
    def test_default_backend_macos(self, mock_system):
        """macOS should default to AVFOUNDATION."""
        mock_system.return_value = "Darwin"
        assert _get_default_device_backend() == cv2.CAP_AVFOUNDATION

    @patch("platform.system")
    def test_default_backend_linux(self, mock_system):
        """Linux should default to V4L2."""
        mock_system.return_value = "Linux"
        assert _get_default_device_backend() == cv2.CAP_V4L2

    @patch("platform.system")
    def test_default_backend_windows(self, mock_system):
        """Windows should default to DSHOW."""
        mock_system.return_value = "Windows"
        assert _get_default_device_backend() == cv2.CAP_DSHOW


class TestDeviceCapture:
    """Test device (webcam/USB) capture."""

    @patch("cv2.VideoCapture")
    def test_device_capture_opens_with_backend(self, mock_cv2_cap):
        """Device capture should open with correct backend."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=0, backend="AVFOUNDATION")
        capture = OpenCVCapture(
            source_config=device_cfg,
            fps_target=15,
        )

        capture.open()

        # Verify cv2.VideoCapture called with device index and backend
        mock_cv2_cap.assert_called_once_with(0, cv2.CAP_AVFOUNDATION)
        assert capture._opened

    @patch("cv2.VideoCapture")
    @patch("cam_vision.io.capture._get_default_device_backend")
    def test_device_capture_auto_backend(self, mock_default_backend, mock_cv2_cap):
        """Device capture should use auto-detected backend if none specified."""
        mock_default_backend.return_value = cv2.CAP_V4L2
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=1)  # No backend specified
        capture = OpenCVCapture(source_config=device_cfg, fps_target=15)

        capture.open()

        mock_cv2_cap.assert_called_once_with(1, cv2.CAP_V4L2)

    @patch("cv2.VideoCapture")
    def test_device_capture_open_failure_raises_error(self, mock_cv2_cap):
        """Device capture should raise error if open fails."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=15)

        with pytest.raises(RuntimeError, match="Failed to open device"):
            capture.open()


class TestNetworkCapture:
    """Test RTSP and HTTP MJPEG capture."""

    @patch("cv2.VideoCapture")
    def test_rtsp_capture_opens_with_url(self, mock_cv2_cap):
        """RTSP capture should open with URL and FFMPEG backend."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        rtsp_cfg = RTSPSource(url="rtsp://192.168.1.100/stream")
        capture = OpenCVCapture(source_config=rtsp_cfg, fps_target=10)

        capture.open()

        mock_cv2_cap.assert_called_once_with("rtsp://192.168.1.100/stream", cv2.CAP_FFMPEG)

    @patch("cv2.VideoCapture")
    def test_http_mjpeg_capture_opens(self, mock_cv2_cap):
        """HTTP MJPEG capture should open with URL."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        http_cfg = HTTPMjpegSource(url="http://192.168.1.50:8080/video")
        capture = OpenCVCapture(source_config=http_cfg, fps_target=10)

        capture.open()

        mock_cv2_cap.assert_called_once_with("http://192.168.1.50:8080/video", cv2.CAP_FFMPEG)


class TestFileCapture:
    """Test file capture."""

    @patch("cv2.VideoCapture")
    def test_file_capture_opens(self, mock_cv2_cap):
        """File capture should open with file path."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        file_cfg = FileSource(url="/path/to/video.mp4")
        capture = OpenCVCapture(source_config=file_cfg, fps_target=30)

        capture.open()

        mock_cv2_cap.assert_called_once_with("/path/to/video.mp4")

    @patch("cv2.VideoCapture")
    def test_file_capture_not_found_raises_error(self, mock_cv2_cap):
        """File capture should raise error if file not found."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_cv2_cap.return_value = mock_cap_instance

        file_cfg = FileSource(url="/nonexistent/video.mp4")
        capture = OpenCVCapture(source_config=file_cfg, fps_target=30)

        with pytest.raises(FileNotFoundError):
            capture.open()


class TestFrameReading:
    """Test frame reading and preprocessing."""

    @patch("cv2.VideoCapture")
    def test_read_returns_frame(self, mock_cv2_cap):
        """Read should return Frame object with correct structure."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.side_effect = [
            (True, test_image.copy()),  # First call for open validation
            (True, test_image.copy()),  # Second call for actual read
        ]
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=30)
        capture.open()

        frame = capture.read()

        assert frame is not None
        assert frame.image.shape == (480, 640, 3)
        assert isinstance(frame.ts_ms, int)
        assert frame.source_id == "default"

    @patch("cv2.VideoCapture")
    @patch("cv2.resize")
    def test_frame_resize(self, mock_resize, mock_cv2_cap):
        """Frame should be resized if configured."""
        original_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        resized_image = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.side_effect = [
            (True, original_image.copy()),
            (True, original_image.copy()),
        ]
        mock_cv2_cap.return_value = mock_cap_instance
        mock_resize.return_value = resized_image

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=30, frame_resize=(640, 480))
        capture.open()

        capture.read()
        # Verify resize was called with correct dimensions
        mock_resize.assert_called()
        # cv2.resize is called as: resize(image, (width, height), interpolation=...)
        call_args = mock_resize.call_args
        assert call_args[0][1] == (640, 480)  # Second positional arg is size tuple
        assert call_args[1]["interpolation"] == cv2.INTER_AREA

    @patch("cv2.VideoCapture")
    @patch("cv2.rotate")
    def test_frame_rotation(self, mock_rotate, mock_cv2_cap):
        """Frame should be rotated 180 degrees if configured."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.side_effect = [
            (True, test_image.copy()),
            (True, test_image.copy()),
        ]
        mock_cv2_cap.return_value = mock_cap_instance
        mock_rotate.return_value = test_image

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=30, rotate_180=True)
        capture.open()

        capture.read()
        # Verify rotate was called with ROTATE_180
        mock_rotate.assert_called_once()
        args = mock_rotate.call_args
        assert args[0][1] == cv2.ROTATE_180


class TestFPSControl:
    """Test FPS control via frame dropping."""

    @patch("cv2.VideoCapture")
    @patch("time.time")
    def test_fps_control_drops_frames(self, mock_time, mock_cv2_cap):
        """Frames should be dropped to maintain target FPS."""
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)

        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, test_image.copy())
        mock_cv2_cap.return_value = mock_cap_instance

        # Need more time values for all time.time() calls:
        # - read() checks time, generates timestamp
        # Each successful read needs 2 time calls, dropped reads need 1
        time_sequence = [
            0.0,
            0.0,
            0.0,  # First read (succeeds)
            0.05,  # Second read check (should drop)
            0.1,
            0.1,
            0.1,  # Third read (succeeds)
        ]
        mock_time.side_effect = time_sequence

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=10)  # 0.1s per frame
        capture.open()

        # First read: should succeed (time=0.0)
        frame1 = capture.read()
        assert frame1 is not None

        # Second read: should be dropped (time=0.05, too soon)
        frame2 = capture.read()
        assert frame2 is None

        # Third read: should succeed (time=0.1)
        frame3 = capture.read()
        assert frame3 is not None


class TestContextManager:
    """Test context manager functionality."""

    @patch("cv2.VideoCapture")
    def test_context_manager_opens_and_closes(self, mock_cv2_cap):
        """Context manager should open on enter and close on exit."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=15)

        with capture:
            assert capture._opened

        # After exit, should be closed
        assert not capture._opened
        mock_cap_instance.release.assert_called_once()


class TestFactoryMethod:
    """Test factory method from VideoSettings."""

    def test_from_config_creates_capture(self):
        """from_config should create OpenCVCapture from VideoSettings."""
        video_settings = VideoSettings(fps_target=20, frame_resize=(800, 600))

        capture = OpenCVCapture.from_config(video_settings, source_id="test_source")

        assert capture.fps_target == 20
        assert capture.frame_resize == (800, 600)
        assert capture.source_id == "test_source"
        assert isinstance(capture.source_config, DeviceSource)  # Default is device


class TestReconnection:
    """Test reconnection logic for network sources."""

    @patch("cv2.VideoCapture")
    @patch("time.sleep")
    def test_network_source_reconnects_on_failure(self, mock_sleep, mock_cv2_cap):
        """Network source should attempt reconnection after consecutive failures."""
        # Setup initial successful capture
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True

        # Simulate: 1 success (for open), then 5 failures, then reconnect success
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap_instance.read.side_effect = [
            (True, test_image),  # Open validation
            (False, None),  # Failure 1
            (False, None),  # Failure 2
            (False, None),  # Failure 3
            (False, None),  # Failure 4
            (False, None),  # Failure 5 - triggers reconnection
            (True, test_image),  # After reconnection
        ]

        mock_cv2_cap.return_value = mock_cap_instance

        rtsp_cfg = RTSPSource(url="rtsp://test/stream")
        capture = OpenCVCapture(source_config=rtsp_cfg, fps_target=10)
        capture.open()

        # Read frames until reconnection attempt
        for _ in range(6):
            capture.read()

        # Verify reconnection was attempted (sleep called for backoff)
        assert mock_sleep.called


class TestGracefulShutdown:
    """Test graceful shutdown and resource cleanup."""

    @patch("cv2.VideoCapture")
    def test_close_releases_resources(self, mock_cv2_cap):
        """Close should release VideoCapture resources."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=15)
        capture.open()

        capture.close()

        mock_cap_instance.release.assert_called_once()
        assert not capture._opened
        assert capture.cap is None

    @patch("cv2.VideoCapture")
    def test_double_close_safe(self, mock_cv2_cap):
        """Calling close twice should be safe."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap_instance

        device_cfg = DeviceSource(device_index=0)
        capture = OpenCVCapture(source_config=device_cfg, fps_target=15)
        capture.open()

        capture.close()
        capture.close()  # Second close should not raise error

        # Release should only be called once
        assert mock_cap_instance.release.call_count == 1
