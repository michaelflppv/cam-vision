"""Design tokens for the strict monochromatic Qt UI.

All visual design constants are centralized here to enforce consistency:
- Pure white background (#FFFFFF)
- Absolute black for primary actions (#000000)
- Subtle gray for unfocused states (#E0E0E0)
- Zero border-radius on ALL elements
- Generous padding and spacing
"""

# ============================================================================
# Color Palette - Monochromatic Only
# ============================================================================

# Backgrounds
BACKGROUND_PRIMARY = "#FFFFFF"  # Pure white - main background
BACKGROUND_SUBTLE = "#F5F5F5"  # Subtle gray - for cards and secondary surfaces
BACKGROUND_HOVER = "#F5F5F5"  # Light gray hover state

# Text
TEXT_PRIMARY = "#000000"  # Absolute black - primary text and headings
TEXT_SECONDARY = "#888888"  # Medium gray - secondary text and labels
TEXT_TERTIARY = "#AAAAAA"  # Light gray - disabled or tertiary text
TEXT_INVERTED = "#FFFFFF"  # White text on dark backgrounds

# Borders
BORDER_UNFOCUSED = "#E0E0E0"  # Light gray - unfocused input borders
BORDER_FOCUSED = "#000000"  # Black - focused input borders
BORDER_DIVIDER = "#E0E0E0"  # Light gray - section dividers

# Primary Actions
ACCENT_PRIMARY = "#000000"  # Absolute black - primary action buttons
ACCENT_PRIMARY_HOVER = "#333333"  # Dark gray - primary hover state
ACCENT_PRIMARY_PRESSED = "#666666"  # Medium gray - primary pressed state

# Status Colors (minimal color for indicators only)
ACCENT_SUCCESS = "#00CC00"  # Green - success states
ACCENT_WARNING = "#FFA500"  # Amber - warning states
ACCENT_ERROR = "#FF0000"  # Red - error states
ACCENT_INFO = "#0066CC"  # Blue - informational states
ACCENT_NEUTRAL = "#888888"  # Gray - neutral states

# Special
CLOSE_BUTTON_HOVER = "#FF0000"  # Red - close button hover (only exception)

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
