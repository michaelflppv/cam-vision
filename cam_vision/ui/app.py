"""SecureVision Streamlit Dashboard - Main Application."""

import time

import cv2
import streamlit as st

from cam_vision.ui.async_helpers import run_async
from cam_vision.ui.capture import CaptureManager
from cam_vision.ui.client import SecureVisionClient
from cam_vision.ui.components.diagnostics_panel import render_diagnostics_panel
from cam_vision.ui.components.event_history import (
    render_face_history_panel,
    render_health_panel,
    render_plate_history_panel,
)
from cam_vision.ui.components.face_controls import render_face_controls
from cam_vision.ui.components.face_panel import render_face_panel
from cam_vision.ui.components.ocr_controls import render_ocr_controls
from cam_vision.ui.components.plate_panel import render_plate_panel
from cam_vision.ui.components.source_picker import render_source_picker
from cam_vision.ui.components.tracking_controls import render_tracking_controls
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

# Inject dashboard styles once
if not st.session_state.get("ui_dashboard_styles_loaded"):
    st.markdown(
        """
        <style>
        .sv-stat-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 4px;
        }
        .sv-stat-label {
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 6px;
        }
        .sv-stat-value {
            font-size: 1.8rem;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.92);
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.ui_dashboard_styles_loaded = True
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

        ui_refresh_max = 10
        ui_refresh_default = int(st.session_state.ui_refresh_fps)
        ui_refresh_default = max(1, min(ui_refresh_max, ui_refresh_default))

        ui_refresh_fps = st.sidebar.slider(
            "UI Refresh FPS",
            min_value=1,
            max_value=ui_refresh_max,
            value=ui_refresh_default,
            key="ui_refresh_fps_slider",
            help="Display refresh rate (higher = smoother but may flash more). Recommended: 5-10 FPS.",
        )
        st.session_state.ui_refresh_fps = ui_refresh_fps

        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox(
            "Auto-Refresh Video",
            value=st.session_state.auto_refresh_enabled,
            key="auto_refresh_checkbox",
            help="Continuously update video preview. Disable for manual refresh only.",
        )
        st.session_state.auto_refresh_enabled = auto_refresh

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
                width="stretch",
            ):
                if source_config:
                    with st.spinner("Connecting and initializing features..."):
                        try:
                            manager.start(
                                source_config=source_config,
                                fps_target=fps_target,
                                frame_resize=st.session_state.frame_resize,
                                face_similarity_threshold=st.session_state.face_similarity_threshold,
                                tracking_enabled=st.session_state.tracking_enabled,
                                frames_required=st.session_state.tracking_frames_required,
                                iou_threshold=st.session_state.tracking_iou_threshold,
                                max_age_frames=st.session_state.tracking_max_age_frames,
                                ocr_agreement_threshold=st.session_state.tracking_ocr_agreement_threshold,
                            )
                            st.session_state.connected = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to connect: {e}")
                else:
                    st.warning("Invalid source configuration")

        with col2:
            if st.button("Disconnect", disabled=not st.session_state.connected, width="stretch"):
                manager.stop()
                st.session_state.connected = False
                st.session_state.latest_frame = None
                st.session_state.latest_face_matches = []
                st.session_state.latest_face_observations = []
                st.session_state.latest_plate_reads = []
                st.session_state.latest_plate_observations = []
                st.session_state.latest_preview_image = None
                st.session_state.latest_detection_counts = {
                    "known": 0,
                    "unknown": 0,
                    "plates_read": 0,
                    "plates_pending": 0,
                    "plates": 0,
                }
                st.rerun()

        # Connection status
        if st.session_state.connected:
            st.sidebar.success("🟢 Connected")
        else:
            st.sidebar.info("⚪ Disconnected")

        # Face recognition controls (collapsible)
        with st.sidebar.expander("👤 Face Recognition Settings", expanded=False):
            render_face_controls()

        # OCR controls (collapsible)
        with st.sidebar.expander("🔧 OCR Tuning", expanded=False):
            render_ocr_controls()

        # Tracking controls (collapsible)
        with st.sidebar.expander("🎯 Tracking & Confirmation", expanded=False):
            render_tracking_controls()

        # System diagnostics (collapsible)
        st.sidebar.divider()
        with st.sidebar.expander("🔍 System Diagnostics", expanded=False):
            render_diagnostics_panel()

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
        if st.button("🔄 Fetch Events", type="primary", width="stretch"):
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
        if st.button("🗑️ Clear Cache", width="stretch"):
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
        # Header with manual refresh button
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.subheader("Live Preview")
        with col_header2:
            if st.session_state.connected and not st.session_state.auto_refresh_enabled:
                if st.button("🔄 Refresh", width="stretch", key="manual_refresh"):
                    st.rerun()

        # Note about smooth video
        if st.session_state.connected and st.session_state.auto_refresh_enabled:
            st.caption(
                "💡 **Tip:** For smoother video without page refreshes, use the CLI tool: "
                "`poetry run securevision-face-demo --source-type device --device 1 --preview`"
            )

        # Create placeholders for stats to prevent flashing
        col_fps, col_frames, col_status = st.columns(3)

        with col_fps:
            fps_placeholder = st.empty()

        with col_frames:
            frames_placeholder = st.empty()

        with col_status:
            status_placeholder = st.empty()

        # Video preview placeholder + stats cards
        preview_placeholder = st.empty()
        stats_known_col, stats_unknown_col, stats_plate_col = st.columns(3)

        def _stat_card(label: str, value: str | int) -> str:
            return f"""
                <div class="sv-stat-card">
                    <div class="sv-stat-label">{label}</div>
                    <div class="sv-stat-value">{value}</div>
                </div>
            """

        def _render_stats(known: int, unknown: int, plates_read: int, plates_pending: int) -> None:
            """Render detection stats without animated transitions."""
            st.session_state.latest_detection_counts = {
                "known": known,
                "unknown": unknown,
                "plates_read": plates_read,
                "plates_pending": plates_pending,
                "plates": plates_read + plates_pending,
            }

            stats_known_col.markdown(_stat_card("Known Faces", known), unsafe_allow_html=True)
            stats_unknown_col.markdown(_stat_card("Unknown Faces", unknown), unsafe_allow_html=True)
            stats_plate_col.markdown(
                _stat_card("Detected Plates", f"{plates_read} read / {plates_pending} pending"),
                unsafe_allow_html=True,
            )

        if st.session_state.connected:
            # Get latest frame
            frame_result = manager.get_latest_frame()

            # Update stats display
            stats = manager.get_stats()
            fps_placeholder.markdown(
                _stat_card("Actual FPS", f"{stats['fps']:.1f}"), unsafe_allow_html=True
            )
            frames_placeholder.markdown(
                _stat_card("Frame Count", stats["frame_count"]), unsafe_allow_html=True
            )

            # Feature status indicators with initialization info
            init_status = manager.get_init_status()

            # Face status with error indicator
            if init_status["faces_enabled"]:
                if init_status["gallery_persons"] > 0:
                    face_status = f"🟢 ({init_status['gallery_persons']} persons)"
                else:
                    face_status = "🟢"
            elif init_status["face_error"]:
                face_status = "🔴 Error"
            else:
                face_status = "⚪ Off"

            # Plate status with error indicator
            if init_status["plates_enabled"]:
                plate_status = "🟢"
            elif init_status["plate_error"]:
                plate_status = "🔴 Error"
            else:
                plate_status = "⚪ Off"

            status_placeholder.markdown(
                _stat_card("Feature Status", f"Faces: {face_status} | Plates: {plate_status}"),
                unsafe_allow_html=True,
            )

            # Show initialization errors prominently
            if init_status["face_error"]:
                st.error(
                    f"⚠️ **Face Recognition Error:** {init_status['face_error']}\n\n"
                    "Check System Diagnostics in sidebar for details."
                )

            if init_status["plate_error"]:
                st.error(
                    f"⚠️ **Plate Detection Error:** {init_status['plate_error']}\n\n"
                    "Check System Diagnostics in sidebar for details."
                )

            if frame_result:
                # Update session state
                st.session_state.latest_frame = frame_result.frame
                st.session_state.latest_face_matches = frame_result.face_matches
                st.session_state.latest_face_observations = frame_result.face_observations
                st.session_state.latest_plate_reads = frame_result.plate_reads
                st.session_state.latest_plate_observations = frame_result.plate_observations
                st.session_state.latest_preview_image = frame_result.preview_image.copy()

                # Display frame with annotations
                frame_rgb = cv2.cvtColor(frame_result.preview_image, cv2.COLOR_BGR2RGB)
                preview_placeholder.image(frame_rgb, channels="RGB", width="stretch")

                # Show detection stats
                matched_faces = sum(1 for obs in frame_result.face_observations if obs.matched)
                unknown_faces = len(frame_result.face_observations) - matched_faces
                plate_observations = frame_result.plate_observations
                plates_read = sum(1 for obs in plate_observations if obs.status == "read")
                plates_pending = sum(
                    1 for obs in plate_observations if obs.status != "read" and obs.is_displayable()
                )
                _render_stats(matched_faces, unknown_faces, plates_read, plates_pending)
            elif st.session_state.get("latest_preview_image") is not None:
                # Show last annotated frame
                frame_rgb = cv2.cvtColor(st.session_state.latest_preview_image, cv2.COLOR_BGR2RGB)
                preview_placeholder.image(frame_rgb, channels="RGB", width="stretch")

                counts = st.session_state.get(
                    "latest_detection_counts",
                    {
                        "known": 0,
                        "unknown": 0,
                        "plates_read": 0,
                        "plates_pending": 0,
                    },
                )
                _render_stats(
                    counts.get("known", 0),
                    counts.get("unknown", 0),
                    counts.get("plates_read", 0),
                    counts.get("plates_pending", 0),
                )
            else:
                preview_placeholder.info("Waiting for frames...")
                _render_stats(0, 0, 0, 0)

            # Auto-refresh at UI refresh rate (only if enabled)
            if st.session_state.auto_refresh_enabled:
                refresh_delay = 1.0 / st.session_state.ui_refresh_fps
                time.sleep(refresh_delay)
                st.rerun()
        else:
            # Show initial stats when disconnected
            stats = manager.get_stats()
            fps_placeholder.markdown(
                _stat_card("Actual FPS", f"{stats['fps']:.1f}"), unsafe_allow_html=True
            )
            frames_placeholder.markdown(
                _stat_card("Frame Count", stats["frame_count"]), unsafe_allow_html=True
            )

            init_status = manager.get_init_status()

            # Face status
            if init_status["faces_enabled"]:
                if init_status["gallery_persons"] > 0:
                    face_status = f"🟢 ({init_status['gallery_persons']} persons)"
                else:
                    face_status = "🟢"
            elif init_status["face_error"]:
                face_status = "🔴 Error"
            else:
                face_status = "⚪ Off"

            # Plate status
            if init_status["plates_enabled"]:
                plate_status = "🟢"
            elif init_status["plate_error"]:
                plate_status = "🔴 Error"
            else:
                plate_status = "⚪ Off"

            status_placeholder.markdown(
                _stat_card("Feature Status", f"Faces: {face_status} | Plates: {plate_status}"),
                unsafe_allow_html=True,
            )

            preview_placeholder.info("Click 'Connect' to start preview")
            _render_stats(0, 0, 0, 0)


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

with col_plates:
    if st.session_state.get("latest_plate_observations") and st.session_state.get("latest_frame"):
        render_plate_panel(
            st.session_state.latest_plate_observations,
            st.session_state.latest_frame,
        )
    else:
        st.info("🚗 No plate observations available yet.")
