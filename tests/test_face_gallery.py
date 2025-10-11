"""Tests for face gallery management."""

from __future__ import annotations

from unittest.mock import Mock

import numpy as np
import pytest

from cam_vision.face.gallery import FaceGallery


class TestFaceGallery:
    """Test FaceGallery initialization and loading."""

    def test_gallery_initialization(self, tmp_path):
        """Gallery should initialize with paths."""
        gallery_path = tmp_path / "gallery"
        cache_path = tmp_path / "cache.npz"

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        assert gallery.gallery_path == gallery_path
        assert gallery.cache_path == cache_path
        assert not gallery._loaded

    def test_load_gallery_not_found_raises_error(self, tmp_path):
        """Loading non-existent cache should raise error."""
        gallery_path = tmp_path / "gallery"
        cache_path = tmp_path / "nonexistent.npz"

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        with pytest.raises(FileNotFoundError, match="cache not found"):
            gallery.load()

    def test_load_gallery_from_cache(self, tmp_path):
        """Should load gallery from valid cache."""
        cache_path = tmp_path / "test.npz"

        # Create mock cache
        person_ids = np.array(["john", "jane"])
        embeddings = np.random.rand(2, 512).astype(np.float32)

        np.savez(cache_path, person_ids=person_ids, embeddings=embeddings)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))
        gallery.load()

        assert gallery._loaded
        assert gallery.person_ids == ["john", "jane"]
        assert gallery.embeddings.shape == (2, 512)

    def test_load_gallery_mismatch_raises_error(self, tmp_path):
        """Loading cache with mismatched dimensions should raise error."""
        cache_path = tmp_path / "test.npz"

        # Create invalid cache (2 IDs, 3 embeddings)
        person_ids = np.array(["john", "jane"])
        embeddings = np.random.rand(3, 512).astype(np.float32)

        np.savez(cache_path, person_ids=person_ids, embeddings=embeddings)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))

        with pytest.raises(ValueError, match="Mismatch"):
            gallery.load()


class TestGalleryMatching:
    """Test gallery matching functionality."""

    def test_match_above_threshold(self, tmp_path):
        """Should return match when similarity >= threshold."""
        cache_path = tmp_path / "test.npz"

        # Create gallery with known embedding
        person_ids = np.array(["john"])
        gallery_embedding = np.array([[1.0] * 512])  # Normalized vector

        np.savez(cache_path, person_ids=person_ids, embeddings=gallery_embedding)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))
        gallery.load()

        # Query with very similar embedding (slightly perturbed)
        query_embedding = gallery_embedding[0] + np.random.randn(512) * 0.01
        query_embedding = query_embedding / np.linalg.norm(query_embedding)  # Normalize

        # Should match with high similarity
        result = gallery.match(query_embedding, threshold=0.3)

        assert result is not None
        person_id, similarity = result
        assert person_id == "john"
        assert similarity > 0.3  # Should be quite high

    def test_match_below_threshold(self, tmp_path):
        """Should return None when similarity < threshold."""
        cache_path = tmp_path / "test.npz"

        # Create gallery
        person_ids = np.array(["john"])
        gallery_embedding = np.array([[1.0] + [0.0] * 511])  # Vector in one direction

        np.savez(cache_path, person_ids=person_ids, embeddings=gallery_embedding)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))
        gallery.load()

        # Query with very different embedding (orthogonal vector)
        query_embedding = np.array([0.0] + [1.0] + [0.0] * 510)

        # Cosine similarity should be ~0 (orthogonal)
        result = gallery.match(query_embedding, threshold=0.5)

        assert result is None

    def test_match_not_loaded_raises_error(self, tmp_path):
        """Matching without loading should raise error."""
        gallery = FaceGallery(str(tmp_path / "gallery"), str(tmp_path / "cache.npz"))

        with pytest.raises(RuntimeError, match="not loaded"):
            gallery.match(np.random.rand(512), threshold=0.5)

    def test_match_empty_gallery(self, tmp_path):
        """Empty gallery should return None."""
        cache_path = tmp_path / "test.npz"

        # Create empty gallery
        person_ids = np.array([])
        embeddings = np.empty((0, 512))

        np.savez(cache_path, person_ids=person_ids, embeddings=embeddings)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))
        gallery.load()

        result = gallery.match(np.random.rand(512), threshold=0.5)

        assert result is None


class TestGalleryBuilding:
    """Test gallery building from images."""

    def test_build_with_no_gallery_path_raises_error(self, tmp_path):
        """Building from non-existent path should raise error."""
        gallery_path = tmp_path / "nonexistent"
        cache_path = tmp_path / "cache.npz"

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        mock_embedder = Mock()

        with pytest.raises(FileNotFoundError, match="Gallery path not found"):
            gallery.build(mock_embedder)

    def test_build_with_no_person_folders_raises_error(self, tmp_path):
        """Building from empty gallery should raise error."""
        gallery_path = tmp_path / "gallery"
        gallery_path.mkdir()

        cache_path = tmp_path / "cache.npz"

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        mock_embedder = Mock()

        with pytest.raises(ValueError, match="No person folders found"):
            gallery.build(mock_embedder)

    def test_build_skips_cache_if_exists(self, tmp_path):
        """Building should skip if cache exists and not force_rebuild."""
        gallery_path = tmp_path / "gallery"
        gallery_path.mkdir()

        cache_path = tmp_path / "cache.npz"
        cache_path.touch()  # Create empty cache

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        mock_embedder = Mock()

        num_enrolled = gallery.build(mock_embedder, force_rebuild=False)

        assert num_enrolled == 0
        assert not mock_embedder.get.called

    def test_build_with_mock_images(self, tmp_path):
        """Test building gallery with mocked face detection."""
        # Create gallery structure
        gallery_path = tmp_path / "gallery"
        john_path = gallery_path / "john_doe"
        john_path.mkdir(parents=True)

        # Create dummy image files
        (john_path / "photo1.jpg").touch()
        (john_path / "photo2.jpg").touch()

        cache_path = tmp_path / "cache.npz"

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        # Mock embedder
        mock_face = Mock()
        mock_face.embedding = np.random.rand(512).astype(np.float32)

        mock_embedder = Mock()
        mock_embedder.get.return_value = [mock_face]  # Return one detected face

        # Need to patch cv2.imread to return valid image
        from unittest.mock import patch

        with patch("cv2.imread") as mock_imread:
            mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

            num_enrolled = gallery.build(mock_embedder, force_rebuild=True)

        assert num_enrolled == 1
        assert cache_path.exists()

        # Verify cache contents
        data = np.load(cache_path, allow_pickle=True)
        assert "john_doe" in data["person_ids"]
        assert data["embeddings"].shape[0] == 1

    def test_build_averages_multiple_images(self, tmp_path):
        """Building should average embeddings for multiple images per person."""
        gallery_path = tmp_path / "gallery"
        person_path = gallery_path / "test_person"
        person_path.mkdir(parents=True)

        # Create 3 images
        (person_path / "img1.jpg").touch()
        (person_path / "img2.jpg").touch()
        (person_path / "img3.jpg").touch()

        cache_path = tmp_path / "cache.npz"

        gallery = FaceGallery(str(gallery_path), str(cache_path))

        # Mock embedder with different embeddings for each image
        embeddings = [
            np.array([1.0] + [0.0] * 511),
            np.array([0.5] + [0.5] + [0.0] * 510),
            np.array([0.0] + [1.0] + [0.0] * 510),
        ]

        mock_faces = [Mock(embedding=emb) for emb in embeddings]

        mock_embedder = Mock()
        mock_embedder.get.side_effect = [[face] for face in mock_faces]

        from unittest.mock import patch

        with patch("cv2.imread") as mock_imread:
            mock_imread.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

            num_enrolled = gallery.build(mock_embedder, force_rebuild=True)

        assert num_enrolled == 1

        # Load and verify average
        data = np.load(cache_path, allow_pickle=True)
        avg_embedding = data["embeddings"][0]

        # Average should be close to mean of input embeddings
        expected_avg = np.mean(embeddings, axis=0)
        np.testing.assert_allclose(avg_embedding, expected_avg, rtol=1e-5)


class TestGalleryHelpers:
    """Test gallery helper methods."""

    def test_get_person_ids(self, tmp_path):
        """Should return copy of person IDs."""
        cache_path = tmp_path / "test.npz"

        person_ids = np.array(["john", "jane", "bob"])
        embeddings = np.random.rand(3, 512).astype(np.float32)

        np.savez(cache_path, person_ids=person_ids, embeddings=embeddings)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))
        gallery.load()

        ids = gallery.get_person_ids()

        assert ids == ["john", "jane", "bob"]
        # Verify it's a copy
        ids.append("new")
        assert len(gallery.person_ids) == 3

    def test_size(self, tmp_path):
        """Should return gallery size."""
        cache_path = tmp_path / "test.npz"

        person_ids = np.array(["john", "jane"])
        embeddings = np.random.rand(2, 512).astype(np.float32)

        np.savez(cache_path, person_ids=person_ids, embeddings=embeddings)

        gallery = FaceGallery(str(tmp_path / "gallery"), str(cache_path))

        assert gallery.size() == 0  # Not loaded yet

        gallery.load()

        assert gallery.size() == 2
