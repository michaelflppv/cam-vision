"""Face recognition controls widget with similarity threshold slider and presets."""

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..styles import tokens
from ..widgets.monochrome_slider import MonochromeSlider

logger = logging.getLogger(__name__)


class FaceControls(QWidget):
    """Face recognition control panel.

    Controls:
    - Similarity threshold slider (0.0-1.0)
    - Quick preset buttons (Strict, Balanced, Lenient)
    - Visual interpretation of current value

    Signals:
        threshold_changed: Emitted when threshold changes (float)
    """

    threshold_changed = Signal(float)

    def __init__(self):
        """Initialize face controls widget."""
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Header
        header = QLabel("Face Recognition")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(header)

        # Description
        description = QLabel(
            "Minimum similarity score (0.0-1.0) for face matching.\n"
            "Lower = stricter, Higher = lenient."
        )
        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(description)

        # Create slider with interpretation function
        self.threshold_slider = MonochromeSlider(
            name="Face Similarity Threshold",
            minimum=0.0,
            maximum=1.0,
            step=0.01,
            default=0.35,
            interpretation_func=self._get_interpretation,
        )
        self.threshold_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.threshold_slider)

        # Quick presets
        presets_label = QLabel("Quick Presets:")
        presets_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(presets_label)

        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(tokens.SPACING_TIGHT)

        self.strict_btn = QPushButton("Strict\n(0.30)")
        self.strict_btn.setObjectName("secondary")
        self.strict_btn.setMinimumHeight(50)
        self.strict_btn.clicked.connect(lambda: self.set_threshold(0.30))
        presets_layout.addWidget(self.strict_btn)

        self.balanced_btn = QPushButton("Balanced\n(0.35)")
        self.balanced_btn.setObjectName("secondary")
        self.balanced_btn.setMinimumHeight(50)
        self.balanced_btn.clicked.connect(lambda: self.set_threshold(0.35))
        presets_layout.addWidget(self.balanced_btn)

        self.lenient_btn = QPushButton("Lenient\n(0.45)")
        self.lenient_btn.setObjectName("secondary")
        self.lenient_btn.setMinimumHeight(50)
        self.lenient_btn.clicked.connect(lambda: self.set_threshold(0.45))
        presets_layout.addWidget(self.lenient_btn)

        layout.addLayout(presets_layout)

        # Note
        note = QLabel(
            "Note: Threshold changes apply to new detections.\n"
            "Restart capture to apply to all frames."
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(note)

    def _on_slider_changed(self, threshold: float):
        """Handle slider value change.

        Args:
            threshold: Threshold value (0.0-1.0)
        """
        # Emit signal
        self.threshold_changed.emit(threshold)

    def _get_interpretation(self, threshold: float) -> str:
        """Get interpretation for threshold value.

        Args:
            threshold: Threshold value (0.0-1.0)

        Returns:
            Interpretation string
        """
        if threshold < 0.25:
            return "Very Strict"
        elif threshold < 0.35:
            return "Strict"
        elif threshold < 0.45:
            return "Balanced"
        elif threshold < 0.55:
            return "Lenient"
        else:
            return "Very Lenient"

    def get_threshold(self) -> float:
        """Get current threshold value.

        Returns:
            Threshold (0.0-1.0)
        """
        return self.threshold_slider.get_value()

    def set_threshold(self, threshold: float):
        """Set threshold value.

        Args:
            threshold: Threshold (0.0-1.0)
        """
        self.threshold_slider.set_value(threshold)
