"""UI components for the monochromatic Qt dashboard.

Components are composed of custom widgets and follow the strict
monochromatic design system.
"""

from .connection_controls import ConnectionControls
from .controls_sidebar import ControlsSidebar
from .detection_card import DetectionCard, FaceMatchCard, PlateDetectionCard
from .detection_panels import FaceMatchesPanel, PlateDetectionsPanel
from .diagnostics_panel import DiagnosticsPanel
from .enrollment_controls import EnrollmentControls
from .face_controls import FaceControls
from .preview_panel import PreviewPanel
from .source_picker import SourcePicker
from .tracking_controls import TrackingControls
from .video_settings import VideoSettings

__all__ = [
    "ConnectionControls",
    "ControlsSidebar",
    "DetectionCard",
    "FaceMatchCard",
    "PlateDetectionCard",
    "FaceMatchesPanel",
    "PlateDetectionsPanel",
    "DiagnosticsPanel",
    "EnrollmentControls",
    "FaceControls",
    "PreviewPanel",
    "SourcePicker",
    "TrackingControls",
    "VideoSettings",
]
