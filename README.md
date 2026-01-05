# SecureVision

SecureVision is a self-hosted computer vision platform for live camera feeds with a
cross-platform desktop dashboard. It detects faces and license plates, tracks events,
and exposes a local API for integrations.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-2b5b84)](https://www.python.org/)
[![Poetry](https://img.shields.io/badge/poetry-managed-60a5fa)](https://python-poetry.org/)
[![FastAPI](https://img.shields.io/badge/api-fastapi-009688)](https://fastapi.tiangolo.com/)
[![PySide6](https://img.shields.io/badge/ui-pyside6-4a90e2)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0b7285)](LICENSE)

## Highlights

- Live camera ingestion with a desktop UI for preview and monitoring
- Face recognition with InsightFace embeddings
- License plate detection with YOLOv8 and OCR via Tesseract
- Local event stream over REST and WebSocket
- Modular pipeline design for swapping components

## Requirements

- Python 3.10+
- Poetry
- Optional: Tesseract (required for OCR)
- Optional: a YOLOv8 plate model at `weights/yolov8n_plate.pt`

## Install

```bash
pipx install poetry
poetry install
```

## Desktop app

Load an environment template and start the Qt dashboard.

```bash
set -a; source examples/env/complete-home.env; set +a
poetry run securevision-qt
```

## Configuration

Settings are provided through environment variables prefixed with `SECUREVISION__`.
Example `.env` files are under `examples/env/`.

```bash
export SECUREVISION__VIDEO__FPS_TARGET=15
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__PLATES__ENABLED=false
```

## Data and assets

- `data/` holds local runtime assets such as enrolled faces and plate lists.
- `weights/` contains pretrained model weights.
- `examples/env/` includes environment templates for common setups.

## Project layout

```
cam_vision/
  api/          FastAPI services and WebSocket streaming
  cli/          CLI entrypoints
  config.py     Pydantic settings and defaults
  face/         Face recognition models and enrollment
  io/           Video capture and device adapters
  pipeline/     Orchestration, state, and triggers
  plates/       Plate detection and OCR
  qt_ui/        PySide6 desktop application
  tracking/     Multi-frame confirmation logic
  utils/        Shared helpers and utilities
  types.py      Core dataclasses and enums

data/           Local runtime assets (faces, plates)
examples/env/   Environment templates
tests/          Pytest suite mirroring cam_vision/
weights/        Pretrained model weights
```

## Development

```bash
poetry run pre-commit run --all-files
poetry run pytest -q
```

## Security and privacy

- Never commit real camera URLs or API tokens; use `examples/env/` templates instead.
- Keep sampled media anonymized and store it under `data/`.

## Contributing

See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` for guidelines.

## License

See `LICENSE`.
