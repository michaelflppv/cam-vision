"""System diagnostics for SecureVision features."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FeatureStatus:
    """Status of a feature component."""

    name: str
    enabled: bool
    available: bool
    error: Optional[str] = None
    details: Optional[str] = None


@dataclass
class SystemDiagnostics:
    """Complete system diagnostics."""

    face_recognition: FeatureStatus
    plate_detection: FeatureStatus
    insightface_models: FeatureStatus
    yolo_model: FeatureStatus
    tesseract: FeatureStatus
    gallery: FeatureStatus

    def all_ok(self) -> bool:
        """Check if all enabled features are available."""
        statuses = [
            self.face_recognition,
            self.plate_detection,
            self.insightface_models,
            self.yolo_model,
            self.tesseract,
            self.gallery,
        ]
        return all(s.available or not s.enabled for s in statuses if s.name != "System Check")

    def get_failures(self) -> list[FeatureStatus]:
        """Get list of enabled features that are not available."""
        statuses = [
            self.face_recognition,
            self.plate_detection,
            self.insightface_models,
            self.yolo_model,
            self.tesseract,
            self.gallery,
        ]
        return [s for s in statuses if s.enabled and not s.available]


def run_diagnostics(settings=None) -> SystemDiagnostics:
    """
    Run comprehensive system diagnostics.

    Args:
        settings: AppSettings instance (will load from env if None)

    Returns:
        SystemDiagnostics with status of all features
    """
    if settings is None:
        try:
            from cam_vision.config import load_settings

            settings = load_settings()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            # Return minimal diagnostics
            return SystemDiagnostics(
                face_recognition=FeatureStatus(
                    name="Face Recognition",
                    enabled=False,
                    available=False,
                    error=f"Config load failed: {e}",
                ),
                plate_detection=FeatureStatus(
                    name="Plate Detection", enabled=False, available=False
                ),
                insightface_models=FeatureStatus(
                    name="InsightFace Models", enabled=False, available=False
                ),
                yolo_model=FeatureStatus(name="YOLO Model", enabled=False, available=False),
                tesseract=FeatureStatus(name="Tesseract OCR", enabled=False, available=False),
                gallery=FeatureStatus(name="Face Gallery", enabled=False, available=False),
            )

    # Check face recognition
    face_status = _check_face_recognition(settings)

    # Check plate detection
    plate_status = _check_plate_detection(settings)

    # Check InsightFace models (only if face enabled)
    insightface_status = _check_insightface_models(settings)

    # Check YOLO model (only if plates enabled)
    yolo_status = _check_yolo_model(settings)

    # Check Tesseract (only if plates enabled)
    tesseract_status = _check_tesseract(settings)

    # Check gallery (only if face enabled)
    gallery_status = _check_gallery(settings)

    return SystemDiagnostics(
        face_recognition=face_status,
        plate_detection=plate_status,
        insightface_models=insightface_status,
        yolo_model=yolo_status,
        tesseract=tesseract_status,
        gallery=gallery_status,
    )


def _check_face_recognition(settings) -> FeatureStatus:
    """Check if face recognition is enabled and available."""
    enabled = settings.face.enabled
    if not enabled:
        return FeatureStatus(
            name="Face Recognition",
            enabled=False,
            available=False,
            details="Disabled in configuration",
        )

    # Check if we can import required modules
    try:
        from cam_vision.face.recognizer import FaceRecognizer  # noqa: F401

        available = True
        error = None
    except ImportError as e:
        available = False
        error = f"Import failed: {e}"

    return FeatureStatus(
        name="Face Recognition",
        enabled=enabled,
        available=available,
        error=error,
        details="Requires InsightFace and gallery" if enabled else None,
    )


def _check_plate_detection(settings) -> FeatureStatus:
    """Check if plate detection is enabled and available."""
    enabled = settings.plates.enabled
    if not enabled:
        return FeatureStatus(
            name="Plate Detection",
            enabled=False,
            available=False,
            details="Disabled in configuration",
        )

    # Check if we can import required modules
    try:
        from cam_vision.plates.pipeline import PlateRecognizer  # noqa: F401

        available = True
        error = None
    except ImportError as e:
        available = False
        error = f"Import failed: {e}"

    return FeatureStatus(
        name="Plate Detection",
        enabled=enabled,
        available=available,
        error=error,
        details="Requires YOLOv8 model and Tesseract" if enabled else None,
    )


def _check_insightface_models(settings) -> FeatureStatus:
    """Check if InsightFace models are available."""
    if not settings.face.enabled:
        return FeatureStatus(
            name="InsightFace Models",
            enabled=False,
            available=False,
            details="Face recognition disabled",
        )

    try:
        # Try to import and check models directory
        import insightface  # noqa: F401

        models_dir = Path.home() / ".insightface" / "models"
        if models_dir.exists():
            available = True
            error = None
            details = f"Models at {models_dir}"
        else:
            available = False
            error = "Models directory not found"
            details = f"Expected at {models_dir}"
    except ImportError as e:
        available = False
        error = f"InsightFace not installed: {e}"
        details = "Run: pip install insightface"

    return FeatureStatus(
        name="InsightFace Models", enabled=True, available=available, error=error, details=details
    )


def _check_yolo_model(settings) -> FeatureStatus:
    """Check if YOLO model file exists."""
    if not settings.plates.enabled:
        return FeatureStatus(
            name="YOLO Model", enabled=False, available=False, details="Plate detection disabled"
        )

    model_path = Path(settings.plates.detector.model_path)
    available = model_path.exists()

    if available:
        size_mb = model_path.stat().st_size / (1024 * 1024)
        error = None
        details = f"Model: {model_path.name} ({size_mb:.1f} MB)"
    else:
        error = f"Model not found at {model_path}"
        details = "Download a YOLOv8 plate detection model"

    return FeatureStatus(
        name="YOLO Model", enabled=True, available=available, error=error, details=details
    )


def _check_tesseract(settings) -> FeatureStatus:
    """Check if Tesseract is installed and available."""
    if not settings.plates.enabled:
        return FeatureStatus(
            name="Tesseract OCR", enabled=False, available=False, details="Plate detection disabled"
        )

    try:
        import pytesseract

        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        available = True
        error = None
        details = f"Version {version}"
    except Exception as e:
        available = False
        error = f"Tesseract not available: {e}"
        details = (
            "Install: brew install tesseract (macOS) or apt-get install tesseract-ocr (Ubuntu)"
        )

    return FeatureStatus(
        name="Tesseract OCR", enabled=True, available=available, error=error, details=details
    )


def _check_gallery(settings) -> FeatureStatus:
    """Check if face gallery is enrolled and available."""
    if not settings.face.enabled:
        return FeatureStatus(
            name="Face Gallery", enabled=False, available=False, details="Face recognition disabled"
        )

    gallery_cache = Path(settings.face.gallery_cache)
    gallery_path = Path(settings.face.gallery_path)

    if not gallery_cache.exists():
        available = False
        error = f"Gallery cache not found at {gallery_cache}"
        details = f"Run: poetry run securevision-face-enroll --gallery {gallery_path} --output {gallery_cache}"
    else:
        # Try to load gallery and get person count
        try:
            from cam_vision.face.gallery import FaceGallery

            gallery = FaceGallery(gallery_path=str(gallery_path), cache_path=str(gallery_cache))
            gallery.load()
            person_count = gallery.size()

            available = person_count > 0
            if available:
                error = None
                details = f"{person_count} person(s) enrolled"
            else:
                error = "Gallery is empty"
                details = f"Add face images to {gallery_path} and re-enroll"

        except Exception as e:
            available = False
            error = f"Failed to load gallery: {e}"
            details = None

    return FeatureStatus(
        name="Face Gallery", enabled=True, available=available, error=error, details=details
    )
