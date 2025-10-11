"""Face recognition module using InsightFace (detection + embeddings)."""

from .gallery import FaceGallery
from .recognizer import FaceRecognizer

__all__ = ["FaceGallery", "FaceRecognizer"]
