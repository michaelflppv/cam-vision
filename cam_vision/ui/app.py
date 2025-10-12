"""SecureVision Streamlit Dashboard - Main Application."""

import time

import cv2
import streamlit as st

from cam_vision.ui.async_helpers import run_async
from cam_vision.ui.capture import CaptureManager
from cam_vision.ui.client import SecureVisionClient
from cam_vision.ui.components.event_history import (
    render_face_history_panel,
    render_health_panel,
    render_plate_history_panel,
)
from cam_vision.ui.components.face_panel import render_face_panel
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

# Initialize capture manager (faces + plates enabled by default)
if "capture_manager" not in st.session_state:
    # Try to enable both features, will gracefully disable if dependencies missing
    st.session_state.capture_manager = CaptureManager(
        enable_faces=True,  # Requires gallery enrollment
        enable_plates=True,  # Requires YOLO model
    )

manager = st.session_state.capture_manager

# Main title
st.title("🎥 SecureVision Dashboard")
st.caption("Live face recognition + license plate detection")

# Sidebar - Mode & Configuration
with st.sidebar:
    st.header("Mode")

    # Mode selector
    mode = st.radio(
        "Operation Mode",
        ["Standalone", "Client (API Server)"],
        key="mode_selector",
        help="Standalone: Local processing | Client: Connect to API server",
    )
    st.session_state.mode = mode

    st.divider()

    # Mode-specific configuration
    if mode == "Client (API Server)":
        st.subheader("API Connection")

        api_url = st.text_input(
            "API URL",
            value=st.session_state.api_url,
            key="api_url_input",
            help="Base URL of SecureVision API (e.g., http://localhost:8000)",
        )
        st.session_state.api_url = api_url

        auth_token = st.text_input(
            "Auth Token (optional)",
            value=st.session_state.api_auth_token,
            type="password",
            key="api_auth_token_input",
            help="Bearer token if API requires authentication",
        )
        st.session_state.api_auth_token = auth_token

        st.caption("ℹ️ In Client mode, events are fetched from the API server.")
        st.caption("Preview and source selection are not available.")

    else:  # Standalone mode
        st.subheader("Source Configuration")

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
            help="Processing frame rate (how many frames to capture/process per second)",
        )
        st.session_state.fps_target = fps_target

        ui_refresh_fps = st.sidebar.slider(
            "UI Refresh FPS",
            min_value=5,
            max_value=60,
            value=st.session_state.ui_refresh_fps,
            key="ui_refresh_fps_slider",
            help="Display refresh rate (how often to update the UI). Higher = smoother but more CPU",
        )
        st.session_state.ui_refresh_fps = ui_refresh_fps

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
                "Connect",
                type="primary",
                disabled=st.session_state.connected,
                use_container_width=True,
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
                st.session_state.latest_face_matches = []
                st.session_state.latest_plate_reads = []
                st.rerun()

        # Connection status
        if st.session_state.connected:
            st.sidebar.success("🟢 Connected")
        else:
            st.sidebar.info("⚪ Disconnected")

        # OCR controls (collapsible)
        with st.sidebar.expander("🔧 OCR Tuning", expanded=False):
            render_ocr_controls()

# Main content area - Mode-specific rendering
if mode == "Client (API Server)":
    # Client mode: Show API health and event history
    st.subheader("API Client Mode")

    # Initialize API client (create once per session)
    if "api_client" not in st.session_state:
        auth_token = st.session_state.api_auth_token if st.session_state.api_auth_token else None
        st.session_state.api_client = SecureVisionClient(
            api_url=st.session_state.api_url,
            auth_token=auth_token,
            max_events=200,
        )

    client = st.session_state.api_client

    # Fetch health data
    try:
        health_data = run_async(client.get_health())
        render_health_panel(health_data)
    except Exception as e:
        st.error(f"❌ Failed to connect to API: {e}")
        st.caption(f"API URL: {st.session_state.api_url}")
        st.caption("Check that the API server is running and the URL is correct.")

    st.divider()

    # Filtering controls
    st.subheader("Event Filters")
    col_time, col_type = st.columns(2)

    with col_time:
        time_filter_options = {
            "All time": None,
            "Last 5 minutes": 5,
            "Last 15 minutes": 15,
            "Last hour": 60,
        }
        time_filter_label = st.selectbox("Time Range", list(time_filter_options.keys()))
        time_filter = time_filter_options[time_filter_label]

    with col_type:
        event_type_filter = st.selectbox(
            "Event Type", ["Both", "Face Matches Only", "Plate Reads Only"]
        )

    # Fetch events button
    col_fetch, col_clear = st.columns(2)

    with col_fetch:
        if st.button("🔄 Fetch Events", type="primary", use_container_width=True):
            try:
                # Fetch face matches
                if event_type_filter in ["Both", "Face Matches Only"]:
                    face_events = run_async(client.get_events(event_type="face_match", limit=100))
                    st.session_state.api_face_events = face_events

                # Fetch plate reads
                if event_type_filter in ["Both", "Plate Reads Only"]:
                    plate_events = run_async(client.get_events(event_type="plate_read", limit=100))
                    st.session_state.api_plate_events = plate_events

                st.success("✅ Events fetched successfully")
            except Exception as e:
                st.error(f"Failed to fetch events: {e}")

    with col_clear:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.session_state.api_face_events = []
            st.session_state.api_plate_events = []
            st.success("Cache cleared")

    st.divider()

    # Event history panels
    col_faces, col_plates = st.columns(2)

    with col_faces:
        if event_type_filter in ["Both", "Face Matches Only"]:
            face_events = st.session_state.get("api_face_events", [])
            render_face_history_panel(face_events, time_filter=time_filter)
        else:
            st.info("👤 Face events hidden by filter")

    with col_plates:
        if event_type_filter in ["Both", "Plate Reads Only"]:
            plate_events = st.session_state.get("api_plate_events", [])
            render_plate_history_panel(plate_events, time_filter=time_filter)
        else:
            st.info("🚗 Plate events hidden by filter")

    # Auto-refresh (optional)
    if st.checkbox("Auto-refresh (every 5s)"):
        time.sleep(5)
        st.rerun()

else:
    # Standalone mode: Live preview with face and plate detection
    col_preview, col_results = st.columns([2, 1])

    with col_preview:
        st.subheader("Live Preview")

        # Stats display
        stats = manager.get_stats()
        col_fps, col_frames, col_status = st.columns(3)

        with col_fps:
            st.metric("Actual FPS", f"{stats['fps']:.1f}")

        with col_frames:
            st.metric("Frame Count", stats["frame_count"])

        with col_status:
            # Feature status indicators
            face_status = "🟢" if manager.enable_faces else "🔴"
            plate_status = "🟢" if manager.enable_plates else "🔴"
            st.metric("Features", f"{face_status} Faces | {plate_status} Plates")

        # Video preview placeholder
        preview_placeholder = st.empty()
        stats_info_placeholder = st.empty()

        if st.session_state.connected:
            # Get latest frame
            frame_result = manager.get_latest_frame()

            if frame_result:
                # Update session state
                st.session_state.latest_frame = frame_result.frame
                st.session_state.latest_face_matches = frame_result.face_matches
                st.session_state.latest_plate_reads = frame_result.plate_reads

                # Display frame with annotations
                frame_rgb = cv2.cvtColor(frame_result.preview_image, cv2.COLOR_BGR2RGB)
                preview_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                # Show detection stats
                face_count = len(frame_result.face_matches)
                plate_count = len(frame_result.plate_reads)
                stats_info_placeholder.info(
                    f"👤 {face_count} face(s) matched | 🚗 {plate_count} plate(s) detected"
                )
            elif st.session_state.get("latest_frame"):
                # Show last frame
                frame_rgb = cv2.cvtColor(st.session_state.latest_frame.image, cv2.COLOR_BGR2RGB)
                preview_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                stats_info_placeholder.info("👤 0 face(s) matched | 🚗 0 plate(s) detected")
            else:
                preview_placeholder.info("Waiting for frames...")
                stats_info_placeholder.info("No detections yet")

            # Auto-refresh at UI refresh rate
            refresh_delay = 1.0 / st.session_state.ui_refresh_fps
            time.sleep(refresh_delay)
            st.rerun()
        else:
            preview_placeholder.info("Click 'Connect' to start preview")
            stats_info_placeholder.info("No detections yet")

# Results panels (below preview)
st.divider()

col_faces, col_plates = st.columns(2)

with col_faces:
    if st.session_state.get("latest_face_matches") and st.session_state.get("latest_frame"):
        # Get similarity threshold from manager settings
        threshold = manager.settings.face.similarity_threshold if manager.settings else 0.35
        render_face_panel(
            st.session_state.latest_face_matches,
            st.session_state.latest_frame,
            similarity_threshold=threshold,
        )
    else:
        st.subheader("Face Matches")
        if not manager.enable_faces:
            st.warning(
                "⚠️ Face recognition disabled. "
                "Check that gallery is enrolled and configured correctly."
            )
        else:
            st.info("👤 No faces matched yet. Waiting for recognized persons...")

with col_plates:
    if st.session_state.get("latest_plate_reads") and st.session_state.get("latest_frame"):
        render_plate_panel(
            st.session_state.latest_plate_reads,
            st.session_state.latest_frame,
        )
    else:
        st.subheader("Plate Detections")
        if not manager.enable_plates:
            st.warning(
                "⚠️ Plate detection disabled. " "Check that YOLO model exists at configured path."
            )
        else:
            st.info("🚗 No plates detected yet. Waiting for vehicles...")
