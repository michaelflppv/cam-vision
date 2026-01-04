"""Tracking and multi-frame confirmation controls component."""

from __future__ import annotations

import streamlit as st


def render_tracking_controls():
    """
    Render tracking configuration controls.

    Allows users to enable/disable tracking and adjust confirmation thresholds.
    """
    st.markdown("### Multi-Frame Tracking")

    # Enable/disable tracking
    tracking_enabled = st.checkbox(
        "Enable Tracking",
        value=st.session_state.get("tracking_enabled", True),
        key="tracking_enabled_checkbox",
        help=(
            "Enable multi-frame tracking and confirmation to reduce false positives. "
            "Requires K consecutive frame matches before emitting events."
        ),
    )
    st.session_state.tracking_enabled = tracking_enabled

    if not tracking_enabled:
        st.info("ℹ️ Tracking disabled - single-frame detection mode.")
        return

    st.divider()

    # Confirmation threshold (K frames)
    frames_required = st.slider(
        "Frames Required (K)",
        min_value=1,
        max_value=10,
        value=st.session_state.get("tracking_frames_required", 3),
        key="tracking_frames_required_slider",
        help=(
            "Number of consecutive frames required to confirm a detection. "
            "Higher values reduce false positives but may delay alerts. "
            "Recommended: 3-5 frames."
        ),
    )
    st.session_state.tracking_frames_required = frames_required

    # IoU threshold
    iou_threshold = st.slider(
        "IoU Threshold",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.get("tracking_iou_threshold", 0.5),
        step=0.05,
        key="tracking_iou_threshold_slider",
        help=(
            "Intersection-over-Union threshold for matching detections across frames. "
            "Higher values require more precise bbox overlap. "
            "Recommended: 0.4-0.6."
        ),
    )
    st.session_state.tracking_iou_threshold = iou_threshold

    # Max age (track expiration)
    max_age_frames = st.slider(
        "Max Age (frames)",
        min_value=10,
        max_value=120,
        value=st.session_state.get("tracking_max_age_frames", 30),
        step=5,
        key="tracking_max_age_frames_slider",
        help=(
            "Number of frames before a lost track expires. "
            "Higher values allow longer occlusions but use more memory. "
            "Recommended: 30-60 frames."
        ),
    )
    st.session_state.tracking_max_age_frames = max_age_frames

    st.divider()

    # OCR agreement threshold (plates only)
    st.markdown("**Plate-Specific Settings:**")
    ocr_agreement_threshold = st.slider(
        "OCR Agreement Threshold",
        min_value=0.1,
        max_value=1.0,
        value=st.session_state.get("tracking_ocr_agreement_threshold", 0.6),
        step=0.05,
        key="tracking_ocr_agreement_threshold_slider",
        help=(
            "Minimum agreement required for OCR text across frames (plates only). "
            "Uses majority voting on the last 10 OCR reads. "
            "Higher values reduce false positives from OCR errors. "
            "Recommended: 0.6 (60% agreement)."
        ),
    )
    st.session_state.tracking_ocr_agreement_threshold = ocr_agreement_threshold

    # Info about settings
    st.caption(
        f"ℹ️ Current: Tracking {'**enabled**' if tracking_enabled else '**disabled**'}. "
        f"Requires {frames_required} consecutive frames with IoU ≥ {iou_threshold:.2f}. "
        f"Plates require {ocr_agreement_threshold*100:.0f}% OCR agreement."
    )

    # Restart warning
    st.warning(
        "⚠️ **Note:** Tracking settings require reconnecting to take effect. "
        "Click 'Disconnect' then 'Connect' to apply changes."
    )
