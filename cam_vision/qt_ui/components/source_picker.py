"""Video source selection widget with type-specific configuration."""

import logging
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from cam_vision.config import DeviceSource, FileSource, HTTPMjpegSource, RTMPSource, RTSPSource

from ..styles import tokens

logger = logging.getLogger(__name__)


class SourcePicker(QWidget):
    """Video source picker with dynamic configuration fields.

    Allows selection of:
    - Device (webcam/USB) with device index and optional backend
    - RTSP stream with URL
    - HTTP MJPEG stream with URL
    - File (video file) with path
    - RTMP stream with URL

    Signals:
        source_changed: Emitted when source configuration changes (source_config)
    """

    source_changed = Signal(object)  # DeviceSource, RTSPSource, etc.

    def __init__(self):
        """Initialize the source picker."""
        super().__init__()

        # Current state
        self._source_type = "device"
        self._device_index = 0
        self._device_backend = ""
        self._rtsp_url = "rtsp://"
        self._http_url = "http://"
        self._file_path = ""
        self._rtmp_url = "rtmp://"

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Header
        header = QLabel("Video Source")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(header)

        # Source type selector (radio buttons)
        type_layout = QVBoxLayout()
        type_layout.setSpacing(tokens.SPACING_TIGHT)

        self.button_group = QButtonGroup(self)

        self.device_radio = QRadioButton("Device")
        self.device_radio.setChecked(True)
        self.button_group.addButton(self.device_radio, 0)
        type_layout.addWidget(self.device_radio)

        self.rtsp_radio = QRadioButton("RTSP")
        self.button_group.addButton(self.rtsp_radio, 1)
        type_layout.addWidget(self.rtsp_radio)

        self.http_radio = QRadioButton("HTTP MJPEG")
        self.button_group.addButton(self.http_radio, 2)
        type_layout.addWidget(self.http_radio)

        self.file_radio = QRadioButton("File")
        self.button_group.addButton(self.file_radio, 3)
        type_layout.addWidget(self.file_radio)

        self.rtmp_radio = QRadioButton("RTMP")
        self.button_group.addButton(self.rtmp_radio, 4)
        type_layout.addWidget(self.rtmp_radio)

        layout.addLayout(type_layout)

        # Stacked widget for type-specific config
        self.config_stack = QStackedWidget()
        self.config_stack.addWidget(self._create_device_config())
        self.config_stack.addWidget(self._create_rtsp_config())
        self.config_stack.addWidget(self._create_http_config())
        self.config_stack.addWidget(self._create_file_config())
        self.config_stack.addWidget(self._create_rtmp_config())

        layout.addWidget(self.config_stack)

        # Connect signals
        self.button_group.idClicked.connect(self._on_source_type_changed)

    def _create_device_config(self) -> QWidget:
        """Create device configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # Device index
        index_label = QLabel("Device Index:")
        index_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(index_label)

        self.device_index_input = QSpinBox()
        self.device_index_input.setRange(0, 10)
        self.device_index_input.setValue(0)
        self.device_index_input.setMinimumHeight(32)
        self.device_index_input.valueChanged.connect(self._on_device_config_changed)
        layout.addWidget(self.device_index_input)

        # Backend (optional)
        backend_label = QLabel("Backend (optional):")
        backend_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(backend_label)

        self.device_backend_input = QLineEdit()
        self.device_backend_input.setPlaceholderText("AVFOUNDATION, V4L2, etc.")
        self.device_backend_input.setMinimumHeight(32)
        self.device_backend_input.textChanged.connect(self._on_device_config_changed)
        layout.addWidget(self.device_backend_input)

        layout.addStretch()

        return widget

    def _create_rtsp_config(self) -> QWidget:
        """Create RTSP configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # URL
        url_label = QLabel("RTSP URL:")
        url_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(url_label)

        self.rtsp_url_input = QLineEdit()
        self.rtsp_url_input.setPlaceholderText("rtsp://user:pass@host:port/stream")
        self.rtsp_url_input.setText("rtsp://")
        self.rtsp_url_input.setMinimumHeight(32)
        self.rtsp_url_input.textChanged.connect(self._on_rtsp_config_changed)
        layout.addWidget(self.rtsp_url_input)

        layout.addStretch()

        return widget

    def _create_http_config(self) -> QWidget:
        """Create HTTP MJPEG configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # URL
        url_label = QLabel("HTTP MJPEG URL:")
        url_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(url_label)

        self.http_url_input = QLineEdit()
        self.http_url_input.setPlaceholderText("http://host:port/video")
        self.http_url_input.setText("http://")
        self.http_url_input.setMinimumHeight(32)
        self.http_url_input.textChanged.connect(self._on_http_config_changed)
        layout.addWidget(self.http_url_input)

        layout.addStretch()

        return widget

    def _create_file_config(self) -> QWidget:
        """Create file configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # File path
        path_label = QLabel("File Path:")
        path_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(path_label)

        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("/path/to/video.mp4")
        self.file_path_input.setMinimumHeight(32)
        self.file_path_input.textChanged.connect(self._on_file_config_changed)
        layout.addWidget(self.file_path_input)

        layout.addStretch()

        return widget

    def _create_rtmp_config(self) -> QWidget:
        """Create RTMP configuration widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # URL
        url_label = QLabel("RTMP URL:")
        url_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(url_label)

        self.rtmp_url_input = QLineEdit()
        self.rtmp_url_input.setPlaceholderText("rtmp://host:port/app/stream")
        self.rtmp_url_input.setText("rtmp://")
        self.rtmp_url_input.setMinimumHeight(32)
        self.rtmp_url_input.textChanged.connect(self._on_rtmp_config_changed)
        layout.addWidget(self.rtmp_url_input)

        layout.addStretch()

        return widget

    def _on_source_type_changed(self, button_id: int):
        """Handle source type change.

        Args:
            button_id: Radio button ID (0=device, 1=rtsp, 2=http, 3=file, 4=rtmp)
        """
        # Update stacked widget
        self.config_stack.setCurrentIndex(button_id)

        # Update source type
        type_map = {0: "device", 1: "rtsp", 2: "http_mjpeg", 3: "file", 4: "rtmp"}
        self._source_type = type_map[button_id]

        # Emit change
        self._emit_source_changed()

    def _on_device_config_changed(self):
        """Handle device configuration change."""
        self._device_index = self.device_index_input.value()
        self._device_backend = self.device_backend_input.text().strip()

        if self._source_type == "device":
            self._emit_source_changed()

    def _on_rtsp_config_changed(self):
        """Handle RTSP configuration change."""
        self._rtsp_url = self.rtsp_url_input.text().strip()

        if self._source_type == "rtsp":
            self._emit_source_changed()

    def _on_http_config_changed(self):
        """Handle HTTP configuration change."""
        self._http_url = self.http_url_input.text().strip()

        if self._source_type == "http_mjpeg":
            self._emit_source_changed()

    def _on_file_config_changed(self):
        """Handle file configuration change."""
        self._file_path = self.file_path_input.text().strip()

        if self._source_type == "file":
            self._emit_source_changed()

    def _on_rtmp_config_changed(self):
        """Handle RTMP configuration change."""
        self._rtmp_url = self.rtmp_url_input.text().strip()

        if self._source_type == "rtmp":
            self._emit_source_changed()

    def _emit_source_changed(self):
        """Emit source_changed signal with current configuration."""
        config = self.get_source_config()
        if config:
            self.source_changed.emit(config)

    def get_source_config(self) -> Optional[object]:
        """Get current source configuration.

        Returns:
            Source config object or None if invalid
        """
        if self._source_type == "device":
            return DeviceSource(
                device_index=self._device_index,
                backend=self._device_backend if self._device_backend else None,
            )

        elif self._source_type == "rtsp":
            if self._rtsp_url and self._rtsp_url != "rtsp://":
                return RTSPSource(url=self._rtsp_url)

        elif self._source_type == "http_mjpeg":
            if self._http_url and self._http_url != "http://":
                return HTTPMjpegSource(url=self._http_url)

        elif self._source_type == "file":
            if self._file_path:
                return FileSource(url=self._file_path)

        elif self._source_type == "rtmp":
            if self._rtmp_url and self._rtmp_url != "rtmp://":
                return RTMPSource(url=self._rtmp_url)

        return None

    def get_source_type(self) -> str:
        """Get current source type.

        Returns:
            Source type string
        """
        return self._source_type
