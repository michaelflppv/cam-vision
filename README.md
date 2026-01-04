# SecureVision

SecureVision is a modular, self-hosted computer vision pipeline for live camera feeds.
It can recognize known faces and read license plates, then publish events through a
FastAPI server and a desktop dashboard.

## Highlights

- Face recognition via InsightFace embeddings (no training in this repo)
- License plate detection with YOLOv8 + OCR with Tesseract
- Multiple sources: device, RTSP, HTTP MJPEG, or video file
- Event output via REST + WebSocket and a Qt desktop UI
- CPU-first design with clean interfaces to swap components later

## Requirements

- Python 3.10+
- Poetry
- Optional: Tesseract (needed for OCR)
- Optional: a YOLOv8 plate model at `weights/yolov8n_plate.pt`

## Install

```bash
pipx install poetry
poetry install
```

This installs project dependencies into Poetry's virtual environment.

## Quick start (local preview)

1. Load an example configuration.
2. Start a preview window to confirm the camera works.

```bash
set -a; source examples/env/complete-home.env; set +a
poetry run securevision-preview --source-type device --device 0 --backend AVFOUNDATION
```

If you are not on macOS, use a different backend or source type.

## Test a video source

Use `securevision-capture` to validate a stream before wiring up the full pipeline.

```bash
# Local webcam
poetry run securevision-capture --source-type device --device 0 --preview

# RTSP camera
poetry run securevision-capture --source-type rtsp --url rtsp://USER:PASS@IP:554/stream --preview

# HTTP MJPEG
poetry run securevision-capture --source-type http_mjpeg --url http://IP:PORT/video --preview

# Video file
poetry run securevision-capture --source-type file --url /path/to/video.mp4 --preview
```

## Configuration basics

Settings are provided through environment variables prefixed with `SECUREVISION__`.
Example `.env` files live under `examples/env/`.

```bash
export SECUREVISION__VIDEO__FPS_TARGET=15
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__PLATES__ENABLED=false
```

To load an example file:

```bash
set -a; source examples/env/complete-driveway.env; set +a
```

## Face recognition setup

1. Place images for each person under `data/faces/trusted/`.
2. Run the enrollment command to build the embedding cache.

```bash
mkdir -p data/faces/trusted
cp /path/to/jane.jpg data/faces/trusted/jane_doe.jpg
poetry run securevision-face-enroll --gallery data/faces/trusted --output data/faces/gallery.npz
```

Enable face recognition:

```bash
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__FACE__GALLERY_PATH=./data/faces/trusted
export SECUREVISION__FACE__GALLERY_CACHE=./data/faces/gallery.npz
```

## License plate recognition setup

1. Put your plate lists under `data/plates/`.
2. Point the config to your YOLOv8 weights file.

```bash
mkdir -p data/plates
printf "ABC123\nXYZ789\n" > data/plates/whitelist.csv

export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8n_plate.pt
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv
```

## API server

```bash
poetry run securevision-api
```

- Health check: `http://localhost:8000/`
- Events: `http://localhost:8000/events`
- WebSocket: `ws://localhost:8000/stream`

## Desktop UI (Qt)

```bash
poetry run securevision-qt
```

Use the sidebar to choose a source, then click Connect to start live preview.

## Project layout

```
cam_vision/
  api/          FastAPI server and WebSocket
  cli/          Command-line tools
  config.py     Pydantic settings
  face/         Face recognition (InsightFace)
  io/           Video capture (OpenCV)
  pipeline/     Orchestration and tracking
  plates/       Plate detection + OCR
  qt_ui/        PySide6 desktop UI
  tracking/     Multi-frame confirmation
  utils/        Shared helpers
  types.py      Core dataclasses and enums

tests/          Pytest suite mirroring cam_vision/
examples/env/   Environment templates
weights/        Pretrained model weights
```

## Development

```bash
poetry run pre-commit run --all-files
poetry run pytest -q
```

## Security and privacy

- Never commit real camera URLs or API tokens; use `examples/env/` templates instead.
- Media and lists stay in `data/` and are intended to be local and private.

## Contributing

See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md` for guidelines.

## License

See `LICENSE`.
