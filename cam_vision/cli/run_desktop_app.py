#!/usr/bin/env python3
"""Launch the SecureVision desktop app with bundled services."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from threading import Thread
from typing import Optional

import uvicorn

from ..api.app import create_app
from ..config import load_settings
from ..utils.resources import get_app_data_dir, get_bundled_path, sync_bundled_data
from . import run_qt_ui

logger = logging.getLogger(__name__)


def _configure_environment() -> None:
    """Configure runtime paths for bundled resources."""
    data_dir = get_app_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    sync_bundled_data(data_dir)

    weights_dir = get_bundled_path("weights")
    if not weights_dir.exists():
        logger.warning("Bundled weights directory not found at %s", weights_dir)

    os.environ.setdefault(
        "SECUREVISION__PLATES__DETECTOR__MODEL_PATH",
        str(weights_dir / "yolov8n_plate.pt"),
    )
    os.environ.setdefault(
        "SECUREVISION__FACE__GALLERY_PATH",
        str(data_dir / "faces" / "trusted"),
    )
    os.environ.setdefault(
        "SECUREVISION__FACE__GALLERY_CACHE",
        str(data_dir / "faces" / "gallery.npz"),
    )
    os.environ.setdefault(
        "SECUREVISION__PLATES__WHITELIST_PATH",
        str(data_dir / "plates" / "whitelist.csv"),
    )
    os.environ.setdefault(
        "SECUREVISION__PLATES__BLACKLIST_PATH",
        str(data_dir / "plates" / "blacklist.csv"),
    )
    os.environ.setdefault(
        "SECUREVISION__EVENTS__DB_URL",
        f"sqlite:///{data_dir / 'events.db'}",
    )

    Path(os.environ["SECUREVISION__FACE__GALLERY_PATH"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["SECUREVISION__PLATES__WHITELIST_PATH"]).parent.mkdir(
        parents=True, exist_ok=True
    )

    insightface_dir = get_bundled_path("insightface")
    if insightface_dir.exists():
        os.environ.setdefault("INSIGHTFACE_HOME", str(insightface_dir))

    _configure_tesseract(get_bundled_path("tesseract"))


def _configure_tesseract(tesseract_root: Path) -> None:
    """Configure tesseract binaries and tessdata if bundled."""
    if not tesseract_root.exists():
        logger.warning("Bundled tesseract not found at %s", tesseract_root)
        return

    bin_dir = tesseract_root / "bin"
    if sys.platform.startswith("win"):
        tesseract_cmd = bin_dir / "tesseract.exe"
    else:
        tesseract_cmd = bin_dir / "tesseract"

    if tesseract_cmd.exists():
        try:
            tesseract_cmd.chmod(tesseract_cmd.stat().st_mode | 0o111)
        except OSError:
            logger.debug("Unable to update tesseract executable permissions", exc_info=True)
        os.environ.setdefault("SECUREVISION__TESSERACT_CMD", str(tesseract_cmd))
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    tessdata_dir = tesseract_root / "share" / "tessdata"
    if not tessdata_dir.exists():
        tessdata_dir = tesseract_root / "tessdata"
    if tessdata_dir.exists():
        os.environ.setdefault("TESSDATA_PREFIX", str(tessdata_dir.parent))

    lib_dir = tesseract_root / "lib"
    if lib_dir.exists():
        if sys.platform == "darwin":
            env_key = "DYLD_LIBRARY_PATH"
        elif sys.platform.startswith("linux"):
            env_key = "LD_LIBRARY_PATH"
        else:
            env_key = ""

        if env_key:
            os.environ[env_key] = f"{lib_dir}{os.pathsep}{os.environ.get(env_key, '')}"


def _start_api_server() -> tuple[uvicorn.Server, Thread]:
    """Start the FastAPI server in a background thread."""
    settings = load_settings()
    app = create_app(settings)
    config = uvicorn.Config(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True)
    thread.start()
    return server, thread


def main() -> int:
    """Launch the combined desktop application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    _configure_environment()

    server: Optional[uvicorn.Server] = None
    thread: Optional[Thread] = None
    try:
        server, thread = _start_api_server()
        return run_qt_ui.launch()
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=5)


if __name__ == "__main__":
    sys.exit(main())
