# SecureVision (Lean Live CV: Trusted Faces + License Plates)

A modular, self-hosted pipeline to process live camera video and:
- Recognize **trusted faces** (no model training in-repo).
- Read **license plates** (ALPR) and match against lists.
- Expose events via API and a minimal dashboard.

**Constraints:** open-source + free tools; no (re)training included.
**Performance:** CPU-first design; optional GPU later.
**Modularity:** clean interfaces to swap detectors/recognizers.

## Roadmap (PRs)
1. ✅ Bootstrap
2. ✅ Core config and interfaces
3. ✅ Multi-source capture (MacBook cam, USB, RTSP, HTTP(MJPEG), file)
4. ✅ Faces (InsightFace) + enrollment CLI
5. ✅ ALPR (YOLOv8 + Tesseract) + lists
6. ✅ Events + FastAPI + WebSocket
7. ✅ Streamlit UI
8. ✅ Tracking + multi-frame confirmation
9. Docker & Compose + E2E tests
10. Wi-Fi (same LAN) helpers: ONVIF discovery + RTSP builder

## Quick Start

### Installation

```bash
# Install Poetry
pipx install poetry           # or pip install --user poetry

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest -q
```

### Testing Video Capture

Test video sources before integration using the `securevision-capture` CLI:

```bash
# MacBook camera
poetry run securevision-capture --source-type device --device 0 --backend AVFOUNDATION --fps 15 --preview

# RTSP camera
poetry run securevision-capture --source-type rtsp --url rtsp://user:pass@192.168.1.100:554/stream --fps 10 --preview

# HTTP MJPEG stream
poetry run securevision-capture --source-type http_mjpeg --url http://192.168.1.50:8080/video --fps 10 --preview

# Video file
poetry run securevision-capture --source-type file --url /path/to/video.mp4 --fps 30 --preview
```

**CLI Options:**
- `--source-type`: `device`, `rtsp`, `http_mjpeg`, or `file` (required)
- `--device`: Device index for webcam/USB (default: 0)
- `--url`: URL or path for rtsp/http_mjpeg/file sources
- `--backend`: OpenCV backend (AVFOUNDATION, V4L2, DSHOW, etc.)
- `--fps`: Target FPS (default: 15)
- `--resize`: Resize frames to WIDTHxHEIGHT (e.g., 640x480)
- `--rotate-180`: Rotate frames 180 degrees
- `--preview`: Show live preview window
- `--duration`: Run for N seconds (default: run forever)
- `--verbose`: Verbose logging

## Configuration

SecureVision uses environment variables for configuration. All settings use the prefix `SECUREVISION__` with double underscores for nesting.

### Configuration Files

Pre-configured environment variable examples are available in the `examples/env/` directory:

**Video Sources:**
- [`examples/env/video-device.env`](examples/env/video-device.env) - MacBook/USB camera
- [`examples/env/video-rtsp.env`](examples/env/video-rtsp.env) - RTSP network camera
- [`examples/env/video-http-mjpeg.env`](examples/env/video-http-mjpeg.env) - HTTP MJPEG stream
- [`examples/env/video-file.env`](examples/env/video-file.env) - Video file (testing)
- [`examples/env/video-processing.env`](examples/env/video-processing.env) - Frame processing options

**Features:**
- [`examples/env/face-recognition.env`](examples/env/face-recognition.env) - Face recognition settings
- [`examples/env/alpr-basic.env`](examples/env/alpr-basic.env) - Basic ALPR configuration
- [`examples/env/alpr-german.env`](examples/env/alpr-german.env) - German plate configuration example
- [`examples/env/alpr-roi.env`](examples/env/alpr-roi.env) - Region of Interest (ROI) settings
- [`examples/env/tracking.env`](examples/env/tracking.env) - Multi-frame tracking and confirmation
- [`examples/env/api.env`](examples/env/api.env) - Event storage and API server

**Complete Examples:**
- [`examples/env/complete-home.env`](examples/env/complete-home.env) - Home setup (USB camera, faces only)
- [`examples/env/complete-driveway.env`](examples/env/complete-driveway.env) - Driveway setup (RTSP, plates only)
- [`examples/env/complete-full-stack.env`](examples/env/complete-full-stack.env) - Full deployment (API server, both features)

### Using Configuration Files

```bash
# Load a configuration file
set -a; source examples/env/complete-home.env; set +a

# Or create your own .env file
cp examples/env/complete-home.env .env
# Edit .env as needed
set -a; source .env; set +a
```

### Configuration Overview

**Video Source Types:**
- `device`: MacBook/USB camera (requires device index, optional backend)
- `rtsp`: RTSP network camera (requires URL with credentials)
- `http_mjpeg`: HTTP MJPEG stream (requires URL)
- `file`: Video file for testing (requires file path)

**Key Settings:**
- `SECUREVISION__VIDEO__FPS_TARGET`: Target processing FPS (1-30)
- `SECUREVISION__FACE__SIMILARITY_THRESHOLD`: Face matching threshold (lower = stricter, default: 0.35)
- `SECUREVISION__PLATES__MIN_CONFIDENCE`: Plate detection confidence (default: 0.55)
- `SECUREVISION__TRACKING__FRAMES_REQUIRED`: Consecutive frames for confirmation (default: 3)
- `SECUREVISION__TRACKING__COOLDOWN_SECONDS`: Duplicate alert suppression (default: 30s)

**Tesseract Installation:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Additional languages
brew install tesseract-lang                                    # macOS
sudo apt-get install tesseract-ocr-deu tesseract-ocr-fra     # Ubuntu (German, French)
```

**YOLO Model:**
Download or train a YOLOv8 plate detection model and place it at `./weights/yolov8n_plate.pt`. Model won't be loaded unless plates feature is enabled.

## Face Recognition Setup

### Enrollment

Create a gallery directory with face images (one or more per person):

```bash
mkdir -p data/faces/trusted

# Add face images
# Filename format: person_name.jpg or person_name_001.jpg
cp /path/to/john_doe.jpg data/faces/trusted/
cp /path/to/jane_smith_01.jpg data/faces/trusted/
cp /path/to/jane_smith_02.jpg data/faces/trusted/

# Generate embeddings
poetry run securevision-face-enroll \
  --gallery data/faces/trusted \
  --output data/faces/gallery.npz
```

The enrollment process detects faces, generates 512-dimensional ArcFace embeddings, and saves them to a `.npz` cache for fast loading.

### Configuration

```bash
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__FACE__GALLERY_PATH=./data/faces/trusted
export SECUREVISION__FACE__GALLERY_CACHE=./data/faces/gallery.npz
```

See [`examples/env/face-recognition.env`](examples/env/face-recognition.env) for full settings.

## License Plate Recognition Setup

### Plate Lists

Create CSV files with authorized/blocked plates:

```bash
mkdir -p data/plates

# Whitelist (authorized plates)
cat > data/plates/whitelist.csv << 'EOF'
ABC123
XYZ789
MY-PLATE
EOF

# Blacklist (blocked plates)
cat > data/plates/blacklist.csv << 'EOF'
STOLEN1
BANNED2
EOF
```

### Configuration

```bash
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8n_plate.pt
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv
export SECUREVISION__PLATES__BLACKLIST_PATH=./data/plates/blacklist.csv
```

See [`examples/env/alpr-basic.env`](examples/env/alpr-basic.env) for full settings including OCR configuration.

**Regional Plate Format Examples:**
- US plates: `SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9]{6,7}"`
- EU plates: `SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,2}"`
- German plates: See [`examples/env/alpr-german.env`](examples/env/alpr-german.env)

## Tracking & Multi-Frame Confirmation

SecureVision uses tracking to dramatically reduce false positives. Events are only emitted after detections are confirmed across multiple consecutive frames.

**How It Works:**
1. **Track Creation:** Each detection creates a new track (TENTATIVE state)
2. **Track Matching:** New detections matched to existing tracks via IoU (bounding box overlap)
3. **Track Confirmation:** After K consecutive matches, track becomes CONFIRMED
4. **Event Emission:** Only CONFIRMED tracks emit events (with track_id)
5. **Temporal Filtering:** Duplicate events suppressed within cooldown period

**Configuration:**
```bash
export SECUREVISION__TRACKING__ENABLED=true
export SECUREVISION__TRACKING__FRAMES_REQUIRED=3          # K consecutive frames
export SECUREVISION__TRACKING__IOU_THRESHOLD=0.5          # Bbox overlap (0.0-1.0)
export SECUREVISION__TRACKING__COOLDOWN_SECONDS=30.0      # Deduplication window
```

See [`examples/env/tracking.env`](examples/env/tracking.env) for full settings and tuning guidelines.

**Expected Impact:**
- False positives: 80-90% reduction
- Duplicate alerts: 95%+ reduction (via cooldown)
- Latency: K frames × frame_time (e.g., 3 × 67ms = 200ms @ 15 FPS)

## API & Events

### Starting the API Server

```bash
# Basic usage
poetry run securevision-api

# Override host/port
poetry run securevision-api --host 0.0.0.0 --port 8080

# Development mode with auto-reload
poetry run securevision-api --reload --log-level DEBUG
```

### REST API Endpoints

#### Health Check
```bash
curl http://localhost:8000/
```

#### Query Events
```bash
# Get all events (max 100, most recent first)
curl http://localhost:8000/events

# Filter by type
curl http://localhost:8000/events?type=face_match
curl http://localhost:8000/events?type=plate_read

# Filter by timestamp (milliseconds)
curl http://localhost:8000/events?since=1700000000000

# Combine filters
curl http://localhost:8000/events?type=plate_read&since=1700000000000&limit=10
```

#### Get Event by ID
```bash
curl http://localhost:8000/faces/1
curl http://localhost:8000/plates/2
```

#### Cleanup Old Events
```bash
curl -X POST http://localhost:8000/cleanup
```

### WebSocket Streaming

Connect to `/stream` for real-time event notifications:

**JavaScript Client:**
```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onopen = () => {
  console.log('Connected to SecureVision event stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'face_match') {
    console.log(`Face: ${data.payload.person_id} (${data.payload.similarity})`);
  } else if (data.type === 'plate_read') {
    console.log(`Plate: ${data.payload.text_clean} (${data.payload.matched_list})`);
  }
};

// Keep-alive: send ping every 30 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000);
```

**Python Client:**
```python
import asyncio
import json
import websockets

async def stream_events():
    uri = "ws://localhost:8000/stream"
    async with websockets.connect(uri) as websocket:
        print("Connected to event stream")

        async for message in websocket:
            data = json.loads(message)
            print(f"Event {data['id']}: {data['type']}")
            print(f"Payload: {data['payload']}")

asyncio.run(stream_events())
```

### Authentication

Enable API authentication:

```bash
export SECUREVISION__API__AUTH_TOKEN=your-secret-token-here
```

Use with bearer token:

```bash
curl -H "Authorization: Bearer your-secret-token-here" http://localhost:8000/events
```

See [`examples/env/api.env`](examples/env/api.env) for full API configuration.

## Dashboard

SecureVision provides a Streamlit-based dashboard for live testing, source switching, and OCR tuning.

### Quick Start

```bash
# Start dashboard
poetry run securevision-ui

# Browser opens at localhost:8501
# 1. Select source (device/rtsp/http/file)
# 2. Configure connection (device index, URL, etc.)
# 3. Click "Connect"
# 4. View live preview + adjust settings in real-time
```

### Dashboard Modes

**Standalone Mode (Local Processing):**
- Captures frames directly from video sources
- Performs face recognition and plate detection locally
- Displays live preview at 5-10 FPS
- Real-time OCR tuning and source switching
- No API server required
- **Use case:** Testing, development, single-machine deployments

**Client Mode (API Consumption):**
- Connects to SecureVision API server
- Consumes events via REST and WebSocket
- Displays event history with filtering
- Shows API health metrics
- No local processing or video preview
- **Use case:** Remote monitoring, multi-client deployments

### Features

**Live Source Switching:**
- Switch between device → RTSP → file → HTTP without restart
- Auto-reconnect for network sources
- Dynamic FPS control (1-30 FPS slider)
- Frame resize options (640×480, 800×600, 1280×720)

**Real-Time OCR Tuning:**
- PSM mode selection (7=line, 6=block, 3=auto, etc.)
- Character whitelist customization
- Preprocessing pipeline (grayscale, bilateral, adaptive threshold, CLAHE)
- Image upscale factor (1x/2x/3x for small plates)
- Crop margin adjustment

**OCR Presets:**
- Fast (Grayscale Only) - Lowest overhead
- Balanced (Adaptive) - Recommended default
- High Quality (Full Pipeline) - Maximum accuracy
- Night/Low Light - CLAHE + adaptive threshold
- Save custom presets

**Tracking Controls:**
- Enable/disable tracking
- Adjust frames required (K)
- Configure IoU threshold
- Set max age and cooldown
- OCR agreement threshold (plates)

### Usage Examples

**Home Setup (MacBook Camera + Faces):**

```bash
# 1. Enroll faces
mkdir -p data/faces/trusted
cp ~/photos/john.jpg data/faces/trusted/john_doe.jpg
poetry run securevision-face-enroll --gallery data/faces/trusted --output data/faces/gallery.npz

# 2. Configure
source examples/env/complete-home.env

# 3. Start dashboard
poetry run securevision-ui

# 4. In browser (Standalone mode):
#    - Source: device, index 0, AVFOUNDATION backend
#    - Connect
#    - Adjust face similarity threshold in sidebar
```

**Driveway Setup (RTSP + Plates):**

```bash
# 1. Set up plate lists
mkdir -p data/plates
echo "ABC123" > data/plates/whitelist.csv

# 2. Configure
source examples/env/complete-driveway.env

# 3. Start dashboard
poetry run securevision-ui

# 4. In browser (Standalone mode):
#    - Source: rtsp, enter camera URL
#    - Connect
#    - Tune OCR for outdoor lighting in sidebar
```

**Remote Monitoring (API Client):**

```bash
# === On capture server ===
source examples/env/complete-full-stack.env
poetry run securevision-api

# === On monitoring client ===
poetry run securevision-ui

# In browser (Client mode):
#    - Mode: Client (API Server)
#    - API URL: http://192.168.1.100:8000
#    - Auth Token: (enter if configured)
#    - Fetch Events
```

### Tips & Troubleshooting

**Preview Lag:**
- Reduce FPS target
- Enable frame resize (640×480)
- Disable heavy preprocessing

**No Detections:**
- Verify model/gallery paths exist
- Check feature status indicators (🟢/🔴)
- Lower confidence thresholds

**Low OCR Confidence:**
- Try different PSM modes
- Enable adaptive threshold for uneven lighting
- Increase upscale factor for small plates

**Connection Fails:**
- MacBook: Grant camera permissions in System Preferences
- RTSP: Test URL with VLC first
- File: Use absolute paths

## Development

### Project Structure

```
cam_vision/
├── api/              # FastAPI server + WebSocket
├── cli/              # Command-line tools
├── config.py         # Pydantic configuration
├── events/           # Event storage (SQLite)
├── face/             # Face recognition (InsightFace)
├── io/               # Video capture (OpenCV)
├── pipeline/         # Processing pipeline + tracking
├── plates/           # ALPR (YOLOv8 + Tesseract)
├── tracking/         # IoU tracking + multi-frame confirmation
├── types.py          # Core dataclasses
└── ui/               # Streamlit dashboard

tests/
├── tracking/         # Tracking tests
├── ui/               # UI component tests
└── ...               # Feature tests

examples/
└── env/              # Configuration examples
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run quietly (less verbose)
poetry run pytest -q

# Run specific test file
poetry run pytest tests/test_config.py

# Run with verbose output
poetry run pytest -v
```

### Code Style

```bash
# Run pre-commit on all files (includes ruff, black, isort)
pre-commit run --all-files

# Run individual tools
poetry run ruff check .
poetry run ruff check --fix .
poetry run black .
poetry run isort .
```

**Style Guidelines:**
- Line length: 100 characters
- Target Python: 3.10+
- Formatter: black
- Import sorting: isort (black profile)
- Linter: ruff

### Adding Features

1. **Implement Processor:** Create a new `Processor` subclass in appropriate module
2. **Add Configuration:** Extend `config.py` with Pydantic settings
3. **Add Tests:** Create test file in `tests/`
4. **Update Documentation:** Add section to README and create example config
5. **Integration:** Wire into pipeline/dashboard as needed

Example: Adding a new vehicle detector

```python
# cam_vision/vehicles/detector.py
from cam_vision.pipeline.base import Processor
from cam_vision.types import Event, Detection

class VehicleDetector(Processor):
    def open(self) -> None:
        # Load model
        pass

    def process_frame(self, frame) -> list[Event]:
        # Detect vehicles
        # Return events
        pass

    def close(self) -> None:
        # Cleanup
        pass
```

### Architecture Principles

**From CLAUDE.md:**
- **Stateless Processors:** Processing logic should be stateless; state lives in wrappers (tracking, deduplication)
- **Decorator Pattern:** Use wrappers for cross-cutting concerns (confirmation, temporal filtering)
- **Type Safety:** Extensive use of dataclasses and Pydantic models
- **Resource Management:** Explicit open/close lifecycle for all components
- **Modularity:** Clean interfaces allow swapping implementations without changing pipeline

## Next Steps

**Upcoming Features (PR9+):**
- Docker & Compose deployment
- E2E tests with sample video
- ONVIF camera discovery
- RTSP URL builder for common camera brands
- Multi-camera support

**Optional Enhancements:**
- Event analytics dashboard
- Webhook notifications
- Email alerts
- Push notifications

## License

This project uses open-source dependencies. See individual packages for license details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run pre-commit hooks
5. Submit a pull request

All contributions must maintain:
- Passing tests (294/294)
- Zero linting errors
- Type hints where applicable
- Updated documentation
