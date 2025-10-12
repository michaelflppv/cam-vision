"""CSV loader for license plate whitelist/blacklist."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Literal, Optional, Set

logger = logging.getLogger(__name__)


class PlateListLoader:
    """
    Loads whitelist and blacklist of license plates from CSV files.

    CSV format (with or without header):
    - Single column: plate number (e.g., "ABC123")
    - Multiple columns: first column is plate number, rest ignored

    All plate numbers are normalized to uppercase and stripped of whitespace.
    """

    def __init__(self, whitelist_path: str, blacklist_path: str):
        """
        Initialize plate list loader.

        Args:
            whitelist_path: Path to whitelist CSV file
            blacklist_path: Path to blacklist CSV file
        """
        self.whitelist_path = Path(whitelist_path)
        self.blacklist_path = Path(blacklist_path)

        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self._loaded = False

    def load(self) -> None:
        """Load whitelist and blacklist from CSV files."""
        if self._loaded:
            logger.warning("Lists already loaded, skipping reload")
            return

        # Load whitelist
        if self.whitelist_path.exists():
            self.whitelist = self._load_csv(self.whitelist_path)
            logger.info(f"Loaded {len(self.whitelist)} plates from whitelist")
        else:
            logger.warning(f"Whitelist not found at {self.whitelist_path}, using empty set")
            self.whitelist = set()

        # Load blacklist
        if self.blacklist_path.exists():
            self.blacklist = self._load_csv(self.blacklist_path)
            logger.info(f"Loaded {len(self.blacklist)} plates from blacklist")
        else:
            logger.warning(f"Blacklist not found at {self.blacklist_path}, using empty set")
            self.blacklist = set()

        self._loaded = True

        # Warn if overlap
        overlap = self.whitelist & self.blacklist
        if overlap:
            logger.warning(
                f"Found {len(overlap)} plates in both whitelist and blacklist: {overlap}"
            )

    def _load_csv(self, csv_path: Path) -> Set[str]:
        """Load plate numbers from CSV file."""
        plates = set()

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)

                for i, row in enumerate(reader):
                    # Skip empty rows
                    if not row or not row[0].strip():
                        continue

                    # Skip header row if it looks like a header
                    if i == 0 and row[0].lower() in ["plate", "number", "license", "id"]:
                        continue

                    # Extract first column and normalize
                    plate = row[0].strip().upper()
                    if plate:
                        plates.add(plate)

        except Exception as e:
            logger.error(f"Failed to load CSV from {csv_path}: {e}")
            raise

        return plates

    def match(self, plate_text: str) -> Optional[Literal["whitelist", "blacklist"]]:
        """
        Check if a plate matches whitelist or blacklist.

        Args:
            plate_text: Plate text (will be normalized)

        Returns:
            "whitelist" if in whitelist, "blacklist" if in blacklist, None if neither
        """
        if not self._loaded:
            raise RuntimeError("Lists not loaded. Call load() first.")

        # Normalize plate text
        normalized = plate_text.strip().upper()

        # Check blacklist first (higher priority)
        if normalized in self.blacklist:
            return "blacklist"

        # Check whitelist
        if normalized in self.whitelist:
            return "whitelist"

        return None

    def size(self) -> dict:
        """Get list sizes."""
        return {"whitelist": len(self.whitelist), "blacklist": len(self.blacklist)}

    def __repr__(self) -> str:
        return (
            f"PlateListLoader(whitelist={len(self.whitelist)}, " f"blacklist={len(self.blacklist)})"
        )
