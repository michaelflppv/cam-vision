"""SecureVision Streamlit Dashboard - Main Application."""

import time

import cv2
import streamlit as st

from cam_vision.ui.capture import CaptureManager
from cam_vision.ui.components.ocr_controls import render_ocr_controls
from cam_vision.ui.components.plate_panel import render_plate_panel
from cam_vision.ui.components.source_picker import render_source_picker
from cam_vision.ui.state import init_session_state

# Page config
st.set_page_config(
    page_title="SecureVision Dashboard",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()

# Initialize capture manager
if "capture_manager" not in st.session_state:
    st.session_state.capture_manager = CaptureManager()

manager = st.session_state.capture_manager

# Main title
st.title("🎥 SecureVision Dashboard")
st.caption("Live video source switching and OCR tuning")

# Sidebar - Source Configuration
with st.sidebar:
    st.header("Configuration")

    # Source picker
    source_config = render_source_picker()

    # FPS and resize options
    st.sidebar.subheader("Video Settings")

    fps_target = st.sidebar.slider(
        "Target FPS",
        min_value=1,
        max_value=30,
        value=st.session_state.fps_target,
        key="fps_target_slider",
    )
    st.session_state.fps_target = fps_target

    resize_options = {
        "None": None,
        "640x480": (640, 480),
        "800x600": (800, 600),
        "1280x720": (1280, 720),
    }

    resize_label = st.sidebar.selectbox(
        "Frame Resize",
        options=list(resize_options.keys()),
        index=0,
        key="resize_selector",
    )
    st.session_state.frame_resize = resize_options[resize_label]

    # Connection controls
    st.sidebar.divider()

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button(
            "Connect", type="primary", disabled=st.session_state.connected, use_container_width=True
        ):
            if source_config:
                try:
                    manager.start(
                        source_config=source_config,
                        fps_target=fps_target,
                        frame_resize=st.session_state.frame_resize,
                    )
                    st.session_state.connected = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to connect: {e}")
            else:
                st.warning("Invalid source configuration")

    with col2:
        if st.button(
            "Disconnect", disabled=not st.session_state.connected, use_container_width=True
        ):
            manager.stop()
            st.session_state.connected = False
            st.session_state.latest_frame = None
            st.session_state.latest_detections = []
            st.rerun()

    # Connection status
    if st.session_state.connected:
        st.sidebar.success("🟢 Connected")
    else:
        st.sidebar.info("⚪ Disconnected")

    # OCR controls (collapsible)
    with st.sidebar.expander("🔧 OCR Tuning", expanded=False):
        render_ocr_controls()

# Main content area
col_preview, col_plates = st.columns([2, 1])

with col_preview:
    st.subheader("Live Preview")

    # Stats display
    stats = manager.get_stats()
    col_fps, col_frames = st.columns(2)

    with col_fps:
        st.metric("Actual FPS", f"{stats['fps']:.1f}")

    with col_frames:
        st.metric("Frame Count", stats["frame_count"])

    # Video preview placeholder
    preview_placeholder = st.empty()
    face_info_placeholder = st.empty()  # Add for face info

    if st.session_state.connected:
        # Get latest frame
        frame_result = manager.get_latest_frame()

        if frame_result:
            st.session_state.latest_frame = frame_result.frame
            st.session_state.latest_detections = frame_result.detections
            st.session_state.latest_faces = (
                frame_result.faces if hasattr(frame_result, "faces") else []
            )

            # Display frame
            frame_rgb = cv2.cvtColor(frame_result.preview_image, cv2.COLOR_BGR2RGB)
            preview_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

            # Show face detection info
            if frame_result.faces:
                face_info_placeholder.info(
                    f"Detected faces: {len(frame_result.faces)} | "
                    + ", ".join(f"BBox: {f.bbox}, Score: {f.score:.2f}" for f in frame_result.faces)
                )
            else:
                face_info_placeholder.info("No faces detected")
        elif st.session_state.latest_frame:
            # Show last frame
            frame_rgb = cv2.cvtColor(st.session_state.latest_frame.image, cv2.COLOR_BGR2RGB)
            preview_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
            face_info_placeholder.info("No faces detected")
        else:
            preview_placeholder.info("Waiting for frames...")
            face_info_placeholder.info("No faces detected")

        # Auto-refresh
        time.sleep(0.2)  # 5 FPS UI update
        st.rerun()
    else:
        preview_placeholder.info("Click 'Connect' to start preview")
        face_info_placeholder.info("No faces detected")

with col_plates:
    if st.session_state.latest_detections and st.session_state.latest_frame:
        render_plate_panel(st.session_state.latest_detections, st.session_state.latest_frame)
    else:
        st.info("No detections yet")
