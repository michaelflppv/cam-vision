"""Tesseract OCR with optimized preprocessing for license plates."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Dict, Tuple

import cv2
import numpy as np

from ..types import BBox

ENABLE_ALL_PREPROCESSING: Dict[str, bool] = {
    "enable_grayscale": True,
    "enable_bilateral": True,
    "enable_adaptive_threshold": True,
    "enable_clahe": True,
}

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR result with raw text, cleaned text, and confidence."""

    text_raw: str
    text_clean: str
    confidence: float  # 0.0-100.0
    preprocessing_used: str


class TesseractOCR:
    """
    Tesseract OCR wrapper with optimized preprocessing for license plates.

    Preprocessing pipeline (configurable):
    1. Crop plate region with margin
    2. Grayscale conversion (recommended, always on by default)
    3. Optional: Bilateral filter (good for noise, adds overhead)
    4. Optional: Adaptive thresholding (good for uneven lighting)
    5. Optional: CLAHE (research shows minimal benefit, disabled by default)

    Post-processing:
    - Uppercase conversion
    - Whitespace removal
    - Optional: O→0, I→1 substitutions
    - Regex cleaning (keep only whitelisted chars)
    """

    def __init__(
        self,
        tesseract_lang: str = "eng",
        psm_mode: int = 7,
        oem_mode: int = 3,
        char_whitelist: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ",
        crop_margin_px: int = 8,
        enable_grayscale: bool = True,
        enable_bilateral: bool = False,
        bilateral_d: int = 9,
        bilateral_sigma_color: int = 75,
        bilateral_sigma_space: int = 75,
        enable_adaptive_threshold: bool = False,
        adaptive_block_size: int = 11,
        adaptive_c: int = 2,
        enable_clahe: bool = False,
        clahe_clip_limit: float = 2.0,
        clahe_tile_size: int = 8,
        to_uppercase: bool = True,
        strip_whitespace: bool = True,
        min_text_length: int = 3,
        substitute_o_to_0: bool = False,
        substitute_i_to_1: bool = False,
    ):
        """Initialize Tesseract OCR with preprocessing configuration."""
        self.tesseract_lang = tesseract_lang
        self.psm_mode = psm_mode
        self.oem_mode = oem_mode
        self.char_whitelist = char_whitelist
        self.crop_margin_px = crop_margin_px
        self.enable_grayscale = enable_grayscale
        self.enable_bilateral = enable_bilateral
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space
        self.enable_adaptive_threshold = enable_adaptive_threshold
        self.adaptive_block_size = adaptive_block_size
        self.adaptive_c = adaptive_c
        self.enable_clahe = enable_clahe
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_size = clahe_tile_size
        self.to_uppercase = to_uppercase
        self.strip_whitespace = strip_whitespace
        self.min_text_length = min_text_length
        self.substitute_o_to_0 = substitute_o_to_0
        self.substitute_i_to_1 = substitute_i_to_1

        self._pytesseract = None
        self._stats = {"total_ocr_calls": 0, "successful_reads": 0, "empty_reads": 0}

    def load(self) -> None:
        """Check if pytesseract is available."""
        try:
            import pytesseract

            tesseract_cmd = os.getenv("SECUREVISION__TESSERACT_CMD")
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

            self._pytesseract = pytesseract
        except ImportError as e:
            raise ImportError(
                "pytesseract not installed. Run: pip install pytesseract\n"
                "Also ensure tesseract-ocr is installed on your system:\n"
                "  Ubuntu/Debian: sudo apt-get install tesseract-ocr\n"
                "  macOS: brew install tesseract"
            ) from e

        logger.info(
            f"TesseractOCR ready: lang={self.tesseract_lang}, psm={self.psm_mode}, "
            f"preprocessing={self._get_preprocessing_pipeline()}"
        )

    def extract_text(self, frame: np.ndarray, bbox: BBox) -> OCRResult:
        """
        Extract text from a plate region in the frame.

        Args:
            frame: BGR image (H, W, 3)
            bbox: Bounding box of the plate

        Returns:
            OCRResult with raw text, cleaned text, confidence
        """
        if self._pytesseract is None:
            raise RuntimeError("OCR not loaded. Call load() first.")

        self._stats["total_ocr_calls"] += 1

        # Step 1: Crop plate region with margin
        plate_crop = self._crop_with_margin(frame, bbox)

        overrides, adaptive_notes = self._determine_adaptive_overrides(plate_crop)
        results: list[OCRResult] = []

        # First pass with adaptive overrides
        results.append(self._ocr_with_overrides(plate_crop, overrides, adaptive_notes))

        base_result = results[0]
        needs_fallback = (
            base_result.confidence < 40.0 or len(base_result.text_clean) < self.min_text_length
        )

        if needs_fallback:
            for fallback_overrides, fallback_notes in self._generate_fallback_variants(overrides):
                results.append(
                    self._ocr_with_overrides(plate_crop, fallback_overrides, fallback_notes)
                )

        best_result = self._select_best_result(results)

        if len(best_result.text_clean) >= self.min_text_length:
            self._stats["successful_reads"] += 1
        else:
            self._stats["empty_reads"] += 1

        return best_result

    def _crop_with_margin(self, frame: np.ndarray, bbox: BBox) -> np.ndarray:
        """Crop plate region with padding to avoid cutting characters."""
        h, w = frame.shape[:2]

        # Add margin
        x1 = max(0, bbox.x1 - self.crop_margin_px)
        y1 = max(0, bbox.y1 - self.crop_margin_px)
        x2 = min(w, bbox.x2 + self.crop_margin_px)
        y2 = min(h, bbox.y2 + self.crop_margin_px)

        return frame[y1:y2, x1:x2]

    def _preprocess(
        self, plate_crop: np.ndarray, overrides: Dict[str, bool] | None = None
    ) -> Tuple[np.ndarray, str]:
        """
        Apply preprocessing pipeline to plate crop.

        Returns:
            (preprocessed_image, pipeline_steps_used)
        """
        img = plate_crop.copy()
        pipeline_steps = []
        flags = overrides or {}

        enable_grayscale = flags.get("enable_grayscale", self.enable_grayscale)
        enable_bilateral = flags.get("enable_bilateral", self.enable_bilateral)
        enable_adaptive_threshold = flags.get(
            "enable_adaptive_threshold", self.enable_adaptive_threshold
        )
        enable_clahe = flags.get("enable_clahe", self.enable_clahe)

        # 1. Grayscale conversion (recommended)
        if enable_grayscale:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            pipeline_steps.append("grayscale")

        # 2. Bilateral filter (optional, for noise)
        if enable_bilateral:
            img = cv2.bilateralFilter(
                img, self.bilateral_d, self.bilateral_sigma_color, self.bilateral_sigma_space
            )
            pipeline_steps.append("bilateral")

        # 3. Adaptive thresholding (optional, for uneven lighting)
        if enable_adaptive_threshold:
            # Ensure grayscale
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            img = cv2.adaptiveThreshold(
                img,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                self.adaptive_block_size,
                self.adaptive_c,
            )
            pipeline_steps.append("adaptive_threshold")

        # 4. CLAHE (optional, research shows minimal benefit)
        if enable_clahe:
            # Ensure grayscale
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            clahe = cv2.createCLAHE(
                clipLimit=self.clahe_clip_limit,
                tileGridSize=(self.clahe_tile_size, self.clahe_tile_size),
            )
            img = clahe.apply(img)
            pipeline_steps.append("clahe")

        pipeline_str = ",".join(pipeline_steps) if pipeline_steps else "none"
        return img, pipeline_str

    def _run_tesseract(self, preprocessed: np.ndarray) -> Tuple[str, float]:
        """
        Run Tesseract OCR on preprocessed image.

        Returns:
            (raw_text, confidence)
        """
        # Build Tesseract config
        config = (
            f"--psm {self.psm_mode} "
            f"--oem {self.oem_mode} "
            f"-c tessedit_char_whitelist={self.char_whitelist}"
        )

        try:
            # Get text with language support
            text = self._pytesseract.image_to_string(
                preprocessed, lang=self.tesseract_lang, config=config
            )

            # Get confidence (average character confidence)
            data = self._pytesseract.image_to_data(
                preprocessed,
                lang=self.tesseract_lang,
                config=config,
                output_type=self._pytesseract.Output.DICT,
            )
            confidences = [float(conf) for conf in data["conf"] if conf != -1 and str(conf) != "-1"]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            text = ""
            avg_conf = 0.0

        return text.strip(), avg_conf

    def _clean_text(self, raw_text: str) -> str:
        """
        Post-process OCR text.

        Steps:
        1. Strip whitespace (optional)
        2. Uppercase (optional)
        3. Character substitutions (O→0, I→1)
        4. Regex: keep only whitelisted characters
        """
        text = raw_text

        if self.strip_whitespace:
            text = text.replace(" ", "").replace("\t", "").replace("\n", "")

        if self.to_uppercase:
            text = text.upper()

        # Normalize accented and Cyrillic characters to Latin equivalents
        text = self._normalize_characters(text)

        # Character substitutions (common OCR errors)
        if self.substitute_o_to_0:
            text = text.replace("O", "0")

        if self.substitute_i_to_1:
            text = text.replace("I", "1")

        # Regex: keep only whitelisted characters
        allowed_pattern = re.escape(self.char_whitelist)
        text = re.sub(f"[^{allowed_pattern}]", "", text)

        return text

    def _ocr_with_overrides(
        self, plate_crop: np.ndarray, overrides: Dict[str, bool | float], notes: list[str]
    ) -> OCRResult:
        """Run OCR with the provided preprocessing overrides."""
        local_overrides: Dict[str, bool | float] = dict(overrides)
        working = plate_crop.copy()

        upscale_factor = float(local_overrides.pop("upscale_factor", 1.0))
        if upscale_factor > 1.0:
            working = cv2.resize(
                working,
                None,
                fx=upscale_factor,
                fy=upscale_factor,
                interpolation=cv2.INTER_CUBIC,
            )

        bool_overrides = {k: v for k, v in local_overrides.items() if isinstance(v, bool)}

        preprocessed, pipeline_used = self._preprocess(working, bool_overrides)

        if local_overrides.get("invert", False):
            preprocessed = cv2.bitwise_not(preprocessed)
            pipeline_used = f"{pipeline_used}+invert" if pipeline_used != "none" else "invert"

        if local_overrides.get("morph_open", False):
            kernel = np.ones((3, 3), np.uint8)
            preprocessed = cv2.morphologyEx(preprocessed, cv2.MORPH_OPEN, kernel)
            pipeline_used = (
                f"{pipeline_used}+morph_open" if pipeline_used != "none" else "morph_open"
            )

        if notes:
            adaptive_info = ",".join(notes)
            pipeline_used = (
                adaptive_info if pipeline_used == "none" else f"{pipeline_used}+{adaptive_info}"
            )

        text_raw, confidence = self._run_tesseract(preprocessed)
        text_clean = self._clean_text(text_raw)

        return OCRResult(
            text_raw=text_raw,
            text_clean=text_clean,
            confidence=confidence,
            preprocessing_used=pipeline_used,
        )

    def _determine_adaptive_overrides(
        self, plate_crop: np.ndarray
    ) -> Tuple[Dict[str, bool | float], list[str]]:
        """Derive preprocessing overrides based on plate crop characteristics."""
        overrides: Dict[str, bool | float] = {}
        notes: list[str] = []

        height, width = plate_crop.shape[:2]
        min_dim = max(1, min(height, width))

        target_min_dim = 110
        if min_dim < target_min_dim:
            scale = min(3.0, max(1.5, target_min_dim / min_dim))
            overrides["upscale_factor"] = scale
            notes.append("auto_upscale")

        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        mean_intensity = float(np.mean(gray))
        std_intensity = float(np.std(gray))

        if mean_intensity < 110 or mean_intensity > 200:
            overrides["enable_adaptive_threshold"] = True
            overrides["enable_grayscale"] = True
            notes.append("auto_threshold")

        if std_intensity < 25:
            overrides["enable_clahe"] = True
            overrides["enable_grayscale"] = True
            notes.append("auto_clahe")

        if 25 <= std_intensity <= 55:
            overrides["enable_bilateral"] = True
            notes.append("auto_bilateral")
        elif std_intensity > 65:
            overrides["enable_bilateral"] = False

        return overrides, notes

    def _generate_fallback_variants(
        self, base_overrides: Dict[str, bool | float]
    ) -> list[Tuple[Dict[str, bool | float], list[str]]]:
        """Return fallback preprocessing combinations for challenging plates."""
        variants: list[Tuple[Dict[str, bool | float], list[str]]] = []

        aggressive_threshold = dict(base_overrides)
        aggressive_threshold.update(ENABLE_ALL_PREPROCESSING)
        variants.append((aggressive_threshold, ["fallback_threshold"]))

        inverted_high_contrast = dict(base_overrides)
        inverted_high_contrast.update(ENABLE_ALL_PREPROCESSING)
        inverted_high_contrast["invert"] = True
        variants.append((inverted_high_contrast, ["fallback_invert"]))

        morph_cleanup = dict(base_overrides)
        morph_cleanup.update(ENABLE_ALL_PREPROCESSING)
        morph_cleanup["morph_open"] = True
        variants.append((morph_cleanup, ["fallback_morph"]))

        return variants

    def _select_best_result(self, results: list[OCRResult]) -> OCRResult:
        """Choose the best OCR result by confidence then text length."""
        if not results:
            return OCRResult("", "", 0.0, "none")

        def _score(res: OCRResult) -> Tuple[float, int]:
            return res.confidence, len(res.text_clean)

        return max(results, key=_score)

    def _normalize_characters(self, text: str) -> str:
        """Normalize accented and Cyrillic characters for consistent post-processing."""
        replacements = {
            "Ä": "A",
            "Å": "A",
            "Æ": "AE",
            "Ç": "C",
            "È": "E",
            "É": "E",
            "Ê": "E",
            "Ë": "E",
            "Ö": "O",
            "Ø": "O",
            "Ó": "O",
            "Ò": "O",
            "Ô": "O",
            "Õ": "O",
            "Ü": "U",
            "Ú": "U",
            "Ű": "U",
            "Ł": "L",
            "Š": "S",
            "Ś": "S",
            "Ž": "Z",
            "Ż": "Z",
            "Ź": "Z",
            "Č": "C",
            "Ć": "C",
            "Ñ": "N",
            "·": "",
        }

        for original, replacement in replacements.items():
            text = text.replace(original, replacement)

        cyrillic_map = {
            "А": "A",
            "В": "B",
            "Е": "E",
            "К": "K",
            "М": "M",
            "Н": "H",
            "О": "O",
            "Р": "P",
            "С": "C",
            "Т": "T",
            "У": "Y",
            "Х": "X",
            "Ё": "E",
        }

        for original, replacement in cyrillic_map.items():
            text = text.replace(original, replacement)

        return text

    def _get_preprocessing_pipeline(self) -> str:
        """Get human-readable preprocessing pipeline description."""
        steps = []
        if self.enable_grayscale:
            steps.append("grayscale")
        if self.enable_bilateral:
            steps.append("bilateral")
        if self.enable_adaptive_threshold:
            steps.append("adaptive")
        if self.enable_clahe:
            steps.append("clahe")

        return ",".join(steps) if steps else "none"

    def get_stats(self) -> dict:
        """Get OCR statistics."""
        return self._stats.copy()

    def __repr__(self) -> str:
        return (
            f"TesseractOCR(psm={self.psm_mode}, "
            f"preprocessing={self._get_preprocessing_pipeline()})"
        )
