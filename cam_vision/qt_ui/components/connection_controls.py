"""Connection controls for starting/stopping video capture."""

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ..styles import tokens
from ..widgets.status_badge import StatusBadge

logger = logging.getLogger(__name__)


class ConnectionControls(QWidget):
    """Connection controls with Connect/Disconnect buttons and status indicator.

    Signals:
        connect_clicked: Emitted when Connect button is clicked
        disconnect_clicked: Emitted when Disconnect button is clicked
    """

    connect_clicked = Signal()
    disconnect_clicked = Signal()

    def __init__(self):
        """Initialize connection controls."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        # Status badge
        self.status_badge = StatusBadge("Disconnected", "gray")
        layout.addWidget(self.status_badge)

        # Connect button (match secondary styling for consistency)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("secondary")
        self.connect_btn.setMinimumHeight(40)
        self.connect_btn.clicked.connect(lambda _=False: self.connect_clicked.emit())
        layout.addWidget(self.connect_btn)

        # Disconnect button (secondary style, initially hidden)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("secondary")
        self.disconnect_btn.setMinimumHeight(40)
        self.disconnect_btn.clicked.connect(lambda _=False: self.disconnect_clicked.emit())
        self.disconnect_btn.hide()  # Initially hidden
        layout.addWidget(self.disconnect_btn)

    def set_connected(self, connected: bool):
        """Update UI based on connection state.

        Args:
            connected: True if connected, False otherwise
        """
        if connected:
            self.status_badge.set_status("Connected", "green")
            self.connect_btn.hide()
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.show()
        else:
            self.status_badge.set_status("Disconnected", "gray")
            self.connect_btn.show()
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.hide()

    def set_connecting(self):
        """Set UI to connecting state."""
        self.status_badge.set_status("Connecting...", "yellow")
        self.connect_btn.setEnabled(False)
        self.connect_btn.show()
        self.disconnect_btn.hide()

    def set_error(self, error_msg: str):
        """Set UI to error state.

        Args:
            error_msg: Error message to display
        """
        self.status_badge.set_status(f"Error: {error_msg}", "red")
        self.connect_btn.show()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.hide()
