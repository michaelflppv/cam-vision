"""Controls sidebar orchestrating all configuration components."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..styles import fonts, tokens
from ..widgets.collapsible_section import CollapsibleSection
from .connection_controls import ConnectionControls
from .diagnostics_panel import DiagnosticsPanel
from .enrollment_controls import EnrollmentControls
from .face_controls import FaceControls
from .source_picker import SourcePicker
from .tracking_controls import TrackingControls
from .video_settings import VideoSettings

logger = logging.getLogger(__name__)


class ControlsSidebar(QWidget):
    """Sidebar containing all configuration controls.

    Organized into collapsible sections:
    - Connection Controls (always visible)
    - Video Source
    - Video Settings
    - Face Recognition

    Signals:
        connect_clicked: Emitted when Connect button clicked
        disconnect_clicked: Emitted when Disconnect button clicked
        source_changed: Emitted when source config changes (source_config)
        fps_changed: Emitted when FPS target changes (int)
        resize_changed: Emitted when resize option changes (tuple or None)
        auto_refresh_changed: Emitted when auto-refresh changes (bool)
        face_threshold_changed: Emitted when face threshold changes (float)
        tracking_enabled_changed: Emitted when tracking is enabled/disabled (bool)
        tracking_params_changed: Emitted when tracking params change (dict)
    """

    connect_clicked = Signal()
    disconnect_clicked = Signal()
    source_changed = Signal(object)
    fps_changed = Signal(int)
    resize_changed = Signal(object)
    auto_refresh_changed = Signal(bool)
    face_threshold_changed = Signal(float)
    tracking_enabled_changed = Signal(bool)
    tracking_params_changed = Signal(dict)

    def __init__(self):
        """Initialize controls sidebar."""
        super().__init__()

        # Create child widgets
        self.connection_controls = ConnectionControls()
        self.source_picker = SourcePicker()
        self.video_settings = VideoSettings()
        self.face_controls = FaceControls()
        self.tracking_controls = TrackingControls()
        self.diagnostics_panel = DiagnosticsPanel()
        self.enrollment_controls = EnrollmentControls()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI layout."""
        self.setFixedWidth(tokens.SIDEBAR_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
        )
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Title
        title = QLabel("SecureVision")
        title.setObjectName("heading")
        font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_HEADING)
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Live Video Detection")
        subtitle.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_NORMAL}px;"
        )
        layout.addWidget(subtitle)

        # Connection controls (always visible)
        layout.addWidget(self.connection_controls)

        # Scrollable area for expandable sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll_container = QWidget()
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(tokens.SPACING_COMFORTABLE)
        scroll_layout.setSizeConstraint(QLayout.SetMinimumSize)

        self._collapsible_sections = []

        # Source picker section (collapsible)
        source_section = CollapsibleSection("Video Source", expanded=True)
        source_section.set_content_widget(self.source_picker)
        self._register_section(source_section)
        scroll_layout.addWidget(source_section)

        # Video settings section (collapsible)
        settings_section = CollapsibleSection("Video Settings", expanded=False)
        settings_section.set_content_widget(self.video_settings)
        self._register_section(settings_section)
        scroll_layout.addWidget(settings_section)

        # Face controls section (collapsible)
        face_section = CollapsibleSection("Face Recognition", expanded=False)
        face_section.set_content_widget(self.face_controls)
        self._register_section(face_section)
        scroll_layout.addWidget(face_section)

        # Tracking controls section (collapsible)
        tracking_section = CollapsibleSection("Tracking", expanded=False)
        tracking_section.set_content_widget(self.tracking_controls)
        self._register_section(tracking_section)
        scroll_layout.addWidget(tracking_section)

        # Diagnostics section (collapsible)
        diagnostics_section = CollapsibleSection("Diagnostics", expanded=False)
        diagnostics_section.set_content_widget(self.diagnostics_panel)
        self._register_section(diagnostics_section)
        scroll_layout.addWidget(diagnostics_section)

        # Enrollment section (collapsible)
        enrollment_section = CollapsibleSection("Accepted Lists", expanded=False)
        enrollment_section.set_content_widget(self.enrollment_controls)
        self._register_section(enrollment_section)
        scroll_layout.addWidget(enrollment_section)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_container)
        layout.addWidget(scroll, 1)

        # Feature status label (for displaying errors/warnings)
        self.feature_status_label = QLabel("")
        self.feature_status_label.setWordWrap(True)
        self.feature_status_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; "
            f"font-size: {tokens.FONT_SIZE_SMALL}px; "
            f"padding: {tokens.PADDING_SMALL}px;"
        )
        layout.addWidget(self.feature_status_label)

    def _register_section(self, section: CollapsibleSection):
        """Register a collapsible section for exclusive expansion."""
        self._collapsible_sections.append(section)
        section.toggled.connect(
            lambda expanded, active=section: self._on_section_toggled(active, expanded)
        )

    def _on_section_toggled(self, active_section: CollapsibleSection, expanded: bool):
        """Ensure only one section stays open at a time."""
        if not expanded:
            return
        for section in self._collapsible_sections:
            if section is not active_section and section.is_expanded():
                section.set_expanded(False, animated=True)

    def _connect_signals(self):
        """Connect child widget signals to parent signals."""
        # Connection controls
        self.connection_controls.connect_clicked.connect(self.connect_clicked.emit)
        self.connection_controls.disconnect_clicked.connect(self.disconnect_clicked.emit)

        # Source picker
        self.source_picker.source_changed.connect(self.source_changed.emit)

        # Video settings
        self.video_settings.fps_changed.connect(self.fps_changed.emit)
        self.video_settings.resize_changed.connect(self.resize_changed.emit)
        self.video_settings.auto_refresh_changed.connect(self.auto_refresh_changed.emit)

        # Face controls
        self.face_controls.threshold_changed.connect(self.face_threshold_changed.emit)

        # Tracking controls
        self.tracking_controls.tracking_enabled_changed.connect(self.tracking_enabled_changed.emit)
        self.tracking_controls.frames_required_changed.connect(self._on_tracking_param_changed)
        self.tracking_controls.iou_threshold_changed.connect(self._on_tracking_param_changed)
        self.tracking_controls.max_age_changed.connect(self._on_tracking_param_changed)
        self.tracking_controls.ocr_agreement_changed.connect(self._on_tracking_param_changed)

    def _on_tracking_param_changed(self):
        """Handle tracking parameter change and emit combined params."""
        params = {
            "frames_required": self.tracking_controls.get_frames_required(),
            "iou_threshold": self.tracking_controls.get_iou_threshold(),
            "max_age_frames": self.tracking_controls.get_max_age(),
            "ocr_agreement_threshold": self.tracking_controls.get_ocr_agreement_threshold(),
        }
        self.tracking_params_changed.emit(params)

    def set_feature_status(self, status_text: str):
        """Set feature status text.

        Args:
            status_text: Status text to display
        """
        self.feature_status_label.setText(status_text)

    def get_source_config(self):
        """Get current source configuration.

        Returns:
            Source config object or None
        """
        return self.source_picker.get_source_config()

    def get_fps_target(self) -> int:
        """Get current FPS target.

        Returns:
            FPS target
        """
        return self.video_settings.get_fps_target()

    def get_resize(self) -> tuple | None:
        """Get current resize option.

        Returns:
            (width, height) tuple or None
        """
        return self.video_settings.get_resize()

    def get_face_threshold(self) -> float:
        """Get current face threshold.

        Returns:
            Face similarity threshold (0.0-1.0)
        """
        return self.face_controls.get_threshold()

    def is_auto_refresh(self) -> bool:
        """Check if auto-refresh is enabled.

        Returns:
            True if enabled
        """
        return self.video_settings.is_auto_refresh()

    def is_tracking_enabled(self) -> bool:
        """Check if tracking is enabled.

        Returns:
            True if enabled
        """
        return self.tracking_controls.is_tracking_enabled()

    def get_tracking_params(self) -> dict:
        """Get tracking parameters.

        Returns:
            Tracking parameters dictionary
        """
        return {
            "frames_required": self.tracking_controls.get_frames_required(),
            "iou_threshold": self.tracking_controls.get_iou_threshold(),
            "max_age_frames": self.tracking_controls.get_max_age(),
            "ocr_agreement_threshold": self.tracking_controls.get_ocr_agreement_threshold(),
        }
