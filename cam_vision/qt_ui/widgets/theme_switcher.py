"""Theme switcher widget for the title bar.

Provides a segmented control for switching between Light, System, and Dark themes.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

from ..styles import tokens


class ThemeSwitcher(QWidget):
    """Theme switcher with segmented buttons.

    Provides three options:
    - Light: Force light theme
    - System: Follow system theme (default)
    - Dark: Force dark theme

    Signals:
        theme_changed: Emitted when theme selection changes (str: "light", "system", "dark")
    """

    theme_changed = Signal(str)

    def __init__(self, parent=None):
        """Initialize the theme switcher.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._current_theme = "system"

        self.setObjectName("themeSwitcher")
        self._setup_ui()

    def _setup_ui(self):
        """Set up the switcher UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(-1)  # Overlap borders for segmented control

        # Button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        # Create buttons
        self.light_button = self._create_theme_button("Light", "light", is_first=True)
        self.system_button = self._create_theme_button("System", "system", is_middle=True)
        self.dark_button = self._create_theme_button("Dark", "dark", is_last=True)

        # Add buttons to layout
        layout.addWidget(self.light_button)
        layout.addWidget(self.system_button)
        layout.addWidget(self.dark_button)

        # Set default selection
        self.system_button.setChecked(True)

        # Connect signals
        self.button_group.buttonClicked.connect(self._on_button_clicked)

    def _create_theme_button(
        self, label: str, theme: str, is_first=False, is_middle=False, is_last=False
    ) -> QPushButton:
        """Create a theme button.

        Args:
            label: Button label
            theme: Theme identifier
            is_first: True if this is the first button
            is_middle: True if this is a middle button
            is_last: True if this is the last button

        Returns:
            Configured QPushButton
        """
        button = QPushButton(label)
        button.setObjectName("themeSwitcherButton")
        button.setCheckable(True)
        button.setProperty("theme", theme)
        button.setFixedHeight(24)
        button.setMinimumWidth(60)
        button.setCursor(Qt.PointingHandCursor)

        # Determine border radius based on position
        border_radius = "0px"
        if is_first:
            border_radius = "4px 0px 0px 4px"
        elif is_last:
            border_radius = "0px 4px 4px 0px"

        # Style for segmented control
        button.setStyleSheet(
            f"""
            QPushButton#themeSwitcherButton {{
                background-color: transparent;
                border: 1px solid {tokens.BORDER_UNFOCUSED};
                border-radius: {border_radius};
                color: {tokens.TEXT_SECONDARY};
                font-size: {tokens.FONT_SIZE_SMALL}px;
                padding: 4px 8px;
            }}
            QPushButton#themeSwitcherButton:hover {{
                background-color: {tokens.BACKGROUND_HOVER};
            }}
            QPushButton#themeSwitcherButton:checked {{
                background-color: {tokens.ACCENT_PRIMARY};
                color: {tokens.TEXT_INVERTED};
                border-color: {tokens.ACCENT_PRIMARY};
            }}
            """
        )

        self.button_group.addButton(button)
        return button

    def _on_button_clicked(self, button: QPushButton):
        """Handle button click.

        Args:
            button: Clicked button
        """
        theme = button.property("theme")
        if theme != self._current_theme:
            self._current_theme = theme
            self.theme_changed.emit(theme)

    def set_theme(self, theme: str):
        """Set the current theme.

        Args:
            theme: Theme identifier ("light", "system", "dark")
        """
        theme = theme.lower()
        if theme not in ("light", "system", "dark"):
            theme = "system"

        if theme != self._current_theme:
            self._current_theme = theme

            # Update button selection
            if theme == "light":
                self.light_button.setChecked(True)
            elif theme == "dark":
                self.dark_button.setChecked(True)
            else:
                self.system_button.setChecked(True)

    def get_theme(self) -> str:
        """Get the current theme.

        Returns:
            Current theme identifier
        """
        return self._current_theme
