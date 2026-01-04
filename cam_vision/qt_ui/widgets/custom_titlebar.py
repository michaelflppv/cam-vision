"""Custom title bar for frameless window.

Provides window controls (minimize/maximize/close) and drag functionality
while maintaining the strict monochromatic design philosophy.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from ..styles import fonts, tokens


class MacOSButton(QPushButton):
    """macOS-style traffic light button with hover symbols."""

    def __init__(self, role: str, parent=None):
        """Initialize macOS button.

        Args:
            role: Button role (close, minimize, maximize)
            parent: Parent widget
        """
        super().__init__(parent)
        self.role = role
        self.hovered = False
        self.setObjectName(f"titleBar{role.capitalize()}")

        # Set colors based on role
        self.colors = {
            "close": "#FF5F57",
            "minimize": "#FFBD2E",
            "maximize": "#28C840",
        }
        self.symbols = {
            "close": "×",
            "minimize": "−",
            "maximize": "+",
        }
        radius = tokens.TITLEBAR_BUTTON_SIZE // 2

        self.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.colors[role]};
                border: 0.5px solid rgba(0, 0, 0, 0.15);
                border-radius: {radius}px;
                color: rgba(0, 0, 0, 0.7);
                font-size: 11px;
                font-weight: bold;
                min-width: {tokens.TITLEBAR_BUTTON_SIZE}px;
                max-width: {tokens.TITLEBAR_BUTTON_SIZE}px;
                min-height: {tokens.TITLEBAR_BUTTON_SIZE}px;
                max-height: {tokens.TITLEBAR_BUTTON_SIZE}px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.colors[role]};
            }}
            """
        )

    def enterEvent(self, event):
        """Show symbol on hover."""
        self.hovered = True
        self.setText(self.symbols[self.role])
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide symbol when not hovering."""
        self.hovered = False
        self.setText("")
        super().leaveEvent(event)


class CustomTitleBar(QWidget):
    """Custom title bar widget for frameless windows.

    Features:
    - Draggable area for window movement
    - Minimize, maximize/restore, and close buttons
    - Application title display
    - Pure white background with black controls
    - Fixed height (40px)

    Signals:
        minimize_clicked: Emitted when minimize button is clicked
        maximize_clicked: Emitted when maximize button is clicked
        close_clicked: Emitted when close button is clicked
    """

    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, title: str = "SecureVision", parent=None):
        """Initialize the custom title bar.

        Args:
            title: Application title to display
            parent: Parent widget
        """
        super().__init__(parent)
        self._title = title
        self._drag_position = None

        self.setObjectName("customTitleBar")
        self.setFixedHeight(tokens.TITLEBAR_HEIGHT)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the title bar UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(tokens.PADDING_SMALL, 0, tokens.PADDING_SMALL, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # Window control buttons (left side, macOS order)
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)  # macOS traffic light spacing

        self.close_button = self._create_title_button("close")
        self.minimize_button = self._create_title_button("minimize")
        self.maximize_button = self._create_title_button("maximize")

        controls_layout.addWidget(self.close_button)
        controls_layout.addWidget(self.minimize_button)
        controls_layout.addWidget(self.maximize_button)

        # Title label (left side)
        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("titleBarLabel")
        font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_NORMAL)
        font.setWeight(QFont.Weight.Bold)
        self.title_label.setFont(font)

        # Spacer (draggable area)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Connect button signals
        self.minimize_button.clicked.connect(self.minimize_clicked)
        self.maximize_button.clicked.connect(self.maximize_clicked)
        self.close_button.clicked.connect(self.close_clicked)

        # Add widgets to layout
        layout.addWidget(controls_container)
        layout.addWidget(self.title_label)
        layout.addWidget(spacer)

    def _create_title_button(self, role: str) -> QPushButton:
        """Create a window control button (macOS style).

        Args:
            role: Button role (close, minimize, maximize)

        Returns:
            Configured QPushButton
        """
        button = MacOSButton(role)
        button.setFixedSize(tokens.TITLEBAR_BUTTON_SIZE, tokens.TITLEBAR_BUTTON_SIZE)
        button.setToolTip(role.capitalize())
        return button

    def set_title(self, title: str):
        """Update the title bar title.

        Args:
            title: New title text
        """
        self._title = title
        self.title_label.setText(title)

    def set_maximized(self, maximized: bool):
        """Update the maximize button icon based on window state.

        Args:
            maximized: True if window is maximized, False otherwise
        """
        self.maximize_button.setProperty("titleBarMaximized", maximized)
        self.maximize_button.style().unpolish(self.maximize_button)
        self.maximize_button.style().polish(self.maximize_button)

    # ========================================================================
    # Window Dragging Support
    # ========================================================================

    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging.

        Args:
            event: QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            # Don't start drag if clicking on buttons
            if not self._is_button_click(event.pos()):
                self._drag_position = (
                    event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
                )
                event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging.

        Args:
            event: QMouseEvent
        """
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            # Only allow dragging if window is not maximized
            if not self.window().isMaximized():
                self.window().move(event.globalPosition().toPoint() - self._drag_position)
                event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events.

        Args:
            event: QMouseEvent
        """
        self._drag_position = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to maximize/restore window.

        Args:
            event: QMouseEvent
        """
        if event.button() == Qt.LeftButton:
            if not self._is_button_click(event.pos()):
                self.maximize_clicked.emit()
                event.accept()

    def _is_button_click(self, pos):
        """Check if click position is on a button.

        Args:
            pos: Click position

        Returns:
            True if click is on a button, False otherwise
        """
        for button in [self.minimize_button, self.maximize_button, self.close_button]:
            if button.geometry().contains(pos):
                return True
        return False
