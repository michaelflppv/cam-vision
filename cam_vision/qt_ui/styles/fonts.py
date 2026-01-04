"""Platform-specific font selection for the monochromatic Qt UI.

Provides runtime detection of the operating system and returns
the appropriate system sans-serif font to achieve a native look.
"""

import platform

from . import tokens


def get_system_font() -> str:
    """Get the platform-appropriate system sans-serif font.

    Returns:
        Font family string suitable for Qt stylesheets and QFont

    Platform mappings:
        - macOS: SF Pro Display (San Francisco)
        - Windows: Segoe UI
        - Linux: Ubuntu/Roboto with fallbacks
        - Unknown: Arial fallback
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        return tokens.FONT_FAMILY_MAC
    elif system == "Windows":
        return tokens.FONT_FAMILY_WIN
    elif system == "Linux":
        return tokens.FONT_FAMILY_LINUX
    else:
        # Fallback for unknown platforms
        return tokens.FONT_FAMILY_FALLBACK


def get_system_font_name() -> str:
    """Get just the primary font name for the current platform.

    Returns:
        Primary font name (e.g., "SF Pro Display", "Segoe UI", "Ubuntu")
    """
    system = platform.system()

    if system == "Darwin":
        return "SF Pro Display"
    elif system == "Windows":
        return "Segoe UI"
    elif system == "Linux":
        return "Ubuntu"
    else:
        return "Arial"
