"""Status badge widget with colored indicator.

Displays a colored circle with text for status indication.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ..styles import fonts, tokens


class StatusBadge(QWidget):
    """Status badge with colored circle and text.

    Features:
    - Colored circle indicator (8px diameter)
    - Status text (10px, uppercase)
    - 6px spacing between elements

    Variants: Success, Warning, Error, Info, Neutral
    """

    def __init__(self, text: str, status: str = "neutral", parent=None):
        """Initialize the status badge.

        Args:
            text: Status text to display
            status: Status type ("success", "warning", "error", "info", "neutral")
            parent: Parent widget
        """
        super().__init__(parent)
        self._text = text.upper()
        self._status = status
        self._color = self._get_status_color(status)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.BADGE_SPACING)

        # Circle indicator
        self.circle = CircleIndicator(self._color)

        # Text label
        self.text_label = QLabel(self._text)
        font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_SMALL)
        self.text_label.setFont(font)

        layout.addWidget(self.circle)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def _get_status_color(self, status: str) -> str:
        """Get the color for a status type.

        Args:
            status: Status type

        Returns:
            Hex color code
        """
        color_map = {
            "success": tokens.ACCENT_SUCCESS,
            "warning": tokens.ACCENT_WARNING,
            "error": tokens.ACCENT_ERROR,
            "info": tokens.ACCENT_INFO,
            "neutral": tokens.ACCENT_NEUTRAL,
        }
        return color_map.get(status, tokens.ACCENT_NEUTRAL)

    def set_status(self, text: str, status: str = "neutral"):
        """Update the badge status and text.

        Args:
            text: New status text
            status: New status type
        """
        self._text = text.upper()
        self._status = status
        self._color = self._get_status_color(status)

        self.text_label.setText(self._text)
        self.circle.set_color(self._color)


class CircleIndicator(QWidget):
    """Simple colored circle widget."""

    def __init__(self, color: str, parent=None):
        """Initialize circle indicator.

        Args:
            color: Hex color code
            parent: Parent widget
        """
        super().__init__(parent)
        self._color = color
        self.setFixedSize(tokens.BADGE_CIRCLE_SIZE, tokens.BADGE_CIRCLE_SIZE)

    def set_color(self, color: str):
        """Update the circle color.

        Args:
            color: Hex color code
        """
        self._color = color
        self.update()

    def paintEvent(self, event):
        """Paint the colored circle.

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(self._color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, tokens.BADGE_CIRCLE_SIZE, tokens.BADGE_CIRCLE_SIZE)
