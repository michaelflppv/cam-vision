"""Base widget for displaying detection results as cards."""

import logging

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ..styles import tokens

logger = logging.getLogger(__name__)


class DetectionCard(QWidget):
    """Base card widget for displaying detection results.

    Shows:
    - Cropped detection image (thumbnail)
    - Primary label (person ID, plate text, etc.)
    - Secondary metadata (confidence, timestamp)

    Design follows monochromatic style with zero border-radius.
    """

    def __init__(
        self,
        image,
        primary_label: str,
        secondary_label: str = "",
        thumbnail_size: int = 80,
        border_color: str = None,
    ):
        """Initialize the detection card.

        Args:
            image: BGR numpy array of cropped detection
            primary_label: Main text (e.g., person ID, plate text)
            secondary_label: Additional info (e.g., confidence, time)
            thumbnail_size: Size of square thumbnail (pixels)
            border_color: Optional border color (uses default if None)
        """
        super().__init__()

        self._thumbnail_size = thumbnail_size
        self._border_color = border_color or tokens.BORDER_UNFOCUSED

        self._setup_ui(image, primary_label, secondary_label)

    def _setup_ui(self, image, primary_label: str, secondary_label: str):
        """Set up the card UI."""
        # Card container with border
        self.setStyleSheet(
            f"background-color: {tokens.BACKGROUND_PRIMARY}; "
            f"border: 1px solid {self._border_color}; "
            f"padding: {tokens.PADDING_MEDIUM}px;"
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Thumbnail
        thumbnail_label = self._create_thumbnail(image)
        layout.addWidget(thumbnail_label)

        # Text content (vertical)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(tokens.SPACING_TIGHT)

        # Primary label (bold, larger)
        primary = QLabel(primary_label)
        primary.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600; "
            f"border: none;"
        )
        primary.setWordWrap(True)
        text_layout.addWidget(primary)

        # Secondary label (smaller, gray)
        if secondary_label:
            secondary = QLabel(secondary_label)
            secondary.setStyleSheet(
                f"color: {tokens.TEXT_SECONDARY}; "
                f"font-size: {tokens.FONT_SIZE_SMALL}px; "
                f"border: none;"
            )
            secondary.setWordWrap(True)
            text_layout.addWidget(secondary)

        text_layout.addStretch()

        layout.addLayout(text_layout, 1)

    def _create_thumbnail(self, image) -> QLabel:
        """Create thumbnail QLabel from BGR image.

        Args:
            image: BGR numpy array

        Returns:
            QLabel with scaled thumbnail
        """
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Resize to thumbnail size
            resized = cv2.resize(
                image_rgb,
                (self._thumbnail_size, self._thumbnail_size),
                interpolation=cv2.INTER_AREA,
            )

            # Convert to QImage
            height, width, channels = resized.shape
            bytes_per_line = channels * width
            q_image = QImage(resized.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # Create QPixmap
            pixmap = QPixmap.fromImage(q_image)

            # Create label
            label = QLabel()
            label.setPixmap(pixmap)
            label.setFixedSize(self._thumbnail_size, self._thumbnail_size)
            label.setStyleSheet(
                f"border: 1px solid {tokens.BORDER_UNFOCUSED}; "
                f"background-color: {tokens.THUMBNAIL_BACKGROUND};"
            )

            return label

        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}", exc_info=True)

            # Fallback: empty placeholder
            label = QLabel("?")
            label.setFixedSize(self._thumbnail_size, self._thumbnail_size)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(
                f"border: 1px solid {tokens.BORDER_UNFOCUSED}; "
                f"background-color: {tokens.BACKGROUND_SUBTLE}; "
                f"color: {tokens.TEXT_SECONDARY};"
            )
            return label


class FaceMatchCard(DetectionCard):
    """Card displaying a face match result."""

    def __init__(self, face_observation, cropped_face):
        """Initialize face match card.

        Args:
            face_observation: FaceObservation object
            cropped_face: BGR numpy array of cropped face
        """
        # Format primary label
        if face_observation.matched and face_observation.person_id:
            primary = face_observation.person_id
        else:
            primary = "Unknown"

        # Format secondary label
        secondary_parts = []
        if face_observation.similarity is not None:
            secondary_parts.append(f"Similarity: {face_observation.similarity:.3f}")
        if face_observation.detection.track_id is not None:
            secondary_parts.append(f"Track #{face_observation.detection.track_id}")
        secondary = " • ".join(secondary_parts) if secondary_parts else ""

        # Choose border color (green for match, amber for unknown)
        border_color = tokens.ACCENT_SUCCESS if face_observation.matched else tokens.ACCENT_WARNING

        super().__init__(
            image=cropped_face,
            primary_label=primary,
            secondary_label=secondary,
            thumbnail_size=80,
            border_color=border_color,
        )


class PlateDetectionCard(DetectionCard):
    """Card displaying a plate detection result."""

    def __init__(self, plate_observation, cropped_plate):
        """Initialize plate detection card.

        Args:
            plate_observation: PlateObservation object
            cropped_plate: BGR numpy array of cropped plate
        """
        # Format primary label (plate text)
        if plate_observation.text_clean:
            primary = plate_observation.text_clean
        elif plate_observation.text_raw:
            primary = plate_observation.text_raw
        else:
            primary = "Plate Detected"

        # Format secondary label
        secondary_parts = []
        if plate_observation.confidence > 0:
            secondary_parts.append(f"Confidence: {plate_observation.confidence:.1f}%")
        if plate_observation.matched_list:
            secondary_parts.append(f"List: {plate_observation.matched_list}")
        if plate_observation.status and plate_observation.status != "read":
            secondary_parts.append(f"Status: {plate_observation.status}")
        if plate_observation.detection.track_id is not None:
            secondary_parts.append(f"Track #{plate_observation.detection.track_id}")
        secondary = " • ".join(secondary_parts) if secondary_parts else ""

        # Choose border color based on status
        if plate_observation.matched_list == "whitelist":
            border_color = tokens.ACCENT_SUCCESS
        elif plate_observation.matched_list == "blacklist":
            border_color = tokens.ACCENT_ERROR
        elif plate_observation.status == "ocr_low_confidence":
            border_color = tokens.ACCENT_WARNING
        else:
            border_color = tokens.ACCENT_INFO

        super().__init__(
            image=cropped_plate,
            primary_label=primary,
            secondary_label=secondary,
            thumbnail_size=100,  # Plates are wider
            border_color=border_color,
        )
