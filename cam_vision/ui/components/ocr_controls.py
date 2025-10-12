"""OCR tuning controls component."""

from __future__ import annotations

import streamlit as st


def render_ocr_controls():
    """Render OCR tuning controls in sidebar."""
    st.sidebar.subheader("OCR Settings")

    # Preset selector
    preset_names = list(st.session_state.ocr_presets.keys())
    selected_preset = st.sidebar.selectbox(
        "Preset",
        options=["Custom"] + preset_names,
        key="ocr_preset_selector",
    )

    if selected_preset != "Custom":
        preset_params = st.session_state.ocr_presets[selected_preset]
        st.session_state.ocr_params.update(preset_params)

    # PSM mode
    psm_options = {
        "7 - Single Line": 7,
        "6 - Uniform Block": 6,
        "3 - Auto": 3,
        "11 - Sparse Text": 11,
        "13 - Raw Line": 13,
    }
    psm_labels = list(psm_options.keys())
    psm_values = list(psm_options.values())

    current_psm = st.session_state.ocr_params["psm_mode"]
    psm_index = psm_values.index(current_psm) if current_psm in psm_values else 0

    selected_psm_label = st.sidebar.selectbox(
        "PSM Mode",
        options=psm_labels,
        index=psm_index,
        key="psm_mode_selector",
    )
    st.session_state.ocr_params["psm_mode"] = psm_options[selected_psm_label]

    # Character whitelist
    char_whitelist = st.sidebar.text_area(
        "Character Whitelist",
        value=st.session_state.ocr_params["char_whitelist"],
        height=60,
        key="char_whitelist_input",
    )
    st.session_state.ocr_params["char_whitelist"] = char_whitelist

    # Basic options
    st.session_state.ocr_params["to_uppercase"] = st.sidebar.checkbox(
        "Uppercase",
        value=st.session_state.ocr_params["to_uppercase"],
        key="to_uppercase_check",
    )

    st.session_state.ocr_params["strip_whitespace"] = st.sidebar.checkbox(
        "Strip Whitespace",
        value=st.session_state.ocr_params["strip_whitespace"],
        key="strip_whitespace_check",
    )

    # Preprocessing
    with st.sidebar.expander("Preprocessing"):
        st.session_state.ocr_params["enable_grayscale"] = st.checkbox(
            "Grayscale",
            value=st.session_state.ocr_params["enable_grayscale"],
            key="grayscale_check",
        )

        st.session_state.ocr_params["enable_bilateral"] = st.checkbox(
            "Bilateral Filter",
            value=st.session_state.ocr_params["enable_bilateral"],
            key="bilateral_check",
        )

        st.session_state.ocr_params["enable_adaptive_threshold"] = st.checkbox(
            "Adaptive Threshold",
            value=st.session_state.ocr_params["enable_adaptive_threshold"],
            key="adaptive_check",
        )

        st.session_state.ocr_params["enable_clahe"] = st.checkbox(
            "CLAHE (minimal benefit)",
            value=st.session_state.ocr_params["enable_clahe"],
            key="clahe_check",
        )

    # Advanced
    with st.sidebar.expander("Advanced"):
        st.session_state.ocr_params["crop_margin_px"] = st.slider(
            "Crop Margin (px)",
            min_value=0,
            max_value=20,
            value=st.session_state.ocr_params["crop_margin_px"],
            key="crop_margin_slider",
        )

        st.session_state.ocr_params["upscale_factor"] = st.select_slider(
            "Upscale Factor",
            options=[1, 2, 3],
            value=st.session_state.ocr_params["upscale_factor"],
            key="upscale_slider",
        )

        st.session_state.ocr_params["min_text_length"] = st.slider(
            "Min Text Length",
            min_value=1,
            max_value=10,
            value=st.session_state.ocr_params["min_text_length"],
            key="min_text_length_slider",
        )
