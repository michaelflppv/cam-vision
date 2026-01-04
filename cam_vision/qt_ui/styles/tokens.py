"""Design tokens for the strict monochromatic Qt UI.

All visual design constants are centralized here to enforce consistency.
Color tokens can be swapped to support light/dark themes while preserving
the monochromatic design system.
"""

from __future__ import annotations

from typing import Dict, Iterable

# ============================================================================
# Color Palette - Monochromatic Only (Theme Aware)
# ============================================================================

_COLOR_TOKEN_NAMES: Iterable[str] = (
    "BACKGROUND_PRIMARY",
    "BACKGROUND_SUBTLE",
    "BACKGROUND_HOVER",
    "BACKGROUND_WINDOW_GRADIENT_END",
    "BACKGROUND_SIDEBAR_GRADIENT_END",
    "BACKGROUND_CONTENT_GRADIENT_END",
    "TEXT_PRIMARY",
    "TEXT_SECONDARY",
    "TEXT_TERTIARY",
    "TEXT_INVERTED",
    "BORDER_UNFOCUSED",
    "BORDER_FOCUSED",
    "BORDER_DIVIDER",
    "ACCENT_PRIMARY",
    "ACCENT_PRIMARY_HOVER",
    "ACCENT_PRIMARY_PRESSED",
    "ACCENT_SUCCESS",
    "ACCENT_WARNING",
    "ACCENT_ERROR",
    "ACCENT_INFO",
    "ACCENT_NEUTRAL",
    "CLOSE_BUTTON_HOVER",
    "TOOLTIP_BACKGROUND",
    "TOOLTIP_TEXT",
    "TITLEBAR_CLOSE_BG",
    "TITLEBAR_CLOSE_BORDER",
    "TITLEBAR_MINIMIZE_BG",
    "TITLEBAR_MINIMIZE_BORDER",
    "TITLEBAR_MAXIMIZE_BG",
    "TITLEBAR_MAXIMIZE_BORDER",
    "TITLEBAR_CLOSE_HOVER_BG",
    "TITLEBAR_MINIMIZE_HOVER_BG",
    "TITLEBAR_MAXIMIZE_HOVER_BG",
    "TITLEBAR_BUTTON_BORDER",
    "TITLEBAR_BUTTON_SYMBOL",
    "THUMBNAIL_BACKGROUND",
)

_LIGHT_THEME: Dict[str, str] = {
    # Backgrounds
    "BACKGROUND_PRIMARY": "#FFFFFF",
    "BACKGROUND_SUBTLE": "#F5F5F5",
    "BACKGROUND_HOVER": "#F5F5F5",
    "BACKGROUND_WINDOW_GRADIENT_END": "#F2F2F2",
    "BACKGROUND_SIDEBAR_GRADIENT_END": "#F6F6F6",
    "BACKGROUND_CONTENT_GRADIENT_END": "#F7F7F7",
    # Text
    "TEXT_PRIMARY": "#000000",
    "TEXT_SECONDARY": "#888888",
    "TEXT_TERTIARY": "#AAAAAA",
    "TEXT_INVERTED": "#FFFFFF",
    # Borders
    "BORDER_UNFOCUSED": "#E0E0E0",
    "BORDER_FOCUSED": "#000000",
    "BORDER_DIVIDER": "#E0E0E0",
    # Primary Actions
    "ACCENT_PRIMARY": "#000000",
    "ACCENT_PRIMARY_HOVER": "#333333",
    "ACCENT_PRIMARY_PRESSED": "#666666",
    # Status Colors
    "ACCENT_SUCCESS": "#00CC00",
    "ACCENT_WARNING": "#FFA500",
    "ACCENT_ERROR": "#FF0000",
    "ACCENT_INFO": "#0066CC",
    "ACCENT_NEUTRAL": "#888888",
    # Special
    "CLOSE_BUTTON_HOVER": "#FF0000",
    "TOOLTIP_BACKGROUND": "#000000",
    "TOOLTIP_TEXT": "#FFFFFF",
    # Title bar controls (macOS)
    "TITLEBAR_CLOSE_BG": "#FF5F57",
    "TITLEBAR_CLOSE_BORDER": "#E0443E",
    "TITLEBAR_MINIMIZE_BG": "#FFBD2E",
    "TITLEBAR_MINIMIZE_BORDER": "#DEA123",
    "TITLEBAR_MAXIMIZE_BG": "#28C940",
    "TITLEBAR_MAXIMIZE_BORDER": "#1BAC2E",
    "TITLEBAR_CLOSE_HOVER_BG": "#FF3B30",
    "TITLEBAR_MINIMIZE_HOVER_BG": "#FFB000",
    "TITLEBAR_MAXIMIZE_HOVER_BG": "#20B53A",
    "TITLEBAR_BUTTON_BORDER": "rgba(0, 0, 0, 0.15)",
    "TITLEBAR_BUTTON_SYMBOL": "rgba(0, 0, 0, 0.7)",
    # Thumbnails
    "THUMBNAIL_BACKGROUND": "#000000",
}

_DARK_THEME: Dict[str, str] = {
    # Backgrounds
    "BACKGROUND_PRIMARY": "#0F0F0F",
    "BACKGROUND_SUBTLE": "#1A1A1A",
    "BACKGROUND_HOVER": "#222222",
    "BACKGROUND_WINDOW_GRADIENT_END": "#141414",
    "BACKGROUND_SIDEBAR_GRADIENT_END": "#161616",
    "BACKGROUND_CONTENT_GRADIENT_END": "#181818",
    # Text
    "TEXT_PRIMARY": "#F5F5F5",
    "TEXT_SECONDARY": "#B0B0B0",
    "TEXT_TERTIARY": "#888888",
    "TEXT_INVERTED": "#0F0F0F",
    # Borders
    "BORDER_UNFOCUSED": "#2A2A2A",
    "BORDER_FOCUSED": "#F5F5F5",
    "BORDER_DIVIDER": "#2A2A2A",
    # Primary Actions
    "ACCENT_PRIMARY": "#F5F5F5",
    "ACCENT_PRIMARY_HOVER": "#FFFFFF",
    "ACCENT_PRIMARY_PRESSED": "#D6D6D6",
    # Status Colors
    "ACCENT_SUCCESS": "#2EDC6E",
    "ACCENT_WARNING": "#FFB347",
    "ACCENT_ERROR": "#FF5C5C",
    "ACCENT_INFO": "#4DA3FF",
    "ACCENT_NEUTRAL": "#B0B0B0",
    # Special
    "CLOSE_BUTTON_HOVER": "#FF5C5C",
    "TOOLTIP_BACKGROUND": "#F5F5F5",
    "TOOLTIP_TEXT": "#111111",
    # Title bar controls (macOS)
    "TITLEBAR_CLOSE_BG": "#FF5F57",
    "TITLEBAR_CLOSE_BORDER": "#E0443E",
    "TITLEBAR_MINIMIZE_BG": "#FFBD2E",
    "TITLEBAR_MINIMIZE_BORDER": "#DEA123",
    "TITLEBAR_MAXIMIZE_BG": "#28C940",
    "TITLEBAR_MAXIMIZE_BORDER": "#1BAC2E",
    "TITLEBAR_CLOSE_HOVER_BG": "#FF3B30",
    "TITLEBAR_MINIMIZE_HOVER_BG": "#FFB000",
    "TITLEBAR_MAXIMIZE_HOVER_BG": "#20B53A",
    "TITLEBAR_BUTTON_BORDER": "rgba(255, 255, 255, 0.2)",
    "TITLEBAR_BUTTON_SYMBOL": "rgba(0, 0, 0, 0.75)",
    # Thumbnails
    "THUMBNAIL_BACKGROUND": "#000000",
}


def apply_theme(theme: str) -> str:
    """Apply the selected color theme to module-level tokens."""
    palette_name = theme.lower()
    if palette_name == "dark":
        palette = _DARK_THEME
    else:
        palette_name = "light"
        palette = _LIGHT_THEME

    globals().update(palette)
    return palette_name


def get_color_tokens() -> Dict[str, str]:
    """Return the current theme color tokens for QSS templating."""
    return {token: globals()[token] for token in _COLOR_TOKEN_NAMES}


# Initialize with the light theme by default.
apply_theme("light")

# ============================================================================
# Typography - System Fonts Only
# ============================================================================

# Font Families (platform-specific, see fonts.py for runtime selection)
FONT_FAMILY_MAC = "SF Pro Display, -apple-system, BlinkMacSystemFont, sans-serif"
FONT_FAMILY_WIN = "Segoe UI, Tahoma, Geneva, Verdana, sans-serif"
FONT_FAMILY_LINUX = "Ubuntu, Roboto, 'Open Sans', Arial, sans-serif"
FONT_FAMILY_FALLBACK = "Arial, sans-serif"

# Font Sizes
FONT_SIZE_TINY = 8  # px - very small labels
FONT_SIZE_SMALL = 10  # px - stat labels, badges
FONT_SIZE_NORMAL = 12  # px - body text, inputs, buttons
FONT_SIZE_LARGE = 14  # px - headings, emphasis
FONT_SIZE_XLARGE = 16  # px - section titles
FONT_SIZE_STAT_LABEL = 10  # px - stat card labels (uppercase)
FONT_SIZE_STAT_VALUE = 24  # px - stat card values (bold)
FONT_SIZE_HEADING = 16  # px - panel headings

# Font Weights
FONT_WEIGHT_NORMAL = 400  # Regular
FONT_WEIGHT_MEDIUM = 500  # Medium (slight emphasis)
FONT_WEIGHT_BOLD = 600  # Bold (headings, emphasis)

# ============================================================================
# Spacing - Generous Whitespace
# ============================================================================

# Internal Padding
PADDING_TINY = 4  # px - minimal padding
PADDING_SMALL = 8  # px - compact padding
PADDING_MEDIUM = 12  # px - standard padding
PADDING_LARGE = 16  # px - generous padding (default)
PADDING_XLARGE = 20  # px - extra generous padding
PADDING_XXLARGE = 24  # px - maximum padding

# Item Spacing (gaps between elements)
SPACING_TIGHT = 4  # px - tight spacing
SPACING_NORMAL = 8  # px - standard spacing
SPACING_COMFORTABLE = 12  # px - comfortable spacing
SPACING_LOOSE = 16  # px - loose spacing

# Section Spacing
MARGIN_SECTION = 12  # px - margin between cards/sections
MARGIN_PANEL = 16  # px - margin around panels

# ============================================================================
# Component Dimensions
# ============================================================================

# Borders
BORDER_WIDTH = 1  # px - standard border width
BORDER_RADIUS = 0  # px - ZERO EVERYWHERE (strict requirement)

# Buttons
BUTTON_HEIGHT = 32  # px - standard button height
BUTTON_HEIGHT_SMALL = 24  # px - compact button
BUTTON_HEIGHT_LARGE = 40  # px - prominent button
BUTTON_PADDING_HORIZONTAL = 16  # px - horizontal button padding
BUTTON_PADDING_VERTICAL = 8  # px - vertical button padding

# Inputs
INPUT_HEIGHT = 32  # px - standard input height
INPUT_PADDING_HORIZONTAL = 12  # px - horizontal input padding
INPUT_PADDING_VERTICAL = 6  # px - vertical input padding

# Sliders
SLIDER_HANDLE_SIZE = 16  # px - slider handle (square)
SLIDER_GROOVE_HEIGHT = 4  # px - slider track height
SLIDER_MARGIN_VERTICAL = 6  # px - margin around handle

# Progress Bars
PROGRESSBAR_HEIGHT = 20  # px - standard progress bar height
PROGRESSBAR_HEIGHT_THIN = 12  # px - thin progress bar

# Cards
CARD_PADDING = 16  # px - internal card padding
CARD_MARGIN_BOTTOM = 12  # px - margin between stacked cards

# Stats Cards
STAT_CARD_HEIGHT = 80  # px - fixed height for stat cards
STAT_CARD_PADDING = 16  # px - internal padding

# Title Bar
TITLEBAR_HEIGHT = 40  # px - custom title bar height
TITLEBAR_BUTTON_SIZE = 12  # px - min/max/close button size

# Sidebar
SIDEBAR_WIDTH = 380  # px - fixed sidebar width

# Badges
BADGE_CIRCLE_SIZE = 8  # px - status indicator circle diameter
BADGE_SPACING = 6  # px - spacing between circle and text

# Detection Cards
DETECTION_IMAGE_SIZE = 120  # px - square image size
DETECTION_IMAGE_WIDTH_RATIO = 0.33  # Image takes 1/3 width
DETECTION_DETAILS_WIDTH_RATIO = 0.67  # Details take 2/3 width

# Scroll Bars
SCROLLBAR_WIDTH = 12  # px - vertical scrollbar width
SCROLLBAR_HANDLE_MIN_HEIGHT = 20  # px - minimum handle size

# Size Grip
SIZE_GRIP_SIZE = 16  # px - resize grip size

# ============================================================================
# Animation Timing
# ============================================================================

ANIMATION_DURATION_FAST = 150  # ms - quick transitions
ANIMATION_DURATION_NORMAL = 300  # ms - standard animations
ANIMATION_DURATION_SLOW = 500  # ms - slow, prominent animations

# Animation Curves (Qt easing)
ANIMATION_CURVE = "ease-in-out"  # CSS easing for QPropertyAnimation

# ============================================================================
# Z-Index Layers
# ============================================================================

Z_INDEX_BASE = 0  # Base layer
Z_INDEX_CONTENT = 1  # Content layer
Z_INDEX_OVERLAY = 10  # Overlays and tooltips
Z_INDEX_MODAL = 100  # Modal dialogs
Z_INDEX_TITLEBAR = 1000  # Custom title bar (always on top)

# ============================================================================
# Shadows - DISABLED (flat design)
# ============================================================================

# All shadows are disabled for strict flat geometry
# No box-shadow, no drop-shadow, no text-shadow
SHADOW_NONE = "none"
