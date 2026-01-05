"""Centralized application state management with Qt signals.

The AppState class serves as the single source of truth for all UI state,
emitting signals whenever state changes to enable reactive UI updates.
"""

from PySide6.QtCore import QObject, QSettings, Signal


class AppState(QObject):
    """Centralized state model with reactive signals.

    Manages all application state including:
    - Mode (Standalone/Client)
    - Connection status
    - Video source configuration
    - Video settings (FPS, resize)
    - Face recognition settings
    - OCR parameters
    - Tracking settings
    - Detection results

    All state changes emit corresponding signals for UI reactivity.
    """

    # ========================================================================
    # Signals
    # ========================================================================

    # Mode and connection
    mode_changed = Signal(str)  # "Standalone" | "Client"
    connected_changed = Signal(bool)

    # Source configuration
    source_type_changed = Signal(str)  # "device", "rtsp", "http_mjpeg", "file", "rtmp"
    source_config_changed = Signal(object)  # Concrete source config object

    # Video settings
    fps_target_changed = Signal(int)
    ui_refresh_fps_changed = Signal(int)
    auto_refresh_changed = Signal(bool)
    frame_resize_changed = Signal(object)  # Optional[tuple]

    # Face settings
    face_threshold_changed = Signal(float)

    # Tracking settings
    tracking_enabled_changed = Signal(bool)
    tracking_params_changed = Signal(dict)

    # OCR settings
    ocr_params_changed = Signal(dict)

    # Detection results
    frame_received = Signal(object)  # FrameResult
    stats_updated = Signal(dict)  # {"fps": float, "frame_count": int}
    feature_status_updated = Signal(dict)

    # API client (for Client mode)
    api_url_changed = Signal(str)
    api_auth_token_changed = Signal(str)

    # Theme
    theme_changed = Signal(str)  # "light" | "dark" | "system"

    def __init__(self):
        """Initialize the application state."""
        super().__init__()

        # Initialize default values
        self._mode = "Standalone"
        self._connected = False

        # Source config
        self._source_type = "device"
        self._source_config = None

        # Video settings
        self._fps_target = 15
        self._ui_refresh_fps = 5
        self._auto_refresh = True
        self._frame_resize = None

        # Face settings
        self._face_threshold = 0.35

        # Tracking settings
        self._tracking_enabled = False
        self._tracking_params = {
            "frames_required": 3,
            "iou_threshold": 0.5,
            "max_age_frames": 30,
            "ocr_agreement_threshold": 0.6,
        }

        # OCR settings (default balanced preset)
        self._ocr_params = {
            "psm_mode": 7,
            "char_whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ",
            "enable_grayscale": True,
            "enable_bilateral": False,
            "bilateral_d": 9,
            "bilateral_sigma_color": 75,
            "bilateral_sigma_space": 75,
            "enable_adaptive_threshold": False,
            "adaptive_block_size": 11,
            "adaptive_c": 2,
            "enable_clahe": False,
            "clahe_clip_limit": 2.0,
            "clahe_tile_size": 8,
            "to_uppercase": True,
            "strip_whitespace": True,
            "min_text_length": 5,
            "substitute_o_to_0": False,
            "substitute_i_to_1": False,
            "crop_margin_px": 0,
            "upscale_factor": 1,
        }

        # API client
        self._api_url = "http://localhost:8000"
        self._api_auth_token = ""

        # Theme
        self._theme = "system"

        # Detection results (latest)
        self._latest_frame = None
        self._latest_stats = {"fps": 0.0, "frame_count": 0}
        self._latest_feature_status = {}

    # ========================================================================
    # Mode and Connection
    # ========================================================================

    def set_mode(self, mode: str):
        """Set the application mode.

        Args:
            mode: "Standalone" or "Client"
        """
        if mode != self._mode:
            self._mode = mode
            self.mode_changed.emit(mode)

    def get_mode(self) -> str:
        """Get the current mode."""
        return self._mode

    def set_connected(self, connected: bool):
        """Set the connection status.

        Args:
            connected: True if connected, False otherwise
        """
        if connected != self._connected:
            self._connected = connected
            self.connected_changed.emit(connected)

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    # ========================================================================
    # Source Configuration
    # ========================================================================

    def set_source_type(self, source_type: str):
        """Set the video source type.

        Args:
            source_type: "device", "rtsp", "http_mjpeg", "file", "rtmp"
        """
        if source_type != self._source_type:
            self._source_type = source_type
            self.source_type_changed.emit(source_type)

    def get_source_type(self) -> str:
        """Get the current source type."""
        return self._source_type

    def set_source_config(self, config):
        """Set the concrete source configuration.

        Args:
            config: DeviceSource, RTSPSource, etc.
        """
        self._source_config = config
        self.source_config_changed.emit(config)

    def get_source_config(self):
        """Get the current source configuration."""
        return self._source_config

    # ========================================================================
    # Video Settings
    # ========================================================================

    def set_fps_target(self, fps: int):
        """Set the target FPS.

        Args:
            fps: Target FPS (1-30)
        """
        fps = max(1, min(30, fps))
        if fps != self._fps_target:
            self._fps_target = fps
            self.fps_target_changed.emit(fps)

    def get_fps_target(self) -> int:
        """Get the target FPS."""
        return self._fps_target

    def set_ui_refresh_fps(self, fps: int):
        """Set the UI refresh FPS.

        Args:
            fps: UI refresh rate (1-10)
        """
        fps = max(1, min(10, fps))
        if fps != self._ui_refresh_fps:
            self._ui_refresh_fps = fps
            self.ui_refresh_fps_changed.emit(fps)

    def get_ui_refresh_fps(self) -> int:
        """Get the UI refresh FPS."""
        return self._ui_refresh_fps

    def set_auto_refresh(self, enabled: bool):
        """Set auto-refresh enabled state.

        Args:
            enabled: True to enable, False to disable
        """
        if enabled != self._auto_refresh:
            self._auto_refresh = enabled
            self.auto_refresh_changed.emit(enabled)

    def is_auto_refresh(self) -> bool:
        """Check if auto-refresh is enabled."""
        return self._auto_refresh

    # ========================================================================
    # Face Settings
    # ========================================================================

    def set_face_threshold(self, threshold: float):
        """Set the face similarity threshold.

        Args:
            threshold: Similarity threshold (0.0-1.0)
        """
        threshold = max(0.0, min(1.0, threshold))
        if threshold != self._face_threshold:
            self._face_threshold = threshold
            self.face_threshold_changed.emit(threshold)

    def get_face_threshold(self) -> float:
        """Get the face similarity threshold."""
        return self._face_threshold

    # ========================================================================
    # Tracking Settings
    # ========================================================================

    def set_tracking_enabled(self, enabled: bool):
        """Set tracking enabled state.

        Args:
            enabled: True to enable, False to disable
        """
        if enabled != self._tracking_enabled:
            self._tracking_enabled = enabled
            self.tracking_enabled_changed.emit(enabled)

    def is_tracking_enabled(self) -> bool:
        """Check if tracking is enabled."""
        return self._tracking_enabled

    def set_tracking_params(self, params: dict):
        """Set tracking parameters.

        Args:
            params: Tracking parameter dictionary
        """
        self._tracking_params.update(params)
        self.tracking_params_changed.emit(self._tracking_params)

    def get_tracking_params(self) -> dict:
        """Get tracking parameters."""
        return self._tracking_params.copy()

    # ========================================================================
    # OCR Settings
    # ========================================================================

    def set_ocr_params(self, params: dict):
        """Set OCR parameters.

        Args:
            params: OCR parameter dictionary
        """
        self._ocr_params.update(params)
        self.ocr_params_changed.emit(self._ocr_params)

    def get_ocr_params(self) -> dict:
        """Get OCR parameters."""
        return self._ocr_params.copy()

    # ========================================================================
    # API Client Settings
    # ========================================================================

    def set_api_url(self, url: str):
        """Set the API URL.

        Args:
            url: API base URL
        """
        if url != self._api_url:
            self._api_url = url
            self.api_url_changed.emit(url)

    def get_api_url(self) -> str:
        """Get the API URL."""
        return self._api_url

    def set_api_auth_token(self, token: str):
        """Set the API auth token.

        Args:
            token: Bearer token
        """
        if token != self._api_auth_token:
            self._api_auth_token = token
            self.api_auth_token_changed.emit(token)

    def get_api_auth_token(self) -> str:
        """Get the API auth token."""
        return self._api_auth_token

    # ========================================================================
    # Theme
    # ========================================================================

    def set_theme(self, theme: str):
        """Set the UI theme.

        Args:
            theme: "light", "dark", or "system"
        """
        theme = theme.lower()
        if theme not in ("light", "dark", "system"):
            theme = "system"

        if theme != self._theme:
            self._theme = theme
            self.theme_changed.emit(theme)

    def get_theme(self) -> str:
        """Get the current theme."""
        return self._theme

    # ========================================================================
    # Detection Results
    # ========================================================================

    def update_frame(self, frame_result):
        """Update with new frame result.

        Args:
            frame_result: FrameResult object
        """
        self._latest_frame = frame_result
        self.frame_received.emit(frame_result)

    def get_latest_frame(self):
        """Get the latest frame result."""
        return self._latest_frame

    def update_stats(self, stats: dict):
        """Update capture statistics.

        Args:
            stats: Statistics dictionary
        """
        self._latest_stats = stats
        self.stats_updated.emit(stats)

    def get_stats(self) -> dict:
        """Get the latest statistics."""
        return self._latest_stats.copy()

    def update_feature_status(self, status: dict):
        """Update feature status.

        Args:
            status: Feature status dictionary
        """
        self._latest_feature_status = status
        self.feature_status_updated.emit(status)

    def get_feature_status(self) -> dict:
        """Get the latest feature status."""
        return self._latest_feature_status.copy()

    # ========================================================================
    # Persistence
    # ========================================================================

    def load_settings(self):
        """Load settings from QSettings."""
        settings = QSettings("SecureVision", "Dashboard")

        # Mode and connection
        self._mode = settings.value("mode", "Standalone")
        self._api_url = settings.value("api_url", "http://localhost:8000")

        # Theme
        self._theme = settings.value("ui/theme", "system")

        # Source
        self._source_type = settings.value("source/type", "device")

        # Video settings
        self._fps_target = int(settings.value("video/fps_target", 15))
        self._ui_refresh_fps = int(settings.value("video/ui_refresh_fps", 5))
        self._auto_refresh = settings.value("video/auto_refresh", True, type=bool)

        # Face settings
        self._face_threshold = float(settings.value("face/threshold", 0.35))

        # Tracking settings
        self._tracking_enabled = settings.value("tracking/enabled", False, type=bool)

    def save_settings(self):
        """Save settings to QSettings."""
        settings = QSettings("SecureVision", "Dashboard")

        # Mode and connection
        settings.setValue("mode", self._mode)
        settings.setValue("api_url", self._api_url)

        # Theme
        settings.setValue("ui/theme", self._theme)

        # Source
        settings.setValue("source/type", self._source_type)

        # Video settings
        settings.setValue("video/fps_target", self._fps_target)
        settings.setValue("video/ui_refresh_fps", self._ui_refresh_fps)
        settings.setValue("video/auto_refresh", self._auto_refresh)

        # Face settings
        settings.setValue("face/threshold", self._face_threshold)

        # Tracking settings
        settings.setValue("tracking/enabled", self._tracking_enabled)
