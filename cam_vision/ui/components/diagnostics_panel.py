"""Diagnostics panel component for system status."""

import streamlit as st

from cam_vision.ui.diagnostics import SystemDiagnostics, run_diagnostics


def render_diagnostics_panel() -> None:
    """Render system diagnostics panel with feature status."""
    st.subheader("🔍 System Diagnostics")

    # Run button
    if st.button("Run System Check", type="primary", width="stretch"):
        with st.spinner("Checking system..."):
            diagnostics = run_diagnostics()
            st.session_state.last_diagnostics = diagnostics

    # Show last diagnostics if available
    if "last_diagnostics" not in st.session_state:
        st.info("Click 'Run System Check' to validate all features")
        return

    diagnostics: SystemDiagnostics = st.session_state.last_diagnostics

    # Overall status
    if diagnostics.all_ok():
        st.success("✅ All enabled features are available")
    else:
        failures = diagnostics.get_failures()
        st.error(f"❌ {len(failures)} feature(s) unavailable")

    # Feature status table
    st.divider()

    # Core features
    st.markdown("**Core Features**")
    _render_feature_status(diagnostics.face_recognition)
    _render_feature_status(diagnostics.plate_detection)

    st.divider()

    # Dependencies
    st.markdown("**Dependencies**")
    _render_feature_status(diagnostics.gallery)
    _render_feature_status(diagnostics.insightface_models)
    _render_feature_status(diagnostics.yolo_model)
    _render_feature_status(diagnostics.tesseract)


def _render_feature_status(feature) -> None:
    """Render a single feature status row."""
    # Determine icon and color
    if not feature.enabled:
        icon = "⚪"
        status_text = "Disabled"
        color = "gray"
    elif feature.available:
        icon = "🟢"
        status_text = "Available"
        color = "green"
    else:
        icon = "🔴"
        status_text = "Unavailable"
        color = "red"

    # Create expandable section
    with st.expander(f"{icon} **{feature.name}**: {status_text}", expanded=False):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("**Status:**")
            st.markdown(f":{color}[{status_text}]")

        with col2:
            if feature.enabled:
                st.markdown("**Enabled:** ✓")
            else:
                st.markdown("**Enabled:** ✗")

            if feature.details:
                st.markdown(f"**Details:** {feature.details}")

            if feature.error:
                st.error(f"**Error:** {feature.error}")


def render_compact_status() -> None:
    """Render compact feature status (for sidebar or main view)."""
    if "last_diagnostics" not in st.session_state:
        # Run quick diagnostics on first load
        diagnostics = run_diagnostics()
        st.session_state.last_diagnostics = diagnostics
    else:
        diagnostics = st.session_state.last_diagnostics

    st.markdown("**Feature Status**")

    # Show key features
    col1, col2 = st.columns(2)

    with col1:
        face = diagnostics.face_recognition
        if face.enabled:
            icon = "🟢" if face.available else "🔴"
            st.markdown(f"{icon} Faces")
        else:
            st.markdown("⚪ Faces")

    with col2:
        plate = diagnostics.plate_detection
        if plate.enabled:
            icon = "🟢" if plate.available else "🔴"
            st.markdown(f"{icon} Plates")
        else:
            st.markdown("⚪ Plates")

    # Show warnings if any
    failures = diagnostics.get_failures()
    if failures:
        st.warning(f"⚠️ {len(failures)} feature(s) need attention")
        if st.button("View Details", key="view_diagnostics_details"):
            st.session_state.show_diagnostics = True
