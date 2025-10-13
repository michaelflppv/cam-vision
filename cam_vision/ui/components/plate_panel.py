"""Plate detection results display component."""

from __future__ import annotations

import cv2
import numpy as np
import streamlit as st

from cam_vision.types import Frame, PlateObservation


def render_plate_panel(plate_observations: list[PlateObservation], frame: Frame):
    """
    Render plate detection results with full metrics.

    Shows recent plates with OCR results, detector/OCR confidences, and list matches.

    Args:
        plate_observations: List of PlateObservation objects
        frame: Frame containing the source image
    """
    panel = st.container()
    panel.subheader("Plate Detections")

    if not plate_observations:
        panel.info("🚗 No plates detected yet. Waiting for vehicles...")
        return

    # Show last 5 observations for each category
    recent_observations = list(reversed(plate_observations[-5:]))

    recognized = [obs for obs in recent_observations if obs.status == "read"]
    pending = [obs for obs in recent_observations if obs.status != "read" and obs.is_displayable()]

    if recognized:
        panel.markdown("### ✅ Recent Recognized Plates")

    for i, plate in enumerate(recognized):
        # Icon and color based on list match
        if plate.matched_list == "whitelist":
            icon = "✅"
            list_status = "Whitelist"
        elif plate.matched_list == "blacklist":
            icon = "🚫"
            list_status = "Blacklist"
        else:
            icon = "🚗"
            list_status = "Unknown"

        with panel.container():
            st.markdown(f"**{icon} {plate.text_clean}**  \nStatus: `{list_status}`")

            col1, col2 = st.columns([1, 2])

            with col1:
                # Extract and display cropped plate
                plate_crop = _extract_crop(frame.image, plate.detection.bbox)
                if plate_crop is not None:
                    # Convert BGR to RGB for display
                    plate_rgb = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2RGB)
                    st.image(plate_rgb, caption="Detected Plate", width="stretch")
                else:
                    st.caption("No crop available")

            with col2:
                # OCR results
                st.markdown(f"**Raw Text:** `{plate.text_raw}`")
                st.markdown(f"**Clean Text:** `{plate.text_clean}`")

                st.divider()

                # Detector confidence (YOLO score 0.0-1.0)
                st.markdown("**Detection Stage:**")
                st.progress(
                    min(1.0, plate.detection.score),
                    text=f"YOLO Confidence: {plate.detection.score*100:.1f}%",
                )

                # OCR confidence (Tesseract 0-100)
                st.markdown("**OCR Stage:**")
                st.progress(
                    min(1.0, plate.confidence / 100.0),
                    text=f"Tesseract Confidence: {plate.confidence:.1f}%",
                )

                st.divider()

                # Combined metrics
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Detector Score**")
                    st.markdown(f"{plate.detection.score:.3f}")
                    bbox_size = plate.detection.bbox.width() * plate.detection.bbox.height()
                    st.markdown("**Plate Size (px²)**")
                    st.markdown(f"{bbox_size}")

                with col_b:
                    st.markdown("**OCR Confidence**")
                    st.markdown(f"{plate.confidence:.1f}%")
                    aspect_ratio = (
                        plate.detection.bbox.width() / plate.detection.bbox.height()
                        if plate.detection.bbox.height() > 0
                        else 0
                    )
                    st.markdown("**Aspect Ratio**")
                    st.markdown(f"{aspect_ratio:.2f}")

                st.divider()

                # List match indicator
                if plate.matched_list == "whitelist":
                    st.success("✅ **Whitelist Match** - Authorized plate")
                elif plate.matched_list == "blacklist":
                    st.error("🚫 **Blacklist Match** - Blocked plate")
                else:
                    st.info("○ **Unknown Plate** - Not in lists")

                # Preprocessing info (debugging aid)
                if plate.preprocessing_used:
                    st.caption(f"🔧 Preprocessing: {plate.preprocessing_used}")

                st.divider()

                # Tracking info (multi-frame confirmation with OCR agreement)
                if plate.detection.track_id is not None:
                    st.info(
                        f"🎯 **Tracked Detection** (ID: {plate.detection.track_id})\n\n"
                        "This plate was confirmed across multiple consecutive frames with "
                        "consistent OCR text, reducing false positives."
                    )
                else:
                    st.caption("ℹ️ Single-frame detection (tracking disabled)")

        if i < len(recognized) - 1:
            panel.divider()

    if pending:
        panel.divider()
        panel.markdown("### 🔎 Pending OCR / Low Confidence")

        for j, obs in enumerate(pending):
            with panel.container():
                label = obs.label if obs.text_clean else "Unresolved Plate"
                status_label = obs.status.replace("_", " ")
                st.markdown(f"**🚗 {label}**  \nStatus: `{status_label}`")

                col1, col2 = st.columns([1, 2])

                with col1:
                    plate_crop = _extract_crop(frame.image, obs.detection.bbox)
                    if plate_crop is not None:
                        plate_rgb = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2RGB)
                        st.image(plate_rgb, caption="Detected Plate", width="stretch")
                    else:
                        st.caption("No crop available")

                with col2:
                    st.markdown("**Detection Stage:**")
                    st.progress(
                        min(1.0, obs.detection.score),
                        text=f"YOLO Confidence: {obs.detection.score*100:.1f}%",
                    )

                    st.markdown("**OCR Stage:**")
                    st.progress(
                        min(1.0, obs.confidence / 100.0),
                        text=f"Tesseract Confidence: {obs.confidence:.1f}%",
                    )

                    if obs.reason:
                        st.warning(f"Reason: {obs.reason}")
                    else:
                        st.caption("Awaiting stable OCR reading...")

                    st.divider()

                    col_a, col_b = st.columns(2)
                    with col_a:
                        bbox = obs.detection.bbox
                        bbox_size = bbox.width() * bbox.height()
                        st.markdown("**Plate Size (px²)**")
                        st.markdown(f"{bbox_size}")

                    with col_b:
                        aspect_ratio = (
                            obs.detection.bbox.width() / obs.detection.bbox.height()
                            if obs.detection.bbox.height() > 0
                            else 0
                        )
                        st.markdown("**Aspect Ratio**")
                        st.markdown(f"{aspect_ratio:.2f}")

                    if obs.preprocessing_used:
                        st.caption(f"🔧 Preprocessing: {obs.preprocessing_used}")

            if j < len(pending) - 1:
                panel.divider()


def _extract_crop(image: np.ndarray, bbox) -> np.ndarray:
    """Extract cropped region from image."""
    try:
        h, w = image.shape[:2]
        x1 = max(0, bbox.x1)
        y1 = max(0, bbox.y1)
        x2 = min(w, bbox.x2)
        y2 = min(h, bbox.y2)

        return image[y1:y2, x1:x2]
    except Exception:
        return None
