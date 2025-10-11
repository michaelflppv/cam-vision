# SecureVision (Lean Live CV: Trusted Faces + License Plates)

A modular, self-hosted pipeline to process live camera video and:
- Recognize **trusted faces** (no model training in-repo).
- Read **license plates** (ALPR) and match against lists.
- Expose events via API and a minimal dashboard.

**Constraints:** open-source + free tools; no (re)training included.
**Performance:** CPU-first design; optional GPU later.
**Modularity:** clean interfaces to swap detectors/recognizers.

## Roadmap (PRs)
1. Bootstrap (this PR)
2. Core config and interfaces
3. Multi-source capture (MacBook cam, USB, RTSP, HTTP(MJPEG), file)
4. Faces (InsightFace) + enrollment CLI
5. ALPR (OpenALPR community) + lists
6. Events + FastAPI + WebSocket
7. Streamlit UI
8. Tracking + multi-frame confirmation
9. Docker & Compose + E2E tests
10. Wi-Fi (same LAN) helpers: ONVIF discovery + RTSP builder

## Quickstart (after clone)
```bash
pipx install poetry           # or pip install --user poetry
poetry install
poetry run pre-commit install
pre-commit run --all-files
poetry run pytest -q
```

## Testing Video Capture (PR3)

The `securevision-capture` CLI tool lets you test video sources before integration:

### MacBook Camera Test
```bash
# Basic test (no preview)
poetry run securevision-capture --source-type device --device 0 --backend AVFOUNDATION --fps 15

# With live preview window
poetry run securevision-capture --source-type device --device 0 --backend AVFOUNDATION --fps 15 --preview

# With frame resize for faster processing
poetry run securevision-capture --source-type device --device 0 --fps 15 --resize 640x480 --preview
```

### RTSP Camera Test
```bash
poetry run securevision-capture \
  --source-type rtsp \
  --url rtsp://user:pass@192.168.1.100:554/stream \
  --fps 10 \
  --preview
```

### HTTP MJPEG Stream Test
```bash
poetry run securevision-capture \
  --source-type http_mjpeg \
  --url http://192.168.1.50:8080/video \
  --fps 10 \
  --resize 800x600 \
  --preview
```

### Video File Test
```bash
poetry run securevision-capture \
  --source-type file \
  --url /path/to/video.mp4 \
  --fps 30 \
  --duration 10 \
  --preview
```

### CLI Options
- `--source-type`: One of `device`, `rtsp`, `http_mjpeg`, `file` (required)
- `--device`: Device index for webcam/USB (default: 0)
- `--url`: URL or path for rtsp/http_mjpeg/file sources
- `--backend`: OpenCV backend (AVFOUNDATION, V4L2, DSHOW, etc.)
- `--fps`: Target FPS (default: 15)
- `--resize`: Resize frames to WIDTHxHEIGHT (e.g., 640x480)
- `--rotate-180`: Rotate frames 180 degrees
- `--preview`: Show live preview window
- `--duration`: Run for N seconds (default: run forever)
- `--verbose`: Verbose logging

**Note:** On macOS, grant camera permissions when prompted. The tool will display FPS statistics and frame counts during capture.

## Configuration

SecureVision uses environment variables for configuration. All settings use the prefix `SECUREVISION__` with double underscores for nesting.

### Video Source Configuration

#### MacBook / USB Camera (device)
```bash
export SECUREVISION__VIDEO__SOURCE__TYPE=device
export SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0        # 0=first camera, 1=second, etc.
export SECUREVISION__VIDEO__SOURCE__BACKEND=AVFOUNDATION  # Optional: macOS hint for OpenCV
export SECUREVISION__VIDEO__FPS_TARGET=15
```

#### RTSP Camera (network)
```bash
export SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
export SECUREVISION__VIDEO__SOURCE__URL=rtsp://user:pass@192.168.1.100:554/stream
export SECUREVISION__VIDEO__FPS_TARGET=15
export SECUREVISION__VIDEO__READ_TIMEOUT_S=5.0
export SECUREVISION__VIDEO__RECONNECT_INTERVAL_S=3.0
```

#### HTTP MJPEG Stream
```bash
export SECUREVISION__VIDEO__SOURCE__TYPE=http_mjpeg
export SECUREVISION__VIDEO__SOURCE__URL=http://192.168.1.100:8080/video
export SECUREVISION__VIDEO__FPS_TARGET=10
```

#### Video File (testing/development)
```bash
export SECUREVISION__VIDEO__SOURCE__TYPE=file
export SECUREVISION__VIDEO__SOURCE__URL=/path/to/video.mp4
export SECUREVISION__VIDEO__FPS_TARGET=30
```

### Video Processing Options

```bash
# Frame resizing (optional, speeds up processing)
export SECUREVISION__VIDEO__FRAME_RESIZE="640,480"  # width,height

# Camera rotation (for upside-down mounted cameras)
export SECUREVISION__VIDEO__ROTATE_180=true

# ONVIF discovery (future feature, PR10)
export SECUREVISION__VIDEO__ONVIF_DISCOVERY_ENABLED=false
```

### Face Recognition Settings

```bash
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__FACE__GALLERY_PATH=./data/faces/trusted
export SECUREVISION__FACE__GALLERY_CACHE=./data/faces/gallery.npz
export SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.35      # Lower = stricter matching
export SECUREVISION__FACE__MIN_FACE_SIZE=40               # Minimum face size in pixels
```

### License Plate (ALPR) Settings

```bash
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv
export SECUREVISION__PLATES__BLACKLIST_PATH=./data/plates/blacklist.csv
export SECUREVISION__PLATES__MIN_CONFIDENCE=0.55          # Minimum OCR confidence
```

### Event Storage & API

```bash
export SECUREVISION__EVENTS__DB_URL=sqlite:///./data/events.db
export SECUREVISION__EVENTS__RETENTION_DAYS=30

export SECUREVISION__API__HOST=0.0.0.0
export SECUREVISION__API__PORT=8000
export SECUREVISION__API__WS_ENABLED=true
export SECUREVISION__API__AUTH_TOKEN=your-secret-token    # Optional API authentication
```

### Example: Complete Configuration for Home Setup

```bash
# Video source: local USB camera
export SECUREVISION__VIDEO__SOURCE__TYPE=device
export SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0
export SECUREVISION__VIDEO__FPS_TARGET=15

# Face recognition: enabled with custom threshold
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.30

# Plates: disabled for indoor use
export SECUREVISION__PLATES__ENABLED=false

# API: local network only
export SECUREVISION__API__HOST=127.0.0.1
export SECUREVISION__API__PORT=8000
```

### Example: Complete Configuration for Driveway/Parking

```bash
# Video source: outdoor RTSP camera
export SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
export SECUREVISION__VIDEO__SOURCE__URL=rtsp://admin:password@192.168.1.50:554/stream
export SECUREVISION__VIDEO__FPS_TARGET=10

# Face recognition: disabled for vehicle-only monitoring
export SECUREVISION__FACE__ENABLED=false

# Plates: enabled with whitelist
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/family_cars.csv
export SECUREVISION__PLATES__MIN_CONFIDENCE=0.60

# API: accessible on local network
export SECUREVISION__API__HOST=0.0.0.0
export SECUREVISION__API__PORT=8000
export SECUREVISION__API__AUTH_TOKEN=secure-random-token
```

### Configuration Loading

The application loads configuration automatically from environment variables. You can also use a `.env` file (not committed to git):

```bash
# Create .env file
cat > .env << 'EOF'
SECUREVISION__VIDEO__SOURCE__TYPE=device
SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0
SECUREVISION__VIDEO__FPS_TARGET=15
EOF

# Load environment and run
set -a; source .env; set +a
poetry run python -m cam_vision.main  # (Coming in PR3)
```

**Note:** Configuration is validated on load. Invalid settings (e.g., missing URL for RTSP source) will raise clear error messages
