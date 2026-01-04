"""Enrollment controls for accepted faces and plates."""

from __future__ import annotations

import csv
import logging
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cam_vision.config import load_settings

from ..styles import tokens

logger = logging.getLogger(__name__)


class EnrollmentControls(QWidget):
    """Controls for adding accepted faces and plates."""

    def __init__(self):
        """Initialize enrollment controls."""
        super().__init__()
        self._gallery_path, self._whitelist_path = self._load_paths()
        self._setup_ui()

    def _load_paths(self) -> tuple[Path, Path]:
        """Load gallery and whitelist paths from settings."""
        try:
            settings = load_settings()
            gallery_path = Path(settings.face.gallery_path)
            whitelist_path = Path(settings.plates.whitelist_path)
        except Exception as exc:
            logger.warning("Failed to load settings for enrollment paths: %s", exc)
            gallery_path = Path("./data/faces/trusted")
            whitelist_path = Path("./data/plates/whitelist.csv")
        return gallery_path, whitelist_path

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(tokens.SPACING_COMFORTABLE)

        # Faces
        faces_header = QLabel("Accepted Faces")
        faces_header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(faces_header)

        faces_desc = QLabel(f"Add a face image to the gallery.\nFolder: {self._gallery_path}")
        faces_desc.setWordWrap(True)
        faces_desc.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(faces_desc)

        name_label = QLabel("Person Name:")
        name_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(name_label)

        self.face_name_input = QLineEdit()
        self.face_name_input.setPlaceholderText("e.g., Jane Doe")
        self.face_name_input.setMinimumHeight(tokens.INPUT_HEIGHT)
        layout.addWidget(self.face_name_input)

        image_label = QLabel("Image File:")
        image_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(image_label)

        image_row = QHBoxLayout()
        image_row.setSpacing(tokens.SPACING_TIGHT)

        self.face_image_input = QLineEdit()
        self.face_image_input.setPlaceholderText("/path/to/face.jpg")
        self.face_image_input.setMinimumHeight(tokens.INPUT_HEIGHT)
        image_row.addWidget(self.face_image_input, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary")
        browse_btn.setMinimumHeight(tokens.INPUT_HEIGHT)
        browse_btn.clicked.connect(self._browse_face_image)
        image_row.addWidget(browse_btn)

        layout.addLayout(image_row)

        add_face_btn = QPushButton("Add Face")
        add_face_btn.setObjectName("primary")
        add_face_btn.setMinimumHeight(tokens.BUTTON_HEIGHT_LARGE)
        add_face_btn.clicked.connect(self._add_face)
        layout.addWidget(add_face_btn)

        self.face_status = QLabel("")
        self.face_status.setWordWrap(True)
        self.face_status.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(self.face_status)

        # Plates
        plates_header = QLabel("Accepted Plates")
        plates_header.setStyleSheet(
            f"color: {tokens.TEXT_PRIMARY}; "
            f"font-size: {tokens.FONT_SIZE_NORMAL}px; "
            f"font-weight: 600;"
        )
        layout.addWidget(plates_header)

        plates_desc = QLabel(f"Add a plate to the whitelist.\nFile: {self._whitelist_path}")
        plates_desc.setWordWrap(True)
        plates_desc.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(plates_desc)

        plate_label = QLabel("Plate Number:")
        plate_label.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(plate_label)

        self.plate_input = QLineEdit()
        self.plate_input.setPlaceholderText("ABC123")
        self.plate_input.setMinimumHeight(tokens.INPUT_HEIGHT)
        layout.addWidget(self.plate_input)

        add_plate_btn = QPushButton("Add Plate")
        add_plate_btn.setObjectName("primary")
        add_plate_btn.setMinimumHeight(tokens.BUTTON_HEIGHT_LARGE)
        add_plate_btn.clicked.connect(self._add_plate)
        layout.addWidget(add_plate_btn)

        self.plate_status = QLabel("")
        self.plate_status.setWordWrap(True)
        self.plate_status.setStyleSheet(
            f"color: {tokens.TEXT_SECONDARY}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(self.plate_status)

    def _browse_face_image(self):
        """Open a file picker for face images."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Face Image",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg)",
        )
        if file_path:
            self.face_image_input.setText(file_path)

    def _add_face(self):
        """Add a face image to the gallery."""
        name_raw = self.face_name_input.text().strip()
        image_path = self.face_image_input.text().strip()

        if not name_raw:
            self._set_face_status("Enter a person name.", error=True)
            return
        if not image_path:
            self._set_face_status("Select an image file.", error=True)
            return

        person_id = self._sanitize_person_id(name_raw)
        if not person_id:
            self._set_face_status("Name must include letters or numbers.", error=True)
            return

        image_file = Path(image_path)
        if not image_file.exists() or not image_file.is_file():
            self._set_face_status("Image file not found.", error=True)
            return

        dest_dir = self._gallery_path / person_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = self._unique_destination(dest_dir, image_file.name)
        try:
            shutil.copy2(image_file, dest_path)
        except Exception as exc:
            logger.error("Failed to copy face image: %s", exc, exc_info=True)
            self._set_face_status("Failed to add face image.", error=True)
            return

        self._set_face_status(
            f"Added to {dest_path}. Rebuild gallery cache and reconnect to apply."
        )
        self.face_image_input.clear()

    def _add_plate(self):
        """Add a plate to the whitelist CSV."""
        plate_raw = self.plate_input.text().strip()
        if not plate_raw:
            self._set_plate_status("Enter a plate number.", error=True)
            return

        plate_text = plate_raw.upper()
        self._whitelist_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._load_existing_plates(self._whitelist_path)

        if plate_text in existing:
            self._set_plate_status("Plate is already in the whitelist.", error=True)
            return

        write_header = not self._whitelist_path.exists() or self._whitelist_path.stat().st_size == 0
        try:
            with open(self._whitelist_path, "a", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                if write_header:
                    writer.writerow(["plate"])
                writer.writerow([plate_text])
        except Exception as exc:
            logger.error("Failed to update whitelist: %s", exc, exc_info=True)
            self._set_plate_status("Failed to add plate.", error=True)
            return

        self._set_plate_status(f"Added {plate_text} to whitelist.")
        self.plate_input.clear()

    def _load_existing_plates(self, csv_path: Path) -> set[str]:
        """Load plate numbers from CSV file."""
        if not csv_path.exists():
            return set()
        plates = set()
        try:
            with open(csv_path, "r", encoding="utf-8") as csv_file:
                reader = csv.reader(csv_file)
                for i, row in enumerate(reader):
                    if not row or not row[0].strip():
                        continue
                    if i == 0 and row[0].lower() in ["plate", "number", "license", "id"]:
                        continue
                    plates.add(row[0].strip().upper())
        except Exception as exc:
            logger.error("Failed to read whitelist: %s", exc, exc_info=True)
        return plates

    def _sanitize_person_id(self, name: str) -> str:
        """Normalize person name for folder usage."""
        cleaned = []
        for char in name.strip().lower():
            if char.isalnum():
                cleaned.append(char)
            elif char in [" ", "-", "_"]:
                cleaned.append("_")
        person_id = "".join(cleaned).strip("_")
        while "__" in person_id:
            person_id = person_id.replace("__", "_")
        return person_id

    def _unique_destination(self, dest_dir: Path, filename: str) -> Path:
        """Pick a unique destination path for a copied image."""
        target = dest_dir / filename
        if not target.exists():
            return target
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while True:
            candidate = dest_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _set_face_status(self, message: str, error: bool = False):
        """Update the face status label."""
        color = tokens.ACCENT_ERROR if error else tokens.TEXT_SECONDARY
        self.face_status.setStyleSheet(
            f"color: {color}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        self.face_status.setText(message)

    def _set_plate_status(self, message: str, error: bool = False):
        """Update the plate status label."""
        color = tokens.ACCENT_ERROR if error else tokens.TEXT_SECONDARY
        self.plate_status.setStyleSheet(
            f"color: {color}; " f"font-size: {tokens.FONT_SIZE_SMALL}px;"
        )
        self.plate_status.setText(message)
