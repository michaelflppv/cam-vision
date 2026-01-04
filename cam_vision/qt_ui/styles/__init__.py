"""Styling system for the monochromatic Qt UI.

Provides:
- Design tokens (colors, typography, spacing)
- Platform-specific font selection
- Theme-aware stylesheet (QSS) loader
"""

from pathlib import Path
from string import Template

from . import tokens


def load_stylesheet() -> str:
    """Load the master stylesheet (QSS) and substitute theme tokens.

    Returns:
        QSS stylesheet string with monochromatic design tokens applied
    """
    stylesheet_path = Path(__file__).parent / "stylesheet.qss"
    if stylesheet_path.exists():
        template = Template(stylesheet_path.read_text())
        return template.safe_substitute(tokens.get_color_tokens())
    return ""
