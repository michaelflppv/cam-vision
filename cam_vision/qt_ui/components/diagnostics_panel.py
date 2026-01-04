"""System diagnostics panel showing feature status and health checks."""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from cam_vision.ui.diagnostics import FeatureStatus, SystemDiagnostics, run_diagnostics

from ..styles import tokens

logger = logging.getLogger(__name__)


class DiagnosticsPanel(QWidget):
    """System diagnostics panel.

    Displays health checks for:
    - Face recognition
    - Plate detection
    - InsightFace models
    - YOLO model
    - Tesseract OCR
    - Face gallery

    Signals:
        diagnostics_updated: Emitted when diagnostics are refreshed (SystemDiagnostics)
    """

    diagnostics_updated = Signal(object)

    def __init__(self):
        """Initialize diagnostics panel."""
        super().__init__()

        self._diagnostics = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Header with refresh button
        header_layout = QVBoxLayout()
        header_layout.setSpacing(tokens.SPACING_TIGHT)

        header = QLabel("System Diagnostics")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        header_layout.addWidget(header)

        description = QLabel("Check system health and feature availability.")
        description.setWordWrap(True)
        description.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        header_layout.addWidget(description)

        layout.addLayout(header_layout)

        # Refresh button
        self.refresh_btn = QPushButton("Run Diagnostics")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.clicked.connect(self.run_checks)
        layout.addWidget(self.refresh_btn)

        # Scroll area for results
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {tokens.BORDER_UNFOCUSED}; "
            f"background-color: {tokens.BACKGROUND_SUBTLE}; }}"
        )

        # Container for diagnostic items
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
        )
        self.results_layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Placeholder message
        self.placeholder_label = QLabel("Click 'Run Diagnostics' to check system health.")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"padding: {tokens.PADDING_LARGE}px;"
        )
        self.results_layout.addWidget(self.placeholder_label)

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll, 1)

    def run_checks(self):
        """Run diagnostics and update display."""
        logger.info("Running system diagnostics...")

        # Clear existing results
        self._clear_results()

        # Show loading message
        loading_label = QLabel("Running diagnostics...")
        loading_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_NORMAL}px;"
        )
        self.results_layout.addWidget(loading_label)

        try:
            # Run diagnostics
            self._diagnostics = run_diagnostics()

            # Clear loading message
            self._clear_results()

            # Display results
            self._display_results(self._diagnostics)

            # Emit signal
            self.diagnostics_updated.emit(self._diagnostics)

        except Exception as e:
            logger.error(f"Failed to run diagnostics: {e}", exc_info=True)
            self._clear_results()
            error_label = QLabel(f"Error running diagnostics:\n{str(e)}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet(
                f"color: #FF0000; "  # Red for errors
                f"font-size: {tokens.FONT_SIZE_NORMAL}px;"
            )
            self.results_layout.addWidget(error_label)

    def _clear_results(self):
        """Clear all result items."""
        while self.results_layout.count() > 0:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _display_results(self, diagnostics: SystemDiagnostics):
        """Display diagnostic results.

        Args:
            diagnostics: SystemDiagnostics object
        """
        # Overall status header
        all_ok = diagnostics.all_ok()
        if all_ok:
            status_icon = "✓"
            status_text = "All Systems Operational"
            status_color = "#00AA00"  # Green
        else:
            status_icon = "✗"
            failures = len(diagnostics.get_failures())
            status_text = f"{failures} Issue(s) Detected"
            status_color = "#FF0000"  # Red

        overall_label = QLabel(f"{status_icon} {status_text}")
        overall_label.setStyleSheet(
            f"color: {status_color}; "
            f"font-size: {tokens.FONT_SIZE_LARGE}px; "
            f"font-weight: 600; "
            f"padding: {tokens.PADDING_SMALL}px;"
        )
        self.results_layout.addWidget(overall_label)

        # Individual feature statuses
        features = [
            diagnostics.face_recognition,
            diagnostics.plate_detection,
            diagnostics.insightface_models,
            diagnostics.yolo_model,
            diagnostics.tesseract,
            diagnostics.gallery,
        ]

        for feature in features:
            feature_widget = self._create_feature_widget(feature)
            self.results_layout.addWidget(feature_widget)

        # Stretch at the end
        self.results_layout.addStretch()

    def _create_feature_widget(self, feature: FeatureStatus) -> QWidget:
        """Create widget for a single feature status.

        Args:
            feature: FeatureStatus object

        Returns:
            Widget displaying feature status
        """
        widget = QWidget()
        widget.setStyleSheet(
            f"background-color: {tokens.BACKGROUND_PRIMARY}; "
            f"border: 1px solid {tokens.BORDER_UNFOCUSED}; "
            f"padding: {tokens.PADDING_MEDIUM}px;"
        )

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_TIGHT)

        # Feature name with status icon
        if not feature.enabled:
            icon = "○"  # Disabled
            color = tokens.TEXT_SECONDARY
        elif feature.available:
            icon = "✓"  # OK
            color = "#00AA00"  # Green
        else:
            icon = "✗"  # Error
            color = "#FF0000"  # Red

        name_label = QLabel(f"{icon} {feature.name}")
        name_label.setStyleSheet(
            f"color: {color}; " f"font-size: {tokens.FONT_SIZE_NORMAL}px; " f"font-weight: 600;"
        )
        layout.addWidget(name_label)

        # Details
        if feature.details:
            details_label = QLabel(feature.details)
            details_label.setWordWrap(True)
            details_label.setStyleSheet(
                f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
            )
            layout.addWidget(details_label)

        # Error message
        if feature.error:
            error_label = QLabel(f"Error: {feature.error}")
            error_label.setWordWrap(True)
            error_label.setStyleSheet(f"color: #FF0000; " f"font-size: {tokens.FONT_SIZE_SMALL}px;")
            layout.addWidget(error_label)

        return widget

    def get_diagnostics(self) -> SystemDiagnostics | None:
        """Get latest diagnostics results.

        Returns:
            SystemDiagnostics or None if not run yet
        """
        return self._diagnostics
