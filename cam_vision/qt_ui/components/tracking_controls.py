"""Multi-frame tracking and confirmation controls widget."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QLabel, QSlider, QSpinBox, QVBoxLayout, QWidget

from ..styles import tokens

logger = logging.getLogger(__name__)


class TrackingControls(QWidget):
    """Multi-frame tracking control panel.

    Controls:
    - Enable/disable tracking
    - Frames required for confirmation (K)
    - IoU threshold for track matching
    - Max age (track expiration in frames)
    - OCR agreement threshold (plates only)

    Signals:
        tracking_enabled_changed: Emitted when tracking is enabled/disabled (bool)
        frames_required_changed: Emitted when frames required changes (int)
        iou_threshold_changed: Emitted when IoU threshold changes (float)
        max_age_changed: Emitted when max age changes (int)
        ocr_agreement_changed: Emitted when OCR agreement threshold changes (float)
    """

    tracking_enabled_changed = Signal(bool)
    frames_required_changed = Signal(int)
    iou_threshold_changed = Signal(float)
    max_age_changed = Signal(int)
    ocr_agreement_changed = Signal(float)

    def __init__(self):
        """Initialize tracking controls widget."""
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Header
        header = QLabel("Multi-Frame Tracking")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(header)

        # Description
        description = QLabel(
            "Enable tracking and confirmation to reduce false positives.\n"
            "Requires K consecutive frame matches before emitting events."
        )
        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(description)

        # Enable/disable tracking
        self.tracking_enabled_check = QCheckBox("Enable Tracking")
        self.tracking_enabled_check.setChecked(True)
        self.tracking_enabled_check.stateChanged.connect(
            lambda state: self._on_tracking_enabled_changed(state == 2)
        )
        layout.addWidget(self.tracking_enabled_check)

        # Frames required (K)
        frames_label = QLabel("Frames Required (K):")
        frames_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(frames_label)

        self.frames_required_input = QSpinBox()
        self.frames_required_input.setRange(1, 10)
        self.frames_required_input.setValue(3)
        self.frames_required_input.setSuffix(" frames")
        self.frames_required_input.setMinimumHeight(32)
        self.frames_required_input.valueChanged.connect(self.frames_required_changed.emit)
        layout.addWidget(self.frames_required_input)

        frames_help = QLabel("Number of consecutive frames required to confirm a detection.")
        frames_help.setWordWrap(True)
        frames_help.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(frames_help)

        # IoU threshold
        iou_label = QLabel("IoU Threshold:")
        iou_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(iou_label)

        self.iou_threshold_slider = QSlider()
        self.iou_threshold_slider.setOrientation(Qt.Horizontal)
        self.iou_threshold_slider.setRange(10, 100)  # 0.1-1.0
        self.iou_threshold_slider.setValue(50)  # 0.5
        self.iou_threshold_slider.setMinimumHeight(32)
        self.iou_threshold_slider.valueChanged.connect(self._on_iou_changed)
        layout.addWidget(self.iou_threshold_slider)

        self.iou_value_label = QLabel("Current: 0.50")
        self.iou_value_label.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(self.iou_value_label)

        iou_help = QLabel(
            "Intersection-over-Union threshold for matching detections across frames."
        )
        iou_help.setWordWrap(True)
        iou_help.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(iou_help)

        # Max age (frames)
        max_age_label = QLabel("Max Age (frames):")
        max_age_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(max_age_label)

        self.max_age_input = QSpinBox()
        self.max_age_input.setRange(10, 120)
        self.max_age_input.setValue(30)
        self.max_age_input.setSingleStep(5)
        self.max_age_input.setSuffix(" frames")
        self.max_age_input.setMinimumHeight(32)
        self.max_age_input.valueChanged.connect(self.max_age_changed.emit)
        layout.addWidget(self.max_age_input)

        max_age_help = QLabel("Number of frames before a lost track expires.")
        max_age_help.setWordWrap(True)
        max_age_help.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(max_age_help)

        # OCR agreement threshold (plates)
        ocr_section_label = QLabel("Plate-Specific Settings:")
        ocr_section_label.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(ocr_section_label)

        ocr_label = QLabel("OCR Agreement Threshold:")
        ocr_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(ocr_label)

        self.ocr_agreement_slider = QSlider()
        self.ocr_agreement_slider.setOrientation(Qt.Horizontal)
        self.ocr_agreement_slider.setRange(10, 100)  # 0.1-1.0
        self.ocr_agreement_slider.setValue(60)  # 0.6
        self.ocr_agreement_slider.setMinimumHeight(32)
        self.ocr_agreement_slider.valueChanged.connect(self._on_ocr_agreement_changed)
        layout.addWidget(self.ocr_agreement_slider)

        self.ocr_value_label = QLabel("Current: 0.60 (60%)")
        self.ocr_value_label.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(self.ocr_value_label)

        ocr_help = QLabel(
            "Minimum agreement required for OCR text across frames. "
            "Uses majority voting on the last 10 OCR reads."
        )
        ocr_help.setWordWrap(True)
        ocr_help.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(ocr_help)

        # Note
        note = QLabel(
            "Note: Tracking settings require reconnecting to take effect.\n"
            "Click Disconnect then Connect to apply changes."
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(note)

    def _on_tracking_enabled_changed(self, enabled: bool):
        """Handle tracking enabled state change.

        Args:
            enabled: True if tracking is enabled
        """
        # Enable/disable controls
        self.frames_required_input.setEnabled(enabled)
        self.iou_threshold_slider.setEnabled(enabled)
        self.max_age_input.setEnabled(enabled)
        self.ocr_agreement_slider.setEnabled(enabled)

        self.tracking_enabled_changed.emit(enabled)

    def _on_iou_changed(self, value: int):
        """Handle IoU threshold slider change.

        Args:
            value: Slider value (10-100)
        """
        # Convert to float (0.1-1.0)
        threshold = value / 100.0
        self.iou_value_label.setText(f"Current: {threshold:.2f}")
        self.iou_threshold_changed.emit(threshold)

    def _on_ocr_agreement_changed(self, value: int):
        """Handle OCR agreement slider change.

        Args:
            value: Slider value (10-100)
        """
        # Convert to float (0.1-1.0)
        threshold = value / 100.0
        self.ocr_value_label.setText(f"Current: {threshold:.2f} ({int(threshold * 100)}%)")
        self.ocr_agreement_changed.emit(threshold)

    def is_tracking_enabled(self) -> bool:
        """Check if tracking is enabled.

        Returns:
            True if enabled
        """
        return self.tracking_enabled_check.isChecked()

    def get_frames_required(self) -> int:
        """Get frames required for confirmation.

        Returns:
            Number of frames
        """
        return self.frames_required_input.value()

    def get_iou_threshold(self) -> float:
        """Get IoU threshold.

        Returns:
            IoU threshold (0.1-1.0)
        """
        return self.iou_threshold_slider.value() / 100.0

    def get_max_age(self) -> int:
        """Get max age in frames.

        Returns:
            Max age
        """
        return self.max_age_input.value()

    def get_ocr_agreement_threshold(self) -> float:
        """Get OCR agreement threshold.

        Returns:
            Agreement threshold (0.1-1.0)
        """
        return self.ocr_agreement_slider.value() / 100.0

    def set_tracking_enabled(self, enabled: bool):
        """Set tracking enabled state.

        Args:
            enabled: True to enable
        """
        self.tracking_enabled_check.setChecked(enabled)
