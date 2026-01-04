"""Video settings widget for FPS, resize, and refresh options."""

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QSpinBox, QVBoxLayout, QWidget

from ..styles import tokens

logger = logging.getLogger(__name__)


class VideoSettings(QWidget):
    """Video settings control panel.

    Controls:
    - FPS target (1-30)
    - Frame resize preset
    - Auto-refresh toggle

    Signals:
        fps_changed: Emitted when FPS target changes (int)
        resize_changed: Emitted when resize option changes (tuple or None)
        auto_refresh_changed: Emitted when auto-refresh toggle changes (bool)
    """

    fps_changed = Signal(int)
    resize_changed = Signal(object)  # Optional[tuple[int, int]]
    auto_refresh_changed = Signal(bool)

    def __init__(self):
        """Initialize video settings widget."""
        super().__init__()

        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Header
        header = QLabel("Video Settings")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(header)

        # FPS target
        fps_label = QLabel("Target FPS:")
        fps_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(fps_label)

        self.fps_input = QSpinBox()
        self.fps_input.setRange(1, 30)
        self.fps_input.setValue(15)
        self.fps_input.setSuffix(" fps")
        self.fps_input.setMinimumHeight(32)
        self.fps_input.valueChanged.connect(self.fps_changed.emit)
        layout.addWidget(self.fps_input)

        # Frame resize
        resize_label = QLabel("Frame Resize:")
        resize_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(resize_label)

        self.resize_combo = QComboBox()
        self.resize_combo.addItem("Original", None)
        self.resize_combo.addItem("1920×1080 (FHD)", (1920, 1080))
        self.resize_combo.addItem("1280×720 (HD)", (1280, 720))
        self.resize_combo.addItem("854×480 (FWVGA)", (854, 480))
        self.resize_combo.addItem("640×480 (VGA)", (640, 480))
        self.resize_combo.addItem("640×360 (nHD)", (640, 360))
        self.resize_combo.setMinimumHeight(32)
        self.resize_combo.currentIndexChanged.connect(self._on_resize_changed)
        layout.addWidget(self.resize_combo)

        # Auto-refresh toggle
        self.auto_refresh_check = QCheckBox("Auto-refresh preview")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(
            lambda state: self.auto_refresh_changed.emit(state == 2)
        )
        layout.addWidget(self.auto_refresh_check)

    def _on_resize_changed(self, index: int):
        """Handle resize option change.

        Args:
            index: Combo box index
        """
        resize_value = self.resize_combo.itemData(index)
        self.resize_changed.emit(resize_value)

    def get_fps_target(self) -> int:
        """Get current FPS target.

        Returns:
            FPS target (1-30)
        """
        return self.fps_input.value()

    def set_fps_target(self, fps: int):
        """Set FPS target.

        Args:
            fps: FPS target (1-30)
        """
        self.fps_input.setValue(fps)

    def get_resize(self) -> tuple | None:
        """Get current resize option.

        Returns:
            (width, height) tuple or None
        """
        return self.resize_combo.currentData()

    def is_auto_refresh(self) -> bool:
        """Check if auto-refresh is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.auto_refresh_check.isChecked()
