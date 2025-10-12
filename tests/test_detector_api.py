"""Integration tests for YOLOv8 detector API (smoke tests)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from cam_vision.plates.detector import YOLOPlateDetector


@pytest.fixture
def model_path() -> Path:
    """Get path to YOLOv8 model weights (if present)."""
    return Path("./weights/yolov8n_plate.pt")


@pytest.fixture
def detector(model_path: Path) -> YOLOPlateDetector:
    """Create detector instance."""
    return YOLOPlateDetector(
        model_path=str(model_path),
        conf_threshold=0.25,
        iou_threshold=0.45,
        max_det=10,
    )


class TestYOLOPlateDetectorAPI:
    """Test YOLOv8 detector API (without requiring actual model)."""

    def test_detector_initialization(self, detector: YOLOPlateDetector):
        """Test detector can be initialized with config."""
        assert detector.model_path.name == "yolov8n_plate.pt"
        assert detector.conf_threshold == 0.25
        assert detector.iou_threshold == 0.45
        assert detector.max_det == 10
        assert detector.model is None  # Not loaded yet

    def test_detector_repr(self, detector: YOLOPlateDetector):
        """Test string representation."""
        repr_str = repr(detector)
        assert "YOLOPlateDetector" in repr_str
        assert "yolov8n_plate.pt" in repr_str
        assert "conf=0.25" in repr_str

    def test_load_fails_if_model_missing(self, tmp_path):
        """Test that load() raises FileNotFoundError if model not present."""
        fake_path = tmp_path / "nonexistent.pt"
        detector = YOLOPlateDetector(model_path=str(fake_path))

        with pytest.raises(FileNotFoundError, match="YOLOv8 model not found"):
            detector.load()

    def test_detect_fails_if_not_loaded(self, detector: YOLOPlateDetector):
        """Test that detect() raises error if model not loaded."""
        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.detect(frame)

    def test_stats_initialization(self, detector: YOLOPlateDetector):
        """Test that stats are initialized correctly."""
        stats = detector.get_stats()
        assert stats["total_frames"] == 0
        assert stats["total_detections"] == 0


@pytest.mark.skipif(
    not Path("./weights/yolov8n_plate.pt").exists(),
    reason="YOLOv8 model weights not present at ./weights/yolov8n_plate.pt",
)
class TestYOLOPlateDetectorWithModel:
    """Integration tests that require actual model weights (skipped if not present)."""

    def test_load_model_succeeds(self, detector: YOLOPlateDetector):
        """Test that model loads successfully if present."""
        detector.load()
        assert detector.model is not None

    def test_detect_on_blank_frame(self, detector: YOLOPlateDetector):
        """Test detection on a blank frame (should return empty list)."""
        detector.load()

        # Create blank frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        detections = detector.detect(frame)

        # Blank frame should have no detections
        assert isinstance(detections, list)
        assert len(detections) == 0

    def test_detect_on_noise_frame(self, detector: YOLOPlateDetector):
        """Test detection on random noise (should return empty or very few detections)."""
        detector.load()

        # Create random noise frame
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

        detections = detector.detect(frame)

        # Noise should typically have no valid detections
        assert isinstance(detections, list)
        # May have false positives, but should be < max_det
        assert len(detections) <= detector.max_det

    def test_stats_update_after_detection(self, detector: YOLOPlateDetector):
        """Test that stats are updated after detection calls."""
        detector.load()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Initial stats
        initial_stats = detector.get_stats()
        assert initial_stats["total_frames"] == 0

        # Run detection
        detector.detect(frame)

        # Stats should update
        updated_stats = detector.get_stats()
        assert updated_stats["total_frames"] == 1

    def test_multiple_detections_update_stats(self, detector: YOLOPlateDetector):
        """Test stats across multiple detection calls."""
        detector.load()

        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Run 5 detections
        for _ in range(5):
            detector.detect(frame)

        stats = detector.get_stats()
        assert stats["total_frames"] == 5

    def test_detection_returns_correct_format(self, detector: YOLOPlateDetector):
        """Test that detections have correct structure if any are returned."""
        detector.load()

        # Create a more realistic frame (still likely no detections)
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)

        detections = detector.detect(frame)

        # If any detections (unlikely with gray frame), verify structure
        for detection in detections:
            assert detection.kind == "plate"
            assert hasattr(detection, "bbox")
            assert hasattr(detection, "score")
            assert 0.0 <= detection.score <= 1.0
            assert detection.bbox.width() > 0
            assert detection.bbox.height() > 0


class TestDetectorConfiguration:
    """Test various detector configurations."""

    def test_custom_thresholds(self):
        """Test detector with custom confidence/IOU thresholds."""
        detector = YOLOPlateDetector(
            model_path="./weights/yolov8n_plate.pt",
            conf_threshold=0.5,
            iou_threshold=0.7,
            max_det=5,
        )

        assert detector.conf_threshold == 0.5
        assert detector.iou_threshold == 0.7
        assert detector.max_det == 5

    def test_custom_input_size(self):
        """Test detector with custom input size."""
        detector = YOLOPlateDetector(
            model_path="./weights/yolov8n_plate.pt",
            input_size=416,
        )

        assert detector.input_size == 416
