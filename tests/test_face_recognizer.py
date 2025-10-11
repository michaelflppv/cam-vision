"""Tests for face recognizer processor."""

from __future__ import annotations

from unittest.mock import Mock, patch

import numpy as np
import pytest

from cam_vision.face.recognizer import FaceRecognizer
from cam_vision.types import Frame


@pytest.fixture
def mock_gallery():
    """Create mock gallery."""
    gallery = Mock()
    gallery._loaded = True
    gallery.size.return_value = 2
    gallery.load = Mock()
    return gallery


@pytest.fixture
def mock_models():
    """Create mock InsightFace models."""
    return Mock()


class TestFaceRecognizerLifecycle:
    """Test recognizer lifecycle (open/close)."""

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    def test_open_loads_models_and_gallery(self, mock_get_models):
        """open() should load models and gallery."""
        mock_get_models.return_value = Mock()

        # Create gallery mock that's not loaded yet
        gallery = Mock()
        gallery._loaded = False
        gallery.load = Mock()

        recognizer = FaceRecognizer(gallery=gallery)
        recognizer.open()

        # Verify models loaded
        mock_get_models.assert_called_once()

        # Verify gallery loaded
        gallery.load.assert_called_once()

        assert recognizer.models is not None

    def test_close_clears_models(self, mock_gallery):
        """close() should clear models and log stats."""
        recognizer = FaceRecognizer(gallery=mock_gallery)
        recognizer.models = Mock()  # Simulate loaded models

        recognizer.close()

        assert recognizer.models is None


class TestFaceRecognizerProcessing:
    """Test frame processing and event emission."""

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    def test_process_frame_no_faces_detected(self, mock_get_models, mock_gallery):
        """Should return empty when no faces detected."""
        mock_models = Mock()
        mock_models.get.return_value = []  # No faces

        mock_get_models.return_value = mock_models

        recognizer = FaceRecognizer(gallery=mock_gallery)
        recognizer.open()

        # Create frame
        frame = Frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            ts_ms=1000,
            source_id="test",
        )

        events = list(recognizer.process_frame(frame))

        assert len(events) == 0

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    def test_process_frame_emits_face_match_event(self, mock_get_models, mock_gallery):
        """Should emit FaceMatch event when face matched."""
        # Mock face detection
        mock_face = Mock()
        mock_face.bbox = np.array([100, 100, 200, 200])  # x1, y1, x2, y2
        mock_face.det_score = 0.95
        mock_face.embedding = np.random.rand(512).astype(np.float32)

        mock_models = Mock()
        mock_models.get.return_value = [mock_face]

        mock_get_models.return_value = mock_models

        # Mock gallery match
        mock_gallery.match.return_value = ("john_doe", 0.85)

        recognizer = FaceRecognizer(
            gallery=mock_gallery, similarity_threshold=0.35, detect_blur=False
        )
        recognizer.open()

        # Create frame
        frame = Frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            ts_ms=1000,
            source_id="test",
        )

        events = list(recognizer.process_frame(frame))

        # Verify event emitted
        assert len(events) == 1

        event = events[0]
        assert event.type == "face_match"
        assert event.payload.person_id == "john_doe"
        assert event.payload.similarity == 0.85
        assert event.payload.detection.kind == "face"
        assert event.payload.detection.score == 0.95
        assert event.ts_ms == 1000
        assert event.frame_source_id == "test"

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    def test_process_frame_filters_small_faces(self, mock_get_models, mock_gallery):
        """Should filter out faces smaller than min_face_size."""
        # Mock small face
        mock_face = Mock()
        mock_face.bbox = np.array([100, 100, 120, 120])  # 20x20 pixels
        mock_face.det_score = 0.95
        mock_face.embedding = np.random.rand(512).astype(np.float32)

        mock_models = Mock()
        mock_models.get.return_value = [mock_face]

        mock_get_models.return_value = mock_models

        recognizer = FaceRecognizer(gallery=mock_gallery, min_face_size=40)
        recognizer.open()

        frame = Frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            ts_ms=1000,
            source_id="test",
        )

        events = list(recognizer.process_frame(frame))

        # Should be filtered out
        assert len(events) == 0
        assert recognizer._stats["rejected_size"] == 1

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    @patch("cv2.cvtColor")
    @patch("cv2.Laplacian")
    def test_process_frame_filters_blurry_faces(
        self, mock_laplacian, mock_cvtcolor, mock_get_models, mock_gallery
    ):
        """Should filter out blurry faces when blur detection enabled."""
        # Mock face
        mock_face = Mock()
        mock_face.bbox = np.array([100, 100, 200, 200])
        mock_face.det_score = 0.95
        mock_face.embedding = np.random.rand(512).astype(np.float32)

        mock_models = Mock()
        mock_models.get.return_value = [mock_face]

        mock_get_models.return_value = mock_models

        # Mock blur detection (low variance = blurry)
        mock_laplacian_result = Mock()
        mock_laplacian_result.var.return_value = 50.0  # Below threshold (100)
        mock_laplacian.return_value = mock_laplacian_result

        mock_cvtcolor.return_value = np.zeros((100, 100), dtype=np.uint8)

        recognizer = FaceRecognizer(gallery=mock_gallery, detect_blur=True, blur_threshold=100.0)
        recognizer.open()

        frame = Frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            ts_ms=1000,
            source_id="test",
        )

        events = list(recognizer.process_frame(frame))

        # Should be filtered out
        assert len(events) == 0
        assert recognizer._stats["rejected_blur"] == 1

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    def test_process_frame_no_match_below_threshold(self, mock_get_models, mock_gallery):
        """Should not emit event when similarity below threshold."""
        # Mock face
        mock_face = Mock()
        mock_face.bbox = np.array([100, 100, 200, 200])
        mock_face.det_score = 0.95
        mock_face.embedding = np.random.rand(512).astype(np.float32)

        mock_models = Mock()
        mock_models.get.return_value = [mock_face]

        mock_get_models.return_value = mock_models

        # Mock gallery returns None (no match above threshold)
        mock_gallery.match.return_value = None

        recognizer = FaceRecognizer(
            gallery=mock_gallery, similarity_threshold=0.35, detect_blur=False
        )
        recognizer.open()

        frame = Frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            ts_ms=1000,
            source_id="test",
        )

        events = list(recognizer.process_frame(frame))

        assert len(events) == 0
        assert recognizer._stats["rejected_threshold"] == 1


class TestFaceRecognizerStatistics:
    """Test statistics tracking."""

    @patch("cam_vision.face.recognizer.FaceModels.get_models")
    def test_statistics_tracking(self, mock_get_models, mock_gallery):
        """Should track statistics correctly."""
        # Process 2 frames with mixed results
        mock_models = Mock()

        # Frame 1: 1 match, 1 too small
        mock_face_matched = Mock()
        mock_face_matched.bbox = np.array([100, 100, 200, 200])
        mock_face_matched.det_score = 0.95
        mock_face_matched.embedding = np.random.rand(512).astype(np.float32)

        mock_face_small = Mock()
        mock_face_small.bbox = np.array([10, 10, 30, 30])  # Too small
        mock_face_small.det_score = 0.90
        mock_face_small.embedding = np.random.rand(512).astype(np.float32)

        mock_models.get.return_value = [mock_face_matched, mock_face_small]

        mock_get_models.return_value = mock_models

        # Mock gallery match
        mock_gallery.match.return_value = ("john", 0.85)

        recognizer = FaceRecognizer(gallery=mock_gallery, min_face_size=40, detect_blur=False)
        recognizer.open()

        frame = Frame(
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            ts_ms=1000,
            source_id="test",
        )

        list(recognizer.process_frame(frame))

        # Check stats
        stats = recognizer.get_stats()
        assert stats["total_frames"] == 1
        assert stats["total_detections"] == 2
        assert stats["matched"] == 1
        assert stats["rejected_size"] == 1


class TestFaceRecognizerFactoryMethod:
    """Test factory method from config."""

    def test_from_config(self, mock_gallery):
        """Should create recognizer from FaceSettings."""
        from cam_vision.config import FaceSettings

        face_settings = FaceSettings(
            similarity_threshold=0.45,
            min_face_size=50,
        )

        recognizer = FaceRecognizer.from_config(face_settings, mock_gallery)

        assert recognizer.gallery == mock_gallery
        assert recognizer.similarity_threshold == 0.45
        assert recognizer.min_face_size == 50
