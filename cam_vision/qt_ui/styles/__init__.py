"""Styling system for the monochromatic Qt UI.

Provides:
- Design tokens (colors, typography, spacing)
- Platform-specific font selection
- Master stylesheet (QSS) loader
"""

from pathlib import Path


def load_stylesheet() -> str:
    """Load the master stylesheet (QSS) from file.

    Returns:
        QSS stylesheet string with monochromatic design tokens applied
    """
    stylesheet_path = Path(__file__).parent / "stylesheet.qss"
    if stylesheet_path.exists():
        return stylesheet_path.read_text()
    return ""
