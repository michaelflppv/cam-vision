"""Face gallery management - loading, building, and matching against trusted faces."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class FaceGallery:
    """
    Manages a gallery of trusted face embeddings.

    Features:
    - Build gallery from folder of person images
    - Average embeddings for multiple images per person (robustness)
    - Save/load precomputed embeddings (cache)
    - Match query embeddings against gallery (cosine similarity)
    """

    def __init__(self, gallery_path: str, cache_path: str):
        """
        Initialize gallery.

        Args:
            gallery_path: Folder containing person subfolders with images
                         Example: gallery_path/john_doe/*.jpg
            cache_path: Path to save/load precomputed embeddings (.npz file)
        """
        self.gallery_path = Path(gallery_path)
        self.cache_path = Path(cache_path)

        self.person_ids: list[str] = []
        self.embeddings: Optional[np.ndarray] = None  # Shape: (N, 512)
        self._loaded = False

    def build(self, embedder, force_rebuild: bool = False) -> int:
        """
        Build gallery from images in gallery_path.

        Args:
            embedder: InsightFace model with get() method
            force_rebuild: Rebuild even if cache exists

        Returns:
            Number of persons enrolled
        """
        if self.cache_path.exists() and not force_rebuild:
            logger.info(f"Cache exists at {self.cache_path}, use force_rebuild=True to rebuild")
            return 0

        if not self.gallery_path.exists():
            raise FileNotFoundError(f"Gallery path not found: {self.gallery_path}")

        # Scan for person folders
        person_folders = [
            d for d in self.gallery_path.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

        if len(person_folders) == 0:
            raise ValueError(f"No person folders found in {self.gallery_path}")

        logger.info(f"Building gallery from {len(person_folders)} persons...")

        enrolled = {}
        for person_dir in person_folders:
            person_id = person_dir.name

            # Find all images
            image_files = []
            for ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
                image_files.extend(person_dir.glob(ext))

            if len(image_files) == 0:
                logger.warning(f"No images found for {person_id}, skipping")
                continue

            # Compute embeddings for each image
            person_embeddings = []
            for img_path in image_files:
                try:
                    # Load image with OpenCV (BGR format expected by InsightFace)
                    import cv2

                    img = cv2.imread(str(img_path))
                    if img is None:
                        logger.warning(f"Failed to read image {img_path}")
                        continue

                    # Detect faces
                    faces = embedder.get(img)

                    if len(faces) == 0:
                        logger.warning(f"No face detected in {img_path.name}")
                        continue

                    if len(faces) > 1:
                        logger.warning(f"Multiple faces detected in {img_path.name}, using first")

                    # Get embedding (512-dim vector)
                    embedding = faces[0].embedding
                    person_embeddings.append(embedding)
                    logger.debug(f"Enrolled {img_path.name} for {person_id}")

                except Exception as e:
                    logger.error(f"Error processing {img_path}: {e}")
                    continue

            if len(person_embeddings) == 0:
                logger.error(f"No valid embeddings for {person_id}, skipping")
                continue

            # Average embeddings for robustness
            avg_embedding = np.mean(person_embeddings, axis=0)
            enrolled[person_id] = {
                "embedding": avg_embedding,
                "num_images": len(person_embeddings),
            }

            logger.info(f"Enrolled {person_id} with {len(person_embeddings)} images")

        if len(enrolled) == 0:
            raise ValueError("No persons successfully enrolled")

        # Save to cache
        self._save_gallery(enrolled)

        return len(enrolled)

    def load(self) -> None:
        """Load precomputed embeddings from cache."""
        if not self.cache_path.exists():
            raise FileNotFoundError(
                f"Gallery cache not found at {self.cache_path}. "
                "Run enrollment first with securevision-face-enroll"
            )

        try:
            data = np.load(self.cache_path, allow_pickle=True)
            self.person_ids = data["person_ids"].tolist()
            self.embeddings = data["embeddings"]
            self._loaded = True

            logger.info(
                f"Loaded gallery with {len(self.person_ids)} persons from {self.cache_path}"
            )

            # Validate embeddings shape
            if self.embeddings.shape[0] != len(self.person_ids):
                raise ValueError(
                    f"Mismatch: {len(self.person_ids)} person IDs but "
                    f"{self.embeddings.shape[0]} embeddings"
                )

            # Load metadata if available
            metadata_path = self.cache_path.parent / f"{self.cache_path.stem}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    logger.debug(f"Gallery metadata: {metadata}")

        except Exception as e:
            logger.error(f"Failed to load gallery cache: {e}")
            raise

    def match(self, query_embedding: np.ndarray, threshold: float) -> Optional[tuple[str, float]]:
        """
        Match query embedding against gallery.

        Args:
            query_embedding: Face embedding (512-dim vector)
            threshold: Minimum cosine similarity for match (0.0-1.0)

        Returns:
            (person_id, similarity) if match found, else None
        """
        if not self._loaded:
            raise RuntimeError("Gallery not loaded. Call load() first.")

        if len(self.person_ids) == 0:
            logger.warning("Gallery is empty, no matches possible")
            return None

        # Reshape embeddings for sklearn
        query = query_embedding.reshape(1, -1)
        gallery = self.embeddings

        # Compute cosine similarity with all gallery embeddings
        similarities = cosine_similarity(query, gallery)[0]

        # Find best match
        best_idx = np.argmax(similarities)
        best_similarity = similarities[best_idx]

        # Check threshold
        if best_similarity >= threshold:
            person_id = self.person_ids[best_idx]
            logger.debug(f"Match found: {person_id} (similarity={best_similarity:.3f})")
            return (person_id, float(best_similarity))

        logger.debug(
            f"No match above threshold (best={best_similarity:.3f}, threshold={threshold})"
        )
        return None

    def _save_gallery(self, enrolled: dict) -> None:
        """Save enrolled data to cache files."""
        # Ensure cache directory exists
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Save embeddings as .npz
        person_ids = list(enrolled.keys())
        embeddings = np.array([data["embedding"] for data in enrolled.values()])

        np.savez(
            self.cache_path,
            person_ids=np.array(person_ids),
            embeddings=embeddings,
        )

        logger.info(f"Saved {len(person_ids)} person embeddings to {self.cache_path}")

        # Save metadata as JSON
        metadata_path = self.cache_path.parent / f"{self.cache_path.stem}_metadata.json"
        metadata = {
            pid: {
                "num_images": data["num_images"],
                "enrolled_at": datetime.now().isoformat(),
            }
            for pid, data in enrolled.items()
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved metadata to {metadata_path}")

    def get_person_ids(self) -> list[str]:
        """Get list of enrolled person IDs."""
        if not self._loaded:
            raise RuntimeError("Gallery not loaded")
        return self.person_ids.copy()

    def size(self) -> int:
        """Get number of persons in gallery."""
        if not self._loaded:
            return 0
        return len(self.person_ids)
