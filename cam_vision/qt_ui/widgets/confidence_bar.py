"""Confidence bar widget with percentage overlay.

A styled progress bar with centered percentage text overlay.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from ..styles import fonts, tokens


class ConfidenceBar(QWidget):
    """Progress bar with percentage overlay label.

    Features:
    - Black fill, white background
    - Centered percentage text
    - Text color adapts: black on white, white on black fill
    - 20px height (or configurable)
    """

    def __init__(self, value: float = 0.0, label: str = None, parent=None):
        """Initialize the confidence bar.

        Args:
            value: Initial value (0.0 to 1.0)
            label: Optional label above the bar
            parent: Parent widget
        """
        super().__init__(parent)
        self._value = value
        self._label_text = label

        self._setup_ui()
        self.set_value(value)

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # Optional label above bar
        if self._label_text:
            self.label = QLabel(self._label_text)
            font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_SMALL)
            font.setWeight(QFont.Weight.DemiBold)
            self.label.setFont(font)
            layout.addWidget(self.label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedHeight(tokens.PROGRESSBAR_HEIGHT)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)

        # Set format to show percentage
        self.progress_bar.setFormat("%p%")

        layout.addWidget(self.progress_bar)

    def set_value(self, value: float):
        """Update the progress bar value.

        Args:
            value: Value between 0.0 and 1.0
        """
        self._value = max(0.0, min(1.0, value))
        percentage = int(self._value * 100)
        self.progress_bar.setValue(percentage)

    def get_value(self) -> float:
        """Get the current value.

        Returns:
            Current value (0.0 to 1.0)
        """
        return self._value

    def set_label(self, label: str):
        """Update the label text.

        Args:
            label: New label text
        """
        if hasattr(self, "label"):
            self.label.setText(label)
