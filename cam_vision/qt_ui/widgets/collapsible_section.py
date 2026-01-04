"""Collapsible section widget for organizing controls.

Provides an expandable/collapsible container with smooth animation,
perfect for sidebar organization.
"""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout, QWidget

from ..styles import fonts, tokens


class CollapsibleSection(QWidget):
    """Collapsible container widget with animated expand/collapse.

    Features:
    - Clickable header with expand/collapse icon
    - Smooth height animation (300ms ease-in-out)
    - Content widget container
    - State persistence via signals

    Signals:
        toggled: Emitted when section is expanded/collapsed (bool expanded)
    """

    toggled = Signal(bool)

    def __init__(
        self, title: str, content_widget: QWidget = None, expanded: bool = False, parent=None
    ):
        """Initialize the collapsible section.

        Args:
            title: Section title displayed in header
            content_widget: Widget to display as collapsible content
            expanded: Initial expansion state
            parent: Parent widget
        """
        super().__init__(parent)
        self._title = title
        self._expanded = expanded
        self._content_widget = content_widget

        self._setup_ui()
        self._setup_animation()

        # Set initial state (collapsed by default)
        if self._expanded:
            self._expand_immediate()
        else:
            self._collapse_immediate()

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.header_button = QPushButton()
        self.header_button.setObjectName("collapseHeader")
        self.header_button.setText(self._get_header_text())
        self.header_button.setCheckable(False)
        self.header_button.clicked.connect(self._toggle)

        font = QFont(fonts.get_system_font_name(), tokens.FONT_SIZE_NORMAL)
        font.setWeight(QFont.Weight.Bold)
        self.header_button.setFont(font)

        # Content container
        self.content_container = QFrame()
        self.content_container.setObjectName("collapseContent")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(
            tokens.PADDING_LARGE,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_LARGE,
            tokens.PADDING_MEDIUM,
        )
        self.content_layout.setSpacing(tokens.SPACING_NORMAL)

        # Add content widget if provided
        if self._content_widget:
            self.content_layout.addWidget(self._content_widget)

        # Add to main layout
        layout.addWidget(self.header_button)
        layout.addWidget(self.content_container)

    def _setup_animation(self):
        """Set up the height animation."""
        self.animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self.animation.setDuration(tokens.ANIMATION_DURATION_NORMAL)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def _get_header_text(self) -> str:
        """Get the header button text with arrow icon.

        Returns:
            Header text with appropriate arrow (▼ expanded, ▶ collapsed)
        """
        arrow = "▼" if self._expanded else "▶"
        return f"{arrow}  {self._title}"

    def _toggle(self):
        """Toggle the expansion state."""
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        """Expand the section with animation."""
        if self._expanded:
            return

        self._expanded = True
        self.header_button.setText(self._get_header_text())

        # Calculate target height
        target_height = self.content_container.sizeHint().height()

        # Animate from current to target
        self.animation.setStartValue(self.content_container.maximumHeight())
        self.animation.setEndValue(target_height)
        self.animation.start()

        # After animation completes, set to expanding to allow dynamic resizing
        self.animation.finished.connect(self._on_expand_finished, Qt.UniqueConnection)

        self.toggled.emit(True)

    def collapse(self):
        """Collapse the section with animation."""
        if not self._expanded:
            return

        self._expanded = False
        self.header_button.setText(self._get_header_text())

        # Animate from current to 0
        self.animation.setStartValue(self.content_container.maximumHeight())
        self.animation.setEndValue(0)
        self.animation.start()

        self.toggled.emit(False)

    def _expand_immediate(self):
        """Expand immediately without animation (for initial state)."""
        self._expanded = True
        self.header_button.setText(self._get_header_text())
        self.content_container.setMaximumHeight(16777215)  # Qt QWIDGETSIZE_MAX

    def _collapse_immediate(self):
        """Collapse immediately without animation (for initial state)."""
        self._expanded = False
        self.header_button.setText(self._get_header_text())
        self.content_container.setMaximumHeight(0)

    def _on_expand_finished(self):
        """Handle animation finished for expansion.

        Sets maximum height to allow content to resize dynamically.
        """
        if self._expanded:
            self.content_container.setMaximumHeight(16777215)  # Qt QWIDGETSIZE_MAX

    def set_content_widget(self, widget: QWidget):
        """Set or replace the content widget.

        Args:
            widget: New content widget
        """
        # Remove existing content widget
        if self._content_widget:
            self.content_layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)

        # Add new widget
        self._content_widget = widget
        self.content_layout.addWidget(widget)

    def is_expanded(self) -> bool:
        """Check if section is expanded.

        Returns:
            True if expanded, False if collapsed
        """
        return self._expanded

    def set_expanded(self, expanded: bool, animated: bool = True):
        """Set the expansion state programmatically.

        Args:
            expanded: True to expand, False to collapse
            animated: True to use animation, False for immediate change
        """
        if expanded == self._expanded:
            return

        if animated:
            if expanded:
                self.expand()
            else:
                self.collapse()
        else:
            if expanded:
                self._expand_immediate()
            else:
                self._collapse_immediate()
