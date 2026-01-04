"""Live video preview panel with stats overlay."""

import logging

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from cam_vision.ui.capture import FrameResult

from ..styles import tokens

logger = logging.getLogger(__name__)


class PreviewPanel(QWidget):
    """Live video preview panel.

    Displays:
    - Live video feed with detection overlays
    - FPS counter
    - Detection counts (faces, plates)

    Updates are triggered by calling update_frame(frame_result).
    """

    def __init__(self):
        """Initialize the preview panel."""
        super().__init__()

        self._setup_ui()
        self._last_pixmap = None
        self._gradient_frame_counter = 0
        self._last_gradient = None
        self._gradient_update_interval = 10
        self._frame_count = 0
        self._fps = 0.0
        self._face_count = 0
        self._plate_count = 0

    def _setup_ui(self):
        """Set up the UI layout."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Stats row (FPS, frame count, detection counts)
        stats_row = QHBoxLayout()
        stats_row.setSpacing(tokens.SPACING_COMFORTABLE)

        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        stats_row.addWidget(self.fps_label)

        self.frame_count_label = QLabel("Frames: 0")
        self.frame_count_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_NORMAL}px;"
        )
        stats_row.addWidget(self.frame_count_label)

        self.face_count_label = QLabel("Faces: 0")
        self.face_count_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_NORMAL}px;"
        )
        stats_row.addWidget(self.face_count_label)

        self.plate_count_label = QLabel("Plates: 0")
        self.plate_count_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_NORMAL}px;"
        )
        stats_row.addWidget(self.plate_count_label)

        stats_row.addStretch()

        layout.addLayout(stats_row)

        # Video display area
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setText("No video feed\nClick Connect to start")
        self._video_base_style = (
            f"border: 1px solid {tokens.BORDER_UNFOCUSED}; "
            f"color: {tokens.TEXT_SECONDARY}; "
            f"font-size: {tokens.FONT_SIZE_LARGE}px;"
        )
        self._set_video_background(tokens.BACKGROUND_SUBTLE, tokens.BACKGROUND_SUBTLE)

        layout.addWidget(self.video_label, 1)

    def update_frame(self, frame_result: FrameResult):
        """Update display with new frame.

        Args:
            frame_result: FrameResult from CaptureManager
        """
        try:
            # Get preview image (already has annotations)
            preview_bgr = frame_result.preview_image

            # Convert BGR to RGB for Qt
            preview_rgb = cv2.cvtColor(preview_bgr, cv2.COLOR_BGR2RGB)

            # Convert to QImage
            height, width, channels = preview_rgb.shape
            bytes_per_line = channels * width
            q_image = QImage(preview_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # Convert to QPixmap and display
            self._last_pixmap = QPixmap.fromImage(q_image)

            # Scale to fit label while maintaining aspect ratio
            self._update_video_pixmap()

            # Update gradient from frame color
            self._update_video_gradient(preview_bgr)

            # Update counts
            self._face_count = len(frame_result.face_observations)
            self._plate_count = len(frame_result.plate_observations)

        except Exception as e:
            logger.error(f"Error updating preview: {e}", exc_info=True)

    def update_stats(self, stats: dict):
        """Update stats display.

        Args:
            stats: Stats dict with fps and frame_count
        """
        self._fps = stats.get("fps", 0.0)
        self._frame_count = stats.get("frame_count", 0)

        # Update labels
        self.fps_label.setText(f"FPS: {self._fps:.1f}")
        self.frame_count_label.setText(f"Frames: {self._frame_count}")
        self.face_count_label.setText(f"Faces: {self._face_count}")
        self.plate_count_label.setText(f"Plates: {self._plate_count}")

    def clear(self):
        """Clear the video display."""
        self.video_label.clear()
        self._last_pixmap = None
        self._last_gradient = None
        self._gradient_frame_counter = 0
        self.video_label.setText("No video feed\nClick Connect to start")
        self._set_video_background(tokens.BACKGROUND_SUBTLE, tokens.BACKGROUND_SUBTLE)

        # Reset stats
        self._frame_count = 0
        self._fps = 0.0
        self._face_count = 0
        self._plate_count = 0

        self.fps_label.setText("FPS: 0.0")
        self.frame_count_label.setText("Frames: 0")
        self.face_count_label.setText("Faces: 0")
        self.plate_count_label.setText("Plates: 0")

    def resizeEvent(self, event):
        """Handle resizing to keep the preview scaled."""
        super().resizeEvent(event)
        self._update_video_pixmap()

    def _update_video_pixmap(self):
        """Scale the current pixmap to the available label size."""
        if not self._last_pixmap:
            return
        if self.video_label.width() <= 0 or self.video_label.height() <= 0:
            return
        scaled_pixmap = self._last_pixmap.scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)

    def _update_video_gradient(self, frame_bgr):
        """Update the video background gradient from the frame average color."""
        self._gradient_frame_counter += 1
        if self._gradient_frame_counter % self._gradient_update_interval != 0:
            return

        try:
            small = cv2.resize(frame_bgr, (32, 18), interpolation=cv2.INTER_AREA)
            mean_bgr = small.mean(axis=(0, 1))
            base = self._bgr_to_hex(mean_bgr)
            top = self._adjust_color(base, 18)
            bottom = self._adjust_color(base, -18)
            gradient_key = (top, bottom)
            if gradient_key != self._last_gradient:
                self._set_video_background(top, bottom)
                self._last_gradient = gradient_key
        except Exception as exc:
            logger.debug("Failed to update gradient: %s", exc)

    def _set_video_background(self, top_color: str, bottom_color: str):
        """Set the background gradient for the video label."""
        self.video_label.setStyleSheet(
            "background: qlineargradient("
            "x1: 0, y1: 0, x2: 0, y2: 1, "
            f"stop: 0 {top_color}, stop: 1 {bottom_color}"
            "); " + self._video_base_style
        )

    def _bgr_to_hex(self, bgr) -> str:
        """Convert BGR array to hex color."""
        b, g, r = [int(round(c)) for c in bgr]
        return f"#{r:02X}{g:02X}{b:02X}"

    def _adjust_color(self, hex_color: str, delta: int) -> str:
        """Lighten or darken a hex color by delta."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = max(0, min(255, r + delta))
        g = max(0, min(255, g + delta))
        b = max(0, min(255, b + delta))
        return f"#{r:02X}{g:02X}{b:02X}"
