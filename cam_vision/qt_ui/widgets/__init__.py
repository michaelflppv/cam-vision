"""Custom widgets for the monochromatic Qt UI.

All widgets follow strict design philosophy:
- Zero border-radius
- Sharp edges and flat geometry
- High contrast (black/white/gray only)
"""

from .theme_switcher import ThemeSwitcher

__all__ = ["ThemeSwitcher"]
