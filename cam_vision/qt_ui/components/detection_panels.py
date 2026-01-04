"""Scrollable panels for displaying detection results."""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from cam_vision.ui.capture import FrameResult

from ..styles import tokens
from .detection_card import FaceMatchCard, PlateDetectionCard

logger = logging.getLogger(__name__)


class FaceMatchesPanel(QWidget):
    """Scrollable panel displaying face match results.

    Shows a vertical list of FaceMatchCard widgets with:
    - Matched faces (green border)
    - Unknown faces (amber border)
    """

    def __init__(self, max_cards: int = 20):
        """Initialize face matches panel.

        Args:
            max_cards: Maximum number of cards to display
        """
        super().__init__()
        self._max_cards = max_cards
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("Face Matches")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_HEADING}px; "
            f"font-weight: 600; "
            f"padding: {tokens.PADDING_MEDIUM}px;"
        )
        layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {tokens.BORDER_UNFOCUSED}; "
            f"background-color: {tokens.BACKGROUND_SUBTLE}; }}"
        )

        # Container for cards
        self.cards_container = QWidget()
        self.cards_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
        )
        self.cards_layout.setSpacing(tokens.SPACING_COMFORTABLE)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, 1)

        # Stats label
        self.stats_label = QLabel("No faces detected")
        self.stats_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; "
            f"font-size: {tokens.FONT_SIZE_SMALL}px; "
            f"padding: {tokens.PADDING_SMALL}px;"
        )
        layout.addWidget(self.stats_label)

    def update_from_frame(self, frame_result: FrameResult):
        """Update panel with new frame result.

        Args:
            frame_result: FrameResult from CaptureManager
        """
        # Clear existing cards
        self._clear_cards()

        observations = frame_result.face_observations
        if not observations:
            self.stats_label.setText("No faces detected")
            return

        # Limit to max_cards
        observations_to_show = observations[: self._max_cards]

        # Create cards
        for obs in observations_to_show:
            try:
                # Crop face from frame
                bbox = obs.detection.bbox
                cropped = frame_result.frame.image[bbox.y1 : bbox.y2, bbox.x1 : bbox.x2]

                if cropped.size == 0:
                    continue

                # Create card
                card = FaceMatchCard(face_observation=obs, cropped_face=cropped)
                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

            except Exception as e:
                logger.error(f"Error creating face card: {e}", exc_info=True)

        # Update stats
        matched_count = sum(1 for obs in observations if obs.matched)
        unknown_count = len(observations) - matched_count
        self.stats_label.setText(
            f"{matched_count} matched, {unknown_count} unknown ({len(observations)} total)"
        )

    def _clear_cards(self):
        """Remove all cards from the layout."""
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class PlateDetectionsPanel(QWidget):
    """Scrollable panel displaying plate detection results.

    Shows a vertical list of PlateDetectionCard widgets with:
    - Recognized plates with color-coded borders (whitelist/blacklist)
    - Pending OCR results
    - Detection candidates
    """

    def __init__(self, max_cards: int = 20):
        """Initialize plate detections panel.

        Args:
            max_cards: Maximum number of cards to display
        """
        super().__init__()
        self._max_cards = max_cards
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("Plate Detections")
        header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_HEADING}px; "
            f"font-weight: 600; "
            f"padding: {tokens.PADDING_MEDIUM}px;"
        )
        layout.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setStyleSheet(
            f"QScrollArea {{ border: 1px solid {tokens.BORDER_UNFOCUSED}; "
            f"background-color: {tokens.BACKGROUND_SUBTLE}; }}"
        )

        # Container for cards
        self.cards_container = QWidget()
        self.cards_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
            tokens.PADDING_MEDIUM,
        )
        self.cards_layout.setSpacing(tokens.SPACING_COMFORTABLE)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, 1)

        # Stats label
        self.stats_label = QLabel("No plates detected")
        self.stats_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; "
            f"font-size: {tokens.FONT_SIZE_SMALL}px; "
            f"padding: {tokens.PADDING_SMALL}px;"
        )
        layout.addWidget(self.stats_label)

    def update_from_frame(self, frame_result: FrameResult):
        """Update panel with new frame result.

        Args:
            frame_result: FrameResult from CaptureManager
        """
        # Clear existing cards
        self._clear_cards()

        observations = frame_result.plate_observations

        # Filter out rejected observations
        displayable = [obs for obs in observations if obs.is_displayable()]

        if not displayable:
            self.stats_label.setText("No plates detected")
            return

        # Limit to max_cards
        observations_to_show = displayable[: self._max_cards]

        # Create cards
        for obs in observations_to_show:
            try:
                # Crop plate from frame
                bbox = obs.detection.bbox
                cropped = frame_result.frame.image[bbox.y1 : bbox.y2, bbox.x1 : bbox.x2]

                if cropped.size == 0:
                    continue

                # Create card
                card = PlateDetectionCard(plate_observation=obs, cropped_plate=cropped)
                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

            except Exception as e:
                logger.error(f"Error creating plate card: {e}", exc_info=True)

        # Update stats
        read_count = sum(1 for obs in displayable if obs.status == "read")
        pending_count = len(displayable) - read_count
        self.stats_label.setText(
            f"{read_count} read, {pending_count} pending ({len(displayable)} total)"
        )

    def _clear_cards(self):
        """Remove all cards from the layout."""
        while self.cards_layout.count() > 1:  # Keep the stretch
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
