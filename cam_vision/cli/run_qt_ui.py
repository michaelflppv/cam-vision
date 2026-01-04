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
from ..qt_ui.styles.tokens import FONT_SIZE_NORMAL


def main():
    """Launch the Qt dashboard application."""
    # Create application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("SecureVision")
    app.setOrganizationName("SecureVision")
    app.setOrganizationDomain("securevision.local")

    # Set system font
    font = QFont(get_system_font_name(), FONT_SIZE_NORMAL)
    app.setFont(font)

    # Load and apply global stylesheet
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)

    # Create and show main window
    window = SecureVisionMainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
