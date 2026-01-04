#!/usr/bin/env python3
"""Download InsightFace models into a specified directory."""

from __future__ import annotations

import os
from pathlib import Path

from cam_vision.face.loader import FaceModels


def main() -> int:
    target = os.environ.get("SECUREVISION_INSIGHTFACE_DIR")
    if not target:
        raise RuntimeError("SECUREVISION_INSIGHTFACE_DIR is not set")

    target_path = Path(target)
    target_path.mkdir(parents=True, exist_ok=True)
    os.environ["INSIGHTFACE_HOME"] = str(target_path)

    FaceModels.get_models()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
