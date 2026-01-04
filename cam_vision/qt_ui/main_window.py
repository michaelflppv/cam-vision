"""Main window for the SecureVision Qt dashboard.

Provides a frameless window with custom title bar and strict
monochromatic design.
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .components import (
    ControlsSidebar,
    DiagnosticsPanel,
    EnrollmentControls,
    FaceControls,
    FaceMatchesPanel,
    PlateDetectionsPanel,
    PreviewPanel,
    TrackingControls,
    VideoSettings,
)
from .state import AppState
from .styles import tokens
from .widgets.custom_titlebar import CustomTitleBar
from .workers import CaptureWorker

logger = logging.getLogger(__name__)

DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 900
MIN_PREVIEW_WIDTH = 640
MIN_DETECTION_WIDTH = 320
MIN_WINDOW_HEIGHT = 720


class SecureVisionMainWindow(QMainWindow):
    """Main application window with frameless design.

    Features:
    - Frameless window with custom title bar
    - Pure white background
    - Custom window controls (minimize/maximize/close)
    - Draggable title bar
    - Resize grip
    - Strict monochromatic design
    - Live video preview with detections
    - Real-time face and plate recognition
    """

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        # Application state
        self.state = AppState()
        self.state.load_settings()

        # Capture worker (created on demand)
        self.capture_worker = None

        # Configure frameless window
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.setWindowTitle("SecureVision")

        self._setup_ui()
        self._apply_window_sizing()
        self._connect_signals()
        self._on_connection_state_changed(self.state.is_connected())

    def _setup_ui(self):
        """Set up the UI layout."""
        # Central widget container
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # Main layout (vertical: title bar + content)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = CustomTitleBar("SecureVision")
        main_layout.addWidget(self.title_bar)

        # Content area (horizontal: sidebar + main content)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar (fixed width)
        self.sidebar = self._create_sidebar()
        content_layout.addWidget(self.sidebar)

        # Main content area (stacked pages)
        self.content_area = self._create_content_area()
        self.content_area.setObjectName("contentArea")
        content_layout.addWidget(self.content_area, 1)

        main_layout.addLayout(content_layout)

        # Size grip for resizing (bottom-right corner)
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(tokens.SIZE_GRIP_SIZE, tokens.SIZE_GRIP_SIZE)

    def _create_sidebar(self) -> QWidget:
        """Create the sidebar with controls.

        Returns:
            Sidebar widget
        """
        self.controls_sidebar = ControlsSidebar()
        return self.controls_sidebar

    def _create_content_area(self) -> QWidget:
        """Create the main content area.

        Returns:
            Content area widget
        """
        content = QWidget()
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.page_stack = QStackedWidget()
        self.page_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        live_page = self._create_live_page()
        self.page_stack.addWidget(live_page)

        self.video_settings = VideoSettings()
        self.page_stack.addWidget(self._wrap_control_page(self.video_settings))

        self.face_controls = FaceControls()
        self.page_stack.addWidget(self._wrap_control_page(self.face_controls))

        self.tracking_controls = TrackingControls()
        self.page_stack.addWidget(self._wrap_control_page(self.tracking_controls))

        self.diagnostics_panel = DiagnosticsPanel()
        self.page_stack.addWidget(self._wrap_control_page(self.diagnostics_panel))

        self.enrollment_controls = EnrollmentControls()
        self.page_stack.addWidget(self._wrap_control_page(self.enrollment_controls))

        layout.addWidget(self.page_stack, 1)

        content.setMinimumSize(live_page.minimumSizeHint())

        return content

    def _create_live_page(self) -> QWidget:
        """Create the live preview page."""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QHBoxLayout(page)
        layout.setContentsMargins(
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
        )
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Left: Preview panel (2/3 width)
        self.preview_panel = PreviewPanel()
        self.preview_panel.setMinimumWidth(MIN_PREVIEW_WIDTH)
        layout.addWidget(self.preview_panel, 2)

        # Right: Detection panels (1/3 width)
        detection_container = QWidget()
        detection_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        detection_container.setMinimumWidth(MIN_DETECTION_WIDTH)
        detection_layout = QVBoxLayout(detection_container)
        detection_layout.setContentsMargins(0, 0, 0, 0)
        detection_layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Face matches panel
        self.face_matches_panel = FaceMatchesPanel()
        detection_layout.addWidget(self.face_matches_panel, 1)

        # Plate detections panel
        self.plate_detections_panel = PlateDetectionsPanel()
        detection_layout.addWidget(self.plate_detections_panel, 1)

        layout.addWidget(detection_container, 1)

        return page

    def _wrap_control_page(self, widget: QWidget) -> QWidget:
        """Wrap a control widget in a scrollable page."""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
            tokens.PADDING_LARGE,
        )
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(tokens.SPACING_COMFORTABLE)
        container_layout.addWidget(widget)
        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        return page

    def _apply_window_sizing(self):
        """Set window sizing defaults and minimum bounds."""
        min_content_width = MIN_PREVIEW_WIDTH + MIN_DETECTION_WIDTH + tokens.SPACING_COMFORTABLE
        min_width_from_tokens = (
            tokens.SIDEBAR_WIDTH + (tokens.PADDING_LARGE * 2) + min_content_width
        )
        min_width_from_layout = (
            self.controls_sidebar.sizeHint().width() + self.content_area.minimumSizeHint().width()
        )
        min_width = max(min_width_from_tokens, min_width_from_layout)

        sidebar_min_height = self.controls_sidebar.minimumSizeHint().height()
        content_min_height = self.content_area.minimumSizeHint().height()
        title_height = self.title_bar.sizeHint().height()
        min_height_from_layout = title_height + max(sidebar_min_height, content_min_height)
        min_height = max(MIN_WINDOW_HEIGHT, min_height_from_layout)

        central_hint = self.centralWidget().minimumSizeHint()
        min_width = max(min_width, central_hint.width())
        min_height = max(min_height, central_hint.height())

        self.setMinimumSize(min_width, min_height)
        self.resize(
            max(DEFAULT_WINDOW_WIDTH, min_width),
            max(DEFAULT_WINDOW_HEIGHT, min_height),
        )

    def _connect_signals(self):
        """Connect signals from title bar to window actions."""
        # Title bar signals
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)

        # Controls sidebar signals
        self.controls_sidebar.connect_clicked.connect(self._on_connect_clicked)
        self.controls_sidebar.disconnect_clicked.connect(self._on_disconnect_clicked)
        self.controls_sidebar.source_changed.connect(self._on_source_changed)

        # Settings page signals
        self.video_settings.fps_changed.connect(self._on_fps_changed)
        self.video_settings.resize_changed.connect(self._on_resize_changed)
        self.face_controls.threshold_changed.connect(self._on_face_threshold_changed)
        self.tracking_controls.tracking_enabled_changed.connect(self._on_tracking_enabled_changed)
        self.tracking_controls.frames_required_changed.connect(self._emit_tracking_params)
        self.tracking_controls.iou_threshold_changed.connect(self._emit_tracking_params)
        self.tracking_controls.max_age_changed.connect(self._emit_tracking_params)
        self.tracking_controls.ocr_agreement_changed.connect(self._emit_tracking_params)

        # State signals
        self.state.connected_changed.connect(self._on_connection_state_changed)

        # Title bar navigation
        nav_labels = [
            "Live",
            "Video",
            "Face",
            "Tracking",
            "Diagnostics",
            "Accepted Lists",
        ]
        self.title_bar.set_navigation_tabs(nav_labels)
        self.title_bar.navigation_changed.connect(self._on_navigation_changed)

    def _on_connect_clicked(self):
        """Handle Connect button click."""
        logger.info("Connect button clicked")

        # Get source config from sidebar
        source_config = self.controls_sidebar.get_source_config()
        if not source_config:
            logger.error("Invalid source configuration")
            self.controls_sidebar.connection_controls.set_error("Invalid source config")
            return

        # Set connecting state
        self.controls_sidebar.connection_controls.set_connecting()

        # Create capture worker if needed
        if self.capture_worker is None:
            self.capture_worker = CaptureWorker(
                enable_faces=True, enable_plates=True, enable_tracking=True
            )

            # Connect worker signals
            self.capture_worker.frame_ready.connect(self._on_frame_ready)
            self.capture_worker.stats_updated.connect(self._on_stats_updated)
            self.capture_worker.error_occurred.connect(self._on_capture_error)
            self.capture_worker.started.connect(self._on_capture_started)
            self.capture_worker.stopped.connect(self._on_capture_stopped)
            self.capture_worker.feature_status_ready.connect(self._on_feature_status_ready)

        # Configure worker with settings from sidebar
        self.capture_worker.configure(
            source_config=source_config,
            fps_target=self.video_settings.get_fps_target(),
            frame_resize=self.video_settings.get_resize(),
            face_similarity_threshold=self.face_controls.get_threshold(),
            tracking_enabled=self.tracking_controls.is_tracking_enabled(),
            **self._get_tracking_params(),
        )

        # Start worker
        self.capture_worker.start()

    def _on_disconnect_clicked(self):
        """Handle Disconnect button click."""
        logger.info("Disconnect button clicked")

        if self.capture_worker and self.capture_worker.isRunning():
            self.capture_worker.stop()
            self.capture_worker.wait()

    def _on_capture_started(self):
        """Handle capture started signal."""
        logger.info("Capture started successfully")
        self.state.set_connected(True)

    def _on_capture_stopped(self):
        """Handle capture stopped signal."""
        logger.info("Capture stopped")
        self.state.set_connected(False)

        # Clear displays
        self.preview_panel.clear()

    def _on_capture_error(self, error_msg: str):
        """Handle capture error.

        Args:
            error_msg: Error message
        """
        logger.error(f"Capture error: {error_msg}")
        self.controls_sidebar.connection_controls.set_error(error_msg)
        self.state.set_connected(False)

    def _on_frame_ready(self, frame_result):
        """Handle new frame from worker.

        Args:
            frame_result: FrameResult object
        """
        # Update preview
        self.preview_panel.update_frame(frame_result)

        # Update detection panels
        self.face_matches_panel.update_from_frame(frame_result)
        self.plate_detections_panel.update_from_frame(frame_result)

        # Update state
        self.state.update_frame(frame_result)

    def _on_stats_updated(self, stats: dict):
        """Handle stats update from worker.

        Args:
            stats: Stats dictionary
        """
        self.preview_panel.update_stats(stats)
        self.state.update_stats(stats)

    def _on_feature_status_ready(self, status: dict):
        """Handle feature initialization status.

        Args:
            status: Feature status dictionary
        """
        # Display feature status in sidebar
        status_lines = []

        if status.get("faces_enabled"):
            gallery_count = status.get("gallery_persons", 0)
            status_lines.append(f"✓ Faces: {gallery_count} persons")
        elif status.get("face_error"):
            status_lines.append(f"✗ Faces: {status['face_error']}")
        else:
            status_lines.append("○ Faces: disabled")

        if status.get("plates_enabled"):
            status_lines.append("✓ Plates: enabled")
        elif status.get("plate_error"):
            status_lines.append(f"✗ Plates: {status['plate_error']}")
        else:
            status_lines.append("○ Plates: disabled")

        self.controls_sidebar.set_feature_status("\n".join(status_lines))

        # Update state
        self.state.update_feature_status(status)

    def _on_connection_state_changed(self, connected: bool):
        """Handle connection state change from AppState.

        Args:
            connected: True if connected, False otherwise
        """
        self.controls_sidebar.connection_controls.set_connected(connected)

    def _on_source_changed(self, source_config):
        """Handle source configuration change.

        Args:
            source_config: New source configuration
        """
        logger.info(f"Source changed: {source_config.type}")
        self.state.set_source_config(source_config)

    def _on_fps_changed(self, fps: int):
        """Handle FPS target change.

        Args:
            fps: New FPS target
        """
        logger.info(f"FPS changed: {fps}")
        self.state.set_fps_target(fps)

    def _on_resize_changed(self, resize):
        """Handle resize option change.

        Args:
            resize: New resize option (tuple or None)
        """
        logger.info(f"Resize changed: {resize}")
        self.state.frame_resize_changed.emit(resize)

    def _on_face_threshold_changed(self, threshold: float):
        """Handle face threshold change.

        Args:
            threshold: New face similarity threshold
        """
        logger.info(f"Face threshold changed: {threshold}")
        self.state.set_face_threshold(threshold)

    def _on_tracking_enabled_changed(self, enabled: bool):
        """Handle tracking enabled state change.

        Args:
            enabled: True if tracking is enabled
        """
        logger.info(f"Tracking enabled changed: {enabled}")
        self.state.set_tracking_enabled(enabled)

    def _on_tracking_params_changed(self, params: dict):
        """Handle tracking parameters change.

        Args:
            params: Tracking parameters dictionary
        """
        logger.info(f"Tracking params changed: {params}")
        self.state.set_tracking_params(params)

    def _emit_tracking_params(self):
        """Collect tracking params from controls and emit state update."""
        params = self._get_tracking_params()
        self._on_tracking_params_changed(params)

    def _get_tracking_params(self) -> dict:
        """Get current tracking parameters."""
        return {
            "frames_required": self.tracking_controls.get_frames_required(),
            "iou_threshold": self.tracking_controls.get_iou_threshold(),
            "max_age_frames": self.tracking_controls.get_max_age(),
            "ocr_agreement_threshold": self.tracking_controls.get_ocr_agreement_threshold(),
        }

    def _on_navigation_changed(self, index: int):
        """Switch content pages based on title bar navigation."""
        self.page_stack.setCurrentIndex(index)

    def _toggle_maximize(self):
        """Toggle between maximized and normal window state."""
        if self.isMaximized():
            self.showNormal()
            self.title_bar.set_maximized(False)
        else:
            self.showMaximized()
            self.title_bar.set_maximized(True)

    def resizeEvent(self, event):
        """Handle window resize to position size grip.

        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)
        # Position size grip in bottom-right corner
        rect = self.rect()
        self.size_grip.move(
            rect.width() - tokens.SIZE_GRIP_SIZE, rect.height() - tokens.SIZE_GRIP_SIZE
        )

    def closeEvent(self, event):
        """Handle window close to save settings and cleanup.

        Args:
            event: QCloseEvent
        """
        # Stop capture if running
        if self.capture_worker and self.capture_worker.isRunning():
            logger.info("Stopping capture before closing...")
            self.capture_worker.stop()
            self.capture_worker.wait()

        # Save settings
        self.state.save_settings()

        event.accept()
