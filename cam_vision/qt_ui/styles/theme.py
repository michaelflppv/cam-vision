"""Theme resolution and application for the Qt UI."""

from __future__ import annotations

import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from . import tokens

logger = logging.getLogger(__name__)

THEME_ENV_VAR = "SECUREVISION__UI__THEME"
SUPPORTED_THEMES = {"light", "dark", "system"}


def get_requested_theme() -> str:
    """Read the requested theme from the environment."""
    return os.getenv(THEME_ENV_VAR, "system").strip().lower()


def resolve_theme(requested: str, app: QApplication) -> str:
    """Resolve a theme name to an actual palette name."""
    if requested not in SUPPORTED_THEMES:
        logger.warning("Unknown theme '%s'; falling back to system.", requested)
        requested = "system"

    if requested == "system":
        scheme = app.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
        if scheme == Qt.ColorScheme.Light:
            return "light"
        return "light"

    return requested


def apply_theme(app: QApplication, requested: str | None = None) -> str:
    """Apply the resolved theme to the token palette."""
    requested_theme = requested or get_requested_theme()
    resolved = resolve_theme(requested_theme, app)
    tokens.apply_theme(resolved)
    logger.info("Qt UI theme set to '%s' (requested '%s')", resolved, requested_theme)
    return resolved
