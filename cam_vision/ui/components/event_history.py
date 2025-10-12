"""Event history panels for Client mode (API consumption)."""

from __future__ import annotations

from typing import Literal, Optional

import streamlit as st

from cam_vision.ui.formatting import (
    format_list_badge,
    format_similarity_badge,
    format_time_ago,
    format_timestamp,
)


def render_health_panel(health_data: dict) -> None:
    """
    Render API health status panel.

    Args:
        health_data: Health data from /health endpoint
    """
    st.subheader("API Health")

    if not health_data.get("ok", False):
        st.error(f"❌ API Error: {health_data.get('error', 'Unknown error')}")
        return

    # Main metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Status", "🟢 Online" if health_data.get("ok") else "🔴 Offline")

    with col2:
        ws_clients = health_data.get("ws_clients", 0)
        st.metric("WebSocket Clients", ws_clients)

    with col3:
        recent = health_data.get("recent_events", {})
        total = recent.get("total", 0)
        st.metric("Recent Events (5m)", total)

    # Event breakdown
    if "recent_events" in health_data:
        st.divider()
        recent = health_data["recent_events"]

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric("Total Events", recent.get("total", 0))

        with col_b:
            st.metric("Face Matches", recent.get("face_matches", 0))

        with col_c:
            st.metric("Plate Reads", recent.get("plate_reads", 0))

    # Event rate
    if "event_rate" in health_data:
        rate = health_data["event_rate"]
        st.caption(
            f"📊 Event rate: {rate.get('events_per_second', 0):.2f} events/sec "
            f"(sampled over {rate.get('sample_duration_seconds', 0):.1f}s)"
        )


def render_face_history_panel(
    events: list[dict],
    time_filter: Optional[int] = None,
    person_filter: Optional[str] = None,
) -> None:
    """
    Render face match history from API events.

    Args:
        events: List of face_match events from API
        time_filter: Filter to last N minutes (None = all)
        person_filter: Filter by person_id (None = all)
    """
    st.subheader("Face Match History")

    if not events:
        st.info("👤 No face matches yet. Waiting for events from API...")
        return

    # Apply filters
    filtered = events

    if time_filter:
        import time

        cutoff_ms = int((time.time() - time_filter * 60) * 1000)
        filtered = [e for e in filtered if e.get("ts_ms", 0) >= cutoff_ms]

    if person_filter:
        filtered = [e for e in filtered if e.get("payload", {}).get("person_id") == person_filter]

    # Show count
    st.caption(f"Showing {len(filtered)} of {len(events)} events")

    # Render events (most recent first)
    for i, event in enumerate(filtered[:20]):  # Limit to 20 for performance
        payload = event.get("payload", {})
        person_id = payload.get("person_id", "Unknown")
        similarity = payload.get("similarity", 0.0)
        ts_ms = event.get("ts_ms", 0)

        # Get badge
        emoji, _ = format_similarity_badge(similarity)

        with st.expander(
            f"{emoji} {person_id} ({similarity:.3f}) - {format_time_ago(ts_ms)}",
            expanded=(i == 0),
        ):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.caption("Event Details")
                st.text(f"ID: {event.get('id')}")
                st.text(f"Source: {event.get('frame_source_id', 'N/A')}")
                st.text(f"Time: {format_timestamp(ts_ms)}")

            with col2:
                st.markdown(f"**Person:** {person_id}")
                st.markdown(f"**Similarity:** {similarity:.3f}")

                # Progress bar
                st.progress(min(1.0, similarity), text=f"Confidence: {similarity*100:.1f}%")

                # Detection metrics
                det_score = payload.get("detection_score", 0.0)
                st.metric("Detection Score", f"{det_score:.3f}")

                # Metadata
                metadata = payload.get("detector_metadata", {})
                if metadata:
                    st.caption(f"🔧 Model: {metadata.get('model_name', 'N/A')}")


def render_plate_history_panel(
    events: list[dict],
    time_filter: Optional[int] = None,
    list_filter: Optional[Literal["whitelist", "blacklist", "unknown"]] = None,
) -> None:
    """
    Render plate read history from API events.

    Args:
        events: List of plate_read events from API
        time_filter: Filter to last N minutes (None = all)
        list_filter: Filter by list match (None = all)
    """
    st.subheader("Plate Read History")

    if not events:
        st.info("🚗 No plate reads yet. Waiting for events from API...")
        return

    # Apply filters
    filtered = events

    if time_filter:
        import time

        cutoff_ms = int((time.time() - time_filter * 60) * 1000)
        filtered = [e for e in filtered if e.get("ts_ms", 0) >= cutoff_ms]

    if list_filter:
        if list_filter == "unknown":
            filtered = [e for e in filtered if not e.get("payload", {}).get("matched_list")]
        else:
            filtered = [
                e for e in filtered if e.get("payload", {}).get("matched_list") == list_filter
            ]

    # Show count
    st.caption(f"Showing {len(filtered)} of {len(events)} events")

    # Render events (most recent first)
    for i, event in enumerate(filtered[:20]):  # Limit to 20 for performance
        payload = event.get("payload", {})
        text_clean = payload.get("text_clean", "???")
        matched_list = payload.get("matched_list")
        ts_ms = event.get("ts_ms", 0)

        # Get badge
        emoji, list_label = format_list_badge(matched_list)

        with st.expander(
            f"{emoji} {text_clean} ({list_label}) - {format_time_ago(ts_ms)}",
            expanded=(i == 0),
        ):
            col1, col2 = st.columns([1, 2])

            with col1:
                st.caption("Event Details")
                st.text(f"ID: {event.get('id')}")
                st.text(f"Source: {event.get('frame_source_id', 'N/A')}")
                st.text(f"Time: {format_timestamp(ts_ms)}")

            with col2:
                # OCR results
                text_raw = payload.get("text_raw", "")
                st.markdown(f"**Raw Text:** `{text_raw}`")
                st.markdown(f"**Clean Text:** `{text_clean}`")

                st.divider()

                # Confidence metrics
                ocr_conf = payload.get("ocr_confidence", 0.0)
                det_score = payload.get("detector_score", 0.0)

                col_a, col_b = st.columns(2)

                with col_a:
                    st.metric("OCR Confidence", f"{ocr_conf:.1f}%")

                with col_b:
                    st.metric("Detector Score", f"{det_score:.3f}")

                # Progress bars
                st.progress(min(1.0, det_score), text=f"Detection: {det_score*100:.1f}%")
                st.progress(min(1.0, ocr_conf / 100.0), text=f"OCR: {ocr_conf:.1f}%")

                st.divider()

                # List match
                if matched_list == "whitelist":
                    st.success("✅ **Whitelist Match** - Authorized plate")
                elif matched_list == "blacklist":
                    st.error("🚫 **Blacklist Match** - Blocked plate")
                else:
                    st.info("○ **Unknown Plate** - Not in lists")

                # Preprocessing
                preprocessing = payload.get("preprocessing_used", "")
                if preprocessing:
                    st.caption(f"🔧 Preprocessing: {preprocessing}")


def render_event_stream_indicator(last_event_age: Optional[float]) -> None:
    """
    Render indicator showing WebSocket stream status.

    Args:
        last_event_age: Seconds since last event (None if no events)
    """
    if last_event_age is None:
        st.caption("⚪ No events received yet")
    elif last_event_age < 3:
        st.caption(f"🟢 Live stream active ({last_event_age:.1f}s ago)")
    elif last_event_age < 10:
        st.caption(f"🟡 Event stream idle ({last_event_age:.1f}s ago)")
    else:
        st.caption(f"🔴 No recent events ({last_event_age:.0f}s ago)")
