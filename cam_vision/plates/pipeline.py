"""License plate recognition processor (YOLOv8 + Tesseract)."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Iterable, List

from ..pipeline.base import Processor
from ..types import Event, Frame, PlateObservation, PlateRead
from .detector import YOLOPlateDetector
from .lists import PlateListLoader
from .ocr import TesseractOCR

logger = logging.getLogger(__name__)


class PlateRecognizer(Processor):
    """
    License plate recognition processor using YOLOv8 + Tesseract.

    Pipeline:
    1. Detect plates in frame (YOLOv8)
    2. Apply quality gates (aspect ratio, size)
    3. Extract text via OCR (Tesseract with preprocessing)
    4. Match against whitelist/blacklist
    5. Emit PlateRead events

    Note: This processor is stateless per CLAUDE.md guidance.
          Multi-frame confirmation should be in Sink layer (PR8).
    """

    def __init__(
        self,
        detector: YOLOPlateDetector,
        ocr: TesseractOCR,
        lists: PlateListLoader,
        min_confidence: float = 0.55,
        min_aspect_ratio: float = 1.5,
        max_aspect_ratio: float = 6.0,
        min_width_px: int = 80,
        min_height_px: int = 20,
    ):
        """
        Initialize plate recognizer.

        Args:
            detector: YOLOv8 detector instance
            ocr: Tesseract OCR instance
            lists: Plate list loader for whitelist/blacklist
            min_confidence: Minimum overall confidence threshold (0.0-1.0)
            min_aspect_ratio: Minimum plate aspect ratio (width/height)
            max_aspect_ratio: Maximum plate aspect ratio
            min_width_px: Minimum plate width in pixels
            min_height_px: Minimum plate height in pixels
        """
        self.detector = detector
        self.ocr = ocr
        self.lists = lists
        self.min_confidence = min_confidence
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.min_width_px = min_width_px
        self.min_height_px = min_height_px

        self._stats = {
            "total_frames": 0,
            "total_detections": 0,
            "rejected_aspect_ratio": 0,
            "rejected_size": 0,
            "rejected_ocr_confidence": 0,
            "rejected_text_length": 0,
            "successful_reads": 0,
            "whitelist_matches": 0,
            "blacklist_matches": 0,
            "ocr_errors": 0,
        }
        self._latest_observations: List[PlateObservation] = []

    def open(self) -> None:
        """Load detector, OCR, and lists."""
        logger.info(
            f"Opening PlateRecognizer (conf_threshold={self.min_confidence}, "
            f"aspect_ratio={self.min_aspect_ratio}-{self.max_aspect_ratio})"
        )

        # Load components
        self.detector.load()
        self.ocr.load()
        self.lists.load()

        self._latest_observations = []

        logger.info(
            f"PlateRecognizer ready: {self.lists.size()} plates in lists, "
            f"detector={self.detector}, ocr={self.ocr}"
        )

    def process_frame(self, frame: Frame) -> Iterable[Event]:
        """
        Process frame and emit PlateRead events.

        Args:
            frame: Input frame with BGR image

        Yields:
            Event with PlateRead payload for each recognized plate
        """
        self._stats["total_frames"] += 1

        observations: List[PlateObservation] = []

        # Step 1: Detect plates
        try:
            detections = self.detector.detect(frame.image)
        except Exception as e:
            logger.error(f"Plate detection failed: {e}")
            self._latest_observations = []
            return

        if len(detections) == 0:
            logger.debug(f"No plates detected in frame {frame.ts_ms}")
            self._latest_observations = []
            return

        self._stats["total_detections"] += len(detections)

        # Step 2: Process each detected plate
        for detection in detections:
            bbox = detection.bbox

            # Quality gate: aspect ratio
            width, height = bbox.width(), bbox.height()
            aspect_ratio = width / height if height > 0 else 0

            if not (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio):
                self._stats["rejected_aspect_ratio"] += 1
                logger.debug(
                    f"Plate rejected: aspect ratio {aspect_ratio:.2f} "
                    f"not in range [{self.min_aspect_ratio}, {self.max_aspect_ratio}]"
                )
                observations.append(
                    PlateObservation(
                        detection=detection,
                        status="rejected_aspect_ratio",
                        reason=(
                            f"aspect {aspect_ratio:.2f} outside "
                            f"[{self.min_aspect_ratio}, {self.max_aspect_ratio}]"
                        ),
                    )
                )
                continue

            # Quality gate: minimum size with soft allowance for adaptive upscale
            if width < self.min_width_px or height < self.min_height_px:
                soft_width = self.min_width_px * 0.6
                soft_height = self.min_height_px * 0.6
                if width < soft_width or height < soft_height:
                    self._stats["rejected_size"] += 1
                    logger.debug(
                        f"Plate rejected: size {width}x{height}px too small "
                        f"(min={self.min_width_px}x{self.min_height_px}px)"
                    )
                    observations.append(
                        PlateObservation(
                            detection=detection,
                            status="rejected_size",
                            reason=(
                                f"size {width}x{height}px < "
                                f"{self.min_width_px}x{self.min_height_px}px"
                            ),
                        )
                    )
                    continue
                logger.debug(
                    "Plate size %sx%s below preferred threshold but within soft margin, "
                    "attempting OCR with adaptive upscale.",
                    width,
                    height,
                )

            # Step 3: OCR
            try:
                ocr_result = self.ocr.extract_text(frame.image, bbox)
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
                self._stats["ocr_errors"] += 1
                observations.append(
                    PlateObservation(
                        detection=detection,
                        status="ocr_error",
                        reason=str(e),
                    )
                )
                continue

            # Quality gate: OCR confidence
            # Convert OCR confidence (0-100) to 0-1 scale for comparison
            ocr_conf_normalized = ocr_result.confidence / 100.0

            base_observation = PlateObservation(
                detection=detection,
                text_raw=ocr_result.text_raw,
                text_clean=ocr_result.text_clean,
                confidence=ocr_result.confidence,
                preprocessing_used=ocr_result.preprocessing_used,
            )

            if ocr_conf_normalized < self.min_confidence:
                self._stats["rejected_ocr_confidence"] += 1
                logger.debug(
                    f"Plate rejected: OCR confidence {ocr_result.confidence:.1f}% "
                    f"below threshold {self.min_confidence*100:.1f}%"
                )
                observations.append(
                    replace(
                        base_observation,
                        status="ocr_low_confidence",
                        reason=(
                            f"confidence {ocr_result.confidence:.1f}% < "
                            f"{self.min_confidence*100:.1f}%"
                        ),
                    )
                )
                continue

            # Quality gate: minimum text length
            if len(ocr_result.text_clean) < self.ocr.min_text_length:
                self._stats["rejected_text_length"] += 1
                logger.debug(
                    f"Plate rejected: text '{ocr_result.text_clean}' too short "
                    f"(min={self.ocr.min_text_length})"
                )
                observations.append(
                    replace(
                        base_observation,
                        status="ocr_short_text",
                        reason=(
                            f"length {len(ocr_result.text_clean)} < " f"{self.ocr.min_text_length}"
                        ),
                    )
                )
                continue

            # Step 4: Match against whitelist/blacklist
            matched_list = self.lists.match(ocr_result.text_clean)
            if matched_list == "whitelist":
                self._stats["whitelist_matches"] += 1
            elif matched_list == "blacklist":
                self._stats["blacklist_matches"] += 1

            # Step 5: Create PlateRead
            self._stats["successful_reads"] += 1

            plate_read = PlateRead(
                text_raw=ocr_result.text_raw,
                text_clean=ocr_result.text_clean,
                confidence=ocr_result.confidence,
                detection=detection,
                matched_list=matched_list,
                preprocessing_used=ocr_result.preprocessing_used,
            )

            observations.append(
                replace(
                    base_observation,
                    status="read",
                    matched_list=matched_list,
                )
            )

            # Step 6: Emit Event
            event = Event(
                type="plate_read",
                payload=plate_read,
                ts_ms=frame.ts_ms,
                frame_source_id=frame.source_id,
            )

            logger.info(
                f"Plate read: '{ocr_result.text_clean}' "
                f"(raw='{ocr_result.text_raw}', conf={ocr_result.confidence:.1f}%, "
                f"det_score={detection.score:.3f}, list={matched_list or 'none'})"
            )

            yield event

        self._latest_observations = observations

    def get_latest_observations(self) -> List[PlateObservation]:
        """Return plate detections (including pending OCR) from the latest processed frame."""
        return list(self._latest_observations)

    def close(self) -> None:
        """Clean up resources and log statistics."""
        logger.info("Closing PlateRecognizer")
        logger.info(f"Statistics: {self._format_stats()}")
        self._latest_observations = []

    def _format_stats(self) -> str:
        """Format statistics as human-readable string."""
        stats = self._stats
        total_det = stats["total_detections"]

        if total_det == 0:
            return "No plates detected"

        successful = stats["successful_reads"]
        reject_ar = stats["rejected_aspect_ratio"]
        reject_size = stats["rejected_size"]
        reject_conf = stats["rejected_ocr_confidence"]
        reject_len = stats["rejected_text_length"]
        wl = stats["whitelist_matches"]
        bl = stats["blacklist_matches"]
        ocr_errors = stats["ocr_errors"]

        return (
            f"frames={stats['total_frames']}, "
            f"detections={total_det}, "
            f"successful={successful} ({100*successful/total_det:.1f}%), "
            f"rejected: aspect_ratio={reject_ar}, size={reject_size}, "
            f"conf={reject_conf}, length={reject_len}, ocr_errors={ocr_errors}, "
            f"matches: whitelist={wl}, blacklist={bl}"
        )

    def get_stats(self) -> dict:
        """Get statistics dictionary."""
        return self._stats.copy()

    @classmethod
    def from_config(
        cls,
        plates_settings,
        detector: YOLOPlateDetector,
        ocr: TesseractOCR,
        lists: PlateListLoader,
    ) -> PlateRecognizer:
        """
        Factory method to create PlateRecognizer from PlatesSettings.

        Args:
            plates_settings: PlatesSettings from AppSettings
            detector: Initialized YOLOPlateDetector
            ocr: Initialized TesseractOCR
            lists: Initialized PlateListLoader

        Returns:
            PlateRecognizer instance
        """
        return cls(
            detector=detector,
            ocr=ocr,
            lists=lists,
            min_confidence=plates_settings.min_confidence,
            min_aspect_ratio=plates_settings.min_aspect_ratio,
            max_aspect_ratio=plates_settings.max_aspect_ratio,
            min_width_px=plates_settings.min_width_px,
            min_height_px=plates_settings.min_height_px,
        )
