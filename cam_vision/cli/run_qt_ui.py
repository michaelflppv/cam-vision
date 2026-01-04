#!/usr/bin/env python3
"""Entry point for the SecureVision Qt dashboard.

Launches the PySide6-based monochromatic UI with strict design philosophy:
- Zero border-radius (sharp edges only)
- Pure white background with absolute black primary actions
- Flat geometry (no gradients, shadows, or bevels)
- Custom frameless window
"""

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ..qt_ui.main_window import SecureVisionMainWindow
from ..qt_ui.styles import load_stylesheet
from ..qt_ui.styles.fonts import get_system_font_name
from ..qt_ui.styles.theme import apply_theme
from ..qt_ui.styles.tokens import FONT_SIZE_NORMAL


def launch(app: QApplication | None = None) -> int:
    """Launch the Qt dashboard application."""
    owns_app = app is None
    if app is None:
        app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("SecureVision")
    app.setOrganizationName("SecureVision")
    app.setOrganizationDomain("securevision.local")

    # Set system font
    font = QFont(get_system_font_name(), FONT_SIZE_NORMAL)
    app.setFont(font)

    # Resolve and apply theme before loading styles
    apply_theme(app)

    # Load and apply global stylesheet
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)

    # Create and show main window
    window = SecureVisionMainWindow()
    window.show()

    if owns_app:
        return app.exec()
    return 0


def main():
    """Launch the Qt dashboard application."""
    sys.exit(launch())


if __name__ == "__main__":
    main()
