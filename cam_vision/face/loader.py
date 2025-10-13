"""Lazy loading of InsightFace models (RetinaFace detector + ArcFace embedder)."""

from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from insightface.app import FaceAnalysis


def _ensure_numpy_lstsq_future_default() -> None:
    """Patch numpy.linalg.lstsq to use rcond=None when omitted."""
    try:
        import numpy as np
    except ImportError:
        return

    current = np.linalg.lstsq
    if getattr(current, "_sv_default_rcond", False):
        return

    @wraps(current)
    def _patched_lstsq(a, b, *args, **kwargs):
        if not args and "rcond" not in kwargs:
            kwargs["rcond"] = None
        return current(a, b, *args, **kwargs)

    _patched_lstsq._sv_default_rcond = True  # type: ignore[attr-defined]
    np.linalg.lstsq = _patched_lstsq


class FaceModels:
    """
    Singleton-style lazy loader for InsightFace models.

    InsightFace's FaceAnalysis includes both:
    - RetinaFace: Face detection
    - ArcFace: Face embedding (512-dim vectors)

    Models are downloaded automatically on first use to ~/.insightface/models/
    """

    _models: Optional["FaceAnalysis"] = None  # type: ignore

    @classmethod
    def get_models(cls, det_size: tuple[int, int] = (640, 640)):
        """
        Get InsightFace FaceAnalysis instance (lazy load).

        Args:
            det_size: Detection input size (width, height). Larger = more accurate but slower.
                      Default (640, 640) is good balance for CPU.

        Returns:
            FaceAnalysis instance ready for detection + embedding
        """
        if cls._models is None:
            logger.info("Loading InsightFace models (first use, may download ~100MB)...")

            try:
                _ensure_numpy_lstsq_future_default()
                from insightface.app import FaceAnalysis

                # Initialize with CPU provider
                app = FaceAnalysis(
                    name="buffalo_l",  # Model name (accurate, balanced)
                    providers=["CPUExecutionProvider"],  # CPU-only for now
                )

                # Prepare models
                app.prepare(ctx_id=0, det_size=det_size)

                cls._models = app

                logger.info(
                    f"InsightFace models loaded successfully "
                    f"(det_size={det_size}, provider=CPU)"
                )

            except Exception as e:
                logger.error(f"Failed to load InsightFace models: {e}")
                raise

        return cls._models

    @classmethod
    def clear_cache(cls):
        """Clear cached models (useful for testing)."""
        cls._models = None
        logger.debug("Cleared InsightFace model cache")
