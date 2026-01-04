"""Helpers for resolving bundled resources and writable app data paths."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_resource_root() -> Path:
    """Return the root directory for bundled resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    cwd = Path.cwd()
    if (cwd / "weights").exists() or (cwd / "data").exists():
        return cwd
    return Path(__file__).resolve().parents[3]


def get_bundled_path(name: str) -> Path:
    """Return a resource path from the bundle or repo."""
    root = get_resource_root()
    bundled = root / "resources" / name
    if bundled.exists():
        return bundled
    return root / name


def get_app_data_dir(app_name: str = "SecureVision") -> Path:
    """Return a writable per-user data directory for the app."""
    system = platform.system()
    home = Path.home()

    if system == "Darwin":
        base = home / "Library" / "Application Support"
    elif system == "Windows":
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))

    return base / app_name


def sync_bundled_data(target_dir: Path) -> None:
    """Copy bundled data files into the writable data directory if missing."""
    source_dir = get_bundled_path("data")
    if not source_dir.exists():
        logger.warning("Bundled data directory not found at %s", source_dir)
        return

    for item in source_dir.rglob("*"):
        relative = item.relative_to(source_dir)
        destination = target_dir / relative
        if item.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination)
