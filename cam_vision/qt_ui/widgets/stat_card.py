"""Stat card widget for displaying key metrics.

Displays a single metric with label and value in a styled card.
"""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ..styles import fonts, tokens


class StatCard(QFrame):
    """Stat card widget for displaying a single metric.

    Features:
    - Subtle gray background (#F5F5F5)
    - Uppercase label (small, gray)
    - Large bold value (24px, black)
    - Fixed height (80px)
    - 16px padding

    Typical use: FPS, Frame Count, Feature Status
    """

    def __init__(self, label: str, value: str = "—", parent=None):
        """Initialize the stat card.

        Args:
            label: Metric label (will be uppercased)
            value: Initial value to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._label = label.upper()
        self._value = value

        self.setObjectName("statCard")
        self.setFixedHeight(tokens.STAT_CARD_HEIGHT)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            tokens.STAT_CARD_PADDING,
            tokens.STAT_CARD_PADDING,
            tokens.STAT_CARD_PADDING,
            tokens.STAT_CARD_PADDING,
        )
        layout.setSpacing(tokens.SPACING_TIGHT)

        # Label (uppercase, small, gray)
        self.label_widget = QLabel(self._label)
        self.label_widget.setObjectName("statLabel")
        label_font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_STAT_LABEL)
        self.label_widget.setFont(label_font)
        self.label_widget.setStyleSheet(f"color: {tokens.TEXT_SECONDARY};")

        # Value (large, bold, black)
        self.value_widget = QLabel(self._value)
        self.value_widget.setObjectName("statValue")
        value_font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_STAT_VALUE)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_widget.setFont(value_font)

        layout.addWidget(self.label_widget)
        layout.addWidget(self.value_widget)
        layout.addStretch()

    def set_value(self, value: str):
        """Update the displayed value.

        Args:
            value: New value text
        """
        self._value = value
        self.value_widget.setText(value)

    def get_value(self) -> str:
        """Get the current value.

        Returns:
            Current value text
        """
        return self._value
