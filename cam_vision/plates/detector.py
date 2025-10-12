"""YOLOv8-based license plate detector."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np

from ..types import BBox, Detection

logger = logging.getLogger(__name__)


class YOLOPlateDetector:
    """
    YOLOv8 wrapper for license plate detection.

    Loads a pre-trained YOLOv8 model and runs inference on frames.
    Returns Detection objects with bboxes, scores, and class.
    """

    def __init__(
        self,
        model_path: str,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        max_det: int = 10,
        input_size: int = 640,
    ):
        """
        Initialize YOLOv8 detector.

        Args:
            model_path: Path to YOLOv8 model weights (.pt file)
            conf_threshold: Detection confidence threshold (0.0-1.0)
            iou_threshold: NMS IoU threshold (0.0-1.0)
            max_det: Maximum detections per frame
            input_size: Model input size (square)
        """
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_det = max_det
        self.input_size = input_size

        self.model = None
        self._stats = {"total_frames": 0, "total_detections": 0}

    def load(self) -> None:
        """Load YOLOv8 model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YOLOv8 model not found at {self.model_path}. "
                f"Download a pre-trained plate detection model and place it there."
            )

        logger.info(f"Loading YOLOv8 model from {self.model_path}")

        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise ImportError(
                "ultralytics package not installed. Run: pip install ultralytics"
            ) from e

        self.model = YOLO(str(self.model_path))
        logger.info(
            f"YOLOv8 detector ready: conf={self.conf_threshold}, "
            f"iou={self.iou_threshold}, max_det={self.max_det}"
        )

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run plate detection on a single frame.

        Args:
            frame: BGR image (H, W, 3) as numpy array

        Returns:
            List of Detection objects with kind="plate"
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        self._stats["total_frames"] += 1

        # Convert BGR to RGB (YOLOv8 expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run inference
        try:
            results = self.model.predict(
                rgb_frame,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                max_det=self.max_det,
                imgsz=self.input_size,
                verbose=False,  # Suppress YOLOv8 logging
            )
        except Exception as e:
            logger.error(f"YOLOv8 inference failed: {e}")
            return []

        # Parse results
        detections = []
        if len(results) > 0:
            result = results[0]  # Single image
            boxes = result.boxes

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    # Extract bbox coordinates (xyxy format)
                    xyxy = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                    conf = float(box.conf[0].cpu().numpy())

                    # Create BBox
                    bbox = BBox(
                        x1=int(xyxy[0]),
                        y1=int(xyxy[1]),
                        x2=int(xyxy[2]),
                        y2=int(xyxy[3]),
                    )

                    # Create Detection
                    detection = Detection(
                        kind="plate",
                        bbox=bbox,
                        score=conf,
                    )

                    detections.append(detection)

        self._stats["total_detections"] += len(detections)
        logger.debug(f"Detected {len(detections)} plates in frame")

        return detections

    def get_stats(self) -> dict:
        """Get detection statistics."""
        return self._stats.copy()

    def __repr__(self) -> str:
        return (
            f"YOLOPlateDetector(model={self.model_path.name}, "
            f"conf={self.conf_threshold}, iou={self.iou_threshold})"
        )
