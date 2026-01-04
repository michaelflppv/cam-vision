"""Controls sidebar for connection and source selection."""

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
from .connection_controls import ConnectionControls
from .source_picker import SourcePicker

logger = logging.getLogger(__name__)


class ControlsSidebar(QWidget):
    """Sidebar containing connection and device selection controls.

    Signals:
        connect_clicked: Emitted when Connect button clicked
        disconnect_clicked: Emitted when Disconnect button clicked
        source_changed: Emitted when source config changes (source_config)
    """

    connect_clicked = Signal()
    disconnect_clicked = Signal()
    source_changed = Signal(object)

    def __init__(self):
        """Initialize controls sidebar."""
        super().__init__()

        # Create child widgets
        self.connection_controls = ConnectionControls()
        self.source_picker = SourcePicker()

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

        # Scrollable area for device selection
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

        scroll_layout.addWidget(self.source_picker)

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

    def _connect_signals(self):
        """Connect child widget signals to parent signals."""
        # Connection controls
        self.connection_controls.connect_clicked.connect(self.connect_clicked.emit)
        self.connection_controls.disconnect_clicked.connect(self.disconnect_clicked.emit)

        # Source picker
        self.source_picker.source_changed.connect(self.source_changed.emit)

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
