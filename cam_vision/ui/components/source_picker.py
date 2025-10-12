"""Source selection UI component."""

from __future__ import annotations

import streamlit as st

from cam_vision.config import DeviceSource, FileSource, HTTPMjpegSource, RTSPSource


def render_source_picker():
    """Render source picker in sidebar."""
    st.sidebar.subheader("Video Source")

    source_type = st.sidebar.radio(
        "Source Type",
        options=["device", "rtsp", "http_mjpeg", "file"],
        index=["device", "rtsp", "http_mjpeg", "file"].index(st.session_state.source_type),
        horizontal=True,
        key="source_type_radio",
    )

    st.session_state.source_type = source_type

    source_config = None

    if source_type == "device":
        device_index = st.sidebar.number_input(
            "Device Index",
            min_value=0,
            max_value=10,
            value=st.session_state.device_index,
            key="device_index_input",
        )
        st.session_state.device_index = device_index

        backend = st.sidebar.text_input(
            "Backend (optional)",
            value=st.session_state.device_backend,
            placeholder="AVFOUNDATION",
            key="device_backend_input",
        )
        st.session_state.device_backend = backend

        source_config = DeviceSource(
            device_index=device_index,
            backend=backend if backend else None,
        )

    elif source_type == "rtsp":
        url = st.sidebar.text_input(
            "RTSP URL",
            value=st.session_state.rtsp_url,
            placeholder="rtsp://user:pass@host:port/stream",
            key="rtsp_url_input",
        )
        st.session_state.rtsp_url = url

        if url and url != "rtsp://":
            source_config = RTSPSource(url=url)

    elif source_type == "http_mjpeg":
        url = st.sidebar.text_input(
            "HTTP MJPEG URL",
            value=st.session_state.http_url,
            placeholder="http://host:port/video",
            key="http_url_input",
        )
        st.session_state.http_url = url

        if url and url != "http://":
            source_config = HTTPMjpegSource(url=url)

    elif source_type == "file":
        file_path = st.sidebar.text_input(
            "File Path",
            value=st.session_state.file_path,
            placeholder="/path/to/video.mp4",
            key="file_path_input",
        )
        st.session_state.file_path = file_path

        if file_path:
            source_config = FileSource(url=file_path)

    return source_config
