"""Session state management for Streamlit dashboard."""

from __future__ import annotations

import platform
from typing import Any, Optional

import streamlit as st


def get_default_ocr_params() -> dict[str, Any]:
    """Get default OCR parameters."""
    return {
        "psm_mode": 7,
        "char_whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ",
        "enable_grayscale": True,
        "enable_bilateral": False,
        "bilateral_d": 9,
        "bilateral_sigma_color": 75,
        "bilateral_sigma_space": 75,
        "enable_adaptive_threshold": False,
        "adaptive_block_size": 11,
        "adaptive_c": 2,
        "enable_clahe": False,
        "clahe_clip_limit": 2.0,
        "clahe_tile_size": 8,
        "to_uppercase": True,
        "strip_whitespace": True,
        "min_text_length": 3,
        "substitute_o_to_0": False,
        "substitute_i_to_1": False,
        "crop_margin_px": 8,
        "upscale_factor": 1,
    }


def get_default_presets() -> dict[str, dict]:
    """Get default OCR presets."""
    return {
        "Fast (Grayscale Only)": {
            **get_default_ocr_params(),
            "enable_grayscale": True,
            "enable_bilateral": False,
            "enable_adaptive_threshold": False,
            "enable_clahe": False,
        },
        "Balanced (Adaptive)": {
            **get_default_ocr_params(),
            "enable_grayscale": True,
            "enable_adaptive_threshold": True,
        },
        "High Quality (Full Pipeline)": {
            **get_default_ocr_params(),
            "psm_mode": 6,
            "enable_grayscale": True,
            "enable_bilateral": True,
            "enable_adaptive_threshold": True,
        },
        "Night/Low Light": {
            **get_default_ocr_params(),
            "enable_grayscale": True,
            "enable_clahe": True,
            "enable_adaptive_threshold": True,
        },
    }


def init_session_state() -> None:
    """Initialize default session_state keys."""
    # Mode selection (Standalone or Client)
    if "mode" not in st.session_state:
        st.session_state.mode = "Standalone"

    # API client settings
    if "api_url" not in st.session_state:
        st.session_state.api_url = "http://localhost:8000"

    if "api_auth_token" not in st.session_state:
        st.session_state.api_auth_token = ""

    if "connected" not in st.session_state:
        st.session_state.connected = False

    if "source_type" not in st.session_state:
        st.session_state.source_type = "device"

    if "device_index" not in st.session_state:
        st.session_state.device_index = 0

    if "device_backend" not in st.session_state:
        # Pre-fill AVFOUNDATION on macOS
        st.session_state.device_backend = "AVFOUNDATION" if platform.system() == "Darwin" else ""

    if "rtsp_url" not in st.session_state:
        st.session_state.rtsp_url = "rtsp://"

    if "http_url" not in st.session_state:
        st.session_state.http_url = "http://"

    if "file_path" not in st.session_state:
        st.session_state.file_path = ""

    if "fps_target" not in st.session_state:
        st.session_state.fps_target = 15

    if "ui_refresh_fps" not in st.session_state:
        st.session_state.ui_refresh_fps = (
            10  # UI refresh rate (higher for smoother video, but may cause page flashing)
        )
    else:
        try:
            current = int(st.session_state.ui_refresh_fps)
        except (TypeError, ValueError):
            current = 10
        st.session_state.ui_refresh_fps = max(1, min(10, current))

    if "auto_refresh_enabled" not in st.session_state:
        st.session_state.auto_refresh_enabled = True  # Enable auto-refresh by default

    if "frame_resize" not in st.session_state:
        st.session_state.frame_resize = None

    if "ocr_params" not in st.session_state:
        st.session_state.ocr_params = get_default_ocr_params()

    if "ocr_presets" not in st.session_state:
        st.session_state.ocr_presets = get_default_presets()

    if "plates_enabled" not in st.session_state:
        st.session_state.plates_enabled = True

    if "model_path" not in st.session_state:
        st.session_state.model_path = "./weights/yolov8n_plate.pt"

    if "latest_frame" not in st.session_state:
        st.session_state.latest_frame = None

    if "latest_face_matches" not in st.session_state:
        st.session_state.latest_face_matches = []

    if "latest_face_observations" not in st.session_state:
        st.session_state.latest_face_observations = []

    if "latest_plate_reads" not in st.session_state:
        st.session_state.latest_plate_reads = []

    # Legacy field for backwards compatibility
    if "latest_detections" not in st.session_state:
        st.session_state.latest_detections = []

    if "latest_preview_image" not in st.session_state:
        st.session_state.latest_preview_image = None
    if "latest_detection_counts" not in st.session_state:
        st.session_state.latest_detection_counts = {"known": 0, "unknown": 0, "plates": 0}

    if "capture_stats" not in st.session_state:
        st.session_state.capture_stats = {"fps": 0.0, "frame_count": 0}

    # API client event caches (for Client mode)
    if "api_face_events" not in st.session_state:
        st.session_state.api_face_events = []

    if "api_plate_events" not in st.session_state:
        st.session_state.api_plate_events = []

    # Face recognition settings
    if "face_similarity_threshold" not in st.session_state:
        st.session_state.face_similarity_threshold = 0.35  # Default from config

    # Tracking settings (multi-frame confirmation)
    if "tracking_enabled" not in st.session_state:
        st.session_state.tracking_enabled = True

    if "tracking_frames_required" not in st.session_state:
        st.session_state.tracking_frames_required = 3

    if "tracking_iou_threshold" not in st.session_state:
        st.session_state.tracking_iou_threshold = 0.5

    if "tracking_max_age_frames" not in st.session_state:
        st.session_state.tracking_max_age_frames = 30

    if "tracking_ocr_agreement_threshold" not in st.session_state:
        st.session_state.tracking_ocr_agreement_threshold = 0.6


def save_preset(name: str, params: dict) -> None:
    """Save OCR preset to session state."""
    if "ocr_presets" not in st.session_state:
        st.session_state.ocr_presets = {}

    st.session_state.ocr_presets[name] = params.copy()


def load_preset(name: str) -> Optional[dict]:
    """Load OCR preset from session state."""
    if "ocr_presets" not in st.session_state:
        return None

    return st.session_state.ocr_presets.get(name)
