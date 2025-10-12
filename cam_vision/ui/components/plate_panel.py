"""Plate detection results display component."""

from __future__ import annotations

import cv2
import numpy as np
import streamlit as st

from cam_vision.types import Frame, PlateRead


def render_plate_panel(plate_reads: list[PlateRead], frame: Frame):
    """
    Render plate detection results with full metrics.

    Shows matched plates with OCR results, detector/OCR confidences, and list matches.

    Args:
        plate_reads: List of PlateRead objects
        frame: Frame containing the source image
    """
    st.subheader("Plate Detections")

    if not plate_reads:
        st.info("🚗 No plates detected yet. Waiting for vehicles...")
        return

    # Show last 5 detections
    for i, plate in enumerate(reversed(plate_reads[-5:])):
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

        with st.expander(
            f"{icon} {plate.text_clean} ({list_status})",
            expanded=(i == 0),
        ):
            col1, col2 = st.columns([1, 2])

            with col1:
                # Extract and display cropped plate
                plate_crop = _extract_crop(frame.image, plate.detection.bbox)
                if plate_crop is not None:
                    # Convert BGR to RGB for display
                    plate_rgb = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2RGB)
                    st.image(plate_rgb, caption="Detected Plate", use_container_width=True)

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
                    st.metric("Detector Score", f"{plate.detection.score:.3f}")
                    bbox_size = plate.detection.bbox.width() * plate.detection.bbox.height()
                    st.metric("Plate Size (px²)", f"{bbox_size}")

                with col_b:
                    st.metric("OCR Confidence", f"{plate.confidence:.1f}%")
                    aspect_ratio = (
                        plate.detection.bbox.width() / plate.detection.bbox.height()
                        if plate.detection.bbox.height() > 0
                        else 0
                    )
                    st.metric("Aspect Ratio", f"{aspect_ratio:.2f}")

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

                # Track ID (for future multi-frame confirmation)
                if plate.detection.track_id is not None:
                    st.caption(f"Track ID: {plate.detection.track_id}")


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
