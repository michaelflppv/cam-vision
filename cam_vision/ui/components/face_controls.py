"""Face recognition controls component."""

import streamlit as st


def render_face_controls() -> float:
    """
    Render face recognition control panel.

    Returns:
        Selected similarity threshold (0.0-1.0)
    """
    st.markdown("**Similarity Threshold**")
    st.caption(
        "Minimum similarity score (0.0-1.0) for face matching. "
        "Lower = stricter (fewer false positives), Higher = lenient (more matches)."
    )

    # Slider for threshold
    threshold = st.slider(
        "Threshold",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.face_similarity_threshold,
        step=0.05,
        key="face_threshold_slider",
        help="Lower values require stronger similarity for a match. Recommended: 0.30-0.40",
        label_visibility="collapsed",
    )

    # Update session state
    st.session_state.face_similarity_threshold = threshold

    # Show interpretation
    if threshold < 0.25:
        st.warning("⚠️ Very strict - May miss valid matches")
        interpretation = "Very Strict"
    elif threshold < 0.35:
        st.info("ℹ️ Strict - Good for high security")
        interpretation = "Strict"
    elif threshold < 0.45:
        st.success("✓ Balanced - Recommended")
        interpretation = "Balanced"
    elif threshold < 0.55:
        st.info("ℹ️ Lenient - More matches")
        interpretation = "Lenient"
    else:
        st.warning("⚠️ Very lenient - May produce false positives")
        interpretation = "Very Lenient"

    # Show current value
    st.markdown(f"**Current:** {threshold:.2f} ({interpretation})")

    st.divider()

    # Quick presets
    st.markdown("**Quick Presets:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Strict\n(0.30)", width="stretch"):
            st.session_state.face_similarity_threshold = 0.30
            st.rerun()

    with col2:
        if st.button("Balanced\n(0.35)", width="stretch"):
            st.session_state.face_similarity_threshold = 0.35
            st.rerun()

    with col3:
        if st.button("Lenient\n(0.45)", width="stretch"):
            st.session_state.face_similarity_threshold = 0.45
            st.rerun()

    # Note about real-time updates
    st.caption(
        "⚠️ Note: Threshold changes apply to new detections only. "
        "Restart capture to apply to all frames."
    )

    return threshold
