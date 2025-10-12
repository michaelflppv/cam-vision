"""Face match results display component."""

from __future__ import annotations

import cv2
import numpy as np
import streamlit as st

from cam_vision.types import FaceMatch, Frame


def render_face_panel(
    face_matches: list[FaceMatch], frame: Frame, similarity_threshold: float = 0.35
):
    """
    Render face match results panel.

    Shows matched faces with person names, similarity scores, and cropped images.

    Args:
        face_matches: List of FaceMatch objects
        frame: Frame containing the source image
        similarity_threshold: Threshold for similarity score coloring
    """
    st.subheader("Face Matches")

    if not face_matches:
        st.info("👤 No faces matched. Waiting for recognized persons...")
        return

    # Show last 5 matches
    for i, match in enumerate(reversed(face_matches[-5:])):
        # Color code based on similarity score
        if match.similarity >= similarity_threshold + 0.15:
            badge_color = "🟢"  # High confidence (green)
        elif match.similarity >= similarity_threshold:
            badge_color = "🟡"  # Medium confidence (amber)
        else:
            badge_color = "🔴"  # Low confidence (red - shouldn't happen if threshold works)

        with st.expander(
            f"{badge_color} {match.person_id} (similarity: {match.similarity:.3f})",
            expanded=(i == 0),
        ):
            col1, col2 = st.columns([1, 2])

            with col1:
                # Extract and display cropped face
                face_crop = _extract_crop(frame.image, match.detection.bbox)
                if face_crop is not None:
                    # Convert BGR to RGB for display
                    face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
                    st.image(face_rgb, caption="Detected Face", use_container_width=True)

            with col2:
                # Match details
                st.markdown(f"**Person:** {match.person_id}")
                st.markdown(f"**Similarity:** {match.similarity:.3f}")

                # Confidence progress bar
                st.progress(
                    min(1.0, match.similarity),
                    text=f"Confidence: {match.similarity*100:.1f}%",
                )

                # Detection metrics
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Detection Score", f"{match.detection.score:.3f}")
                with col_b:
                    bbox_size = match.detection.bbox.width() * match.detection.bbox.height()
                    st.metric("Face Size (px²)", f"{bbox_size}")

                # Confidence assessment
                if match.similarity >= similarity_threshold + 0.15:
                    st.success("✓ High Confidence Match")
                elif match.similarity >= similarity_threshold:
                    st.warning("~ Medium Confidence Match")
                else:
                    st.error("✗ Low Confidence (below threshold)")

                # Track ID (for future multi-frame confirmation)
                if match.detection.track_id is not None:
                    st.caption(f"Track ID: {match.detection.track_id}")


def _extract_crop(image: np.ndarray, bbox) -> np.ndarray:
    """
    Extract cropped region from image.

    Args:
        image: Source image
        bbox: BBox object with coordinates

    Returns:
        Cropped image or None on failure
    """
    try:
        h, w = image.shape[:2]
        x1 = max(0, bbox.x1)
        y1 = max(0, bbox.y1)
        x2 = min(w, bbox.x2)
        y2 = min(h, bbox.y2)

        return image[y1:y2, x1:x2]
    except Exception:
        return None
