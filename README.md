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
poetry run securevision-capture --source-type device --device 1 --backend AVFOUNDATION --fps 15

# With live preview window
poetry run securevision-capture --source-type device --device 1 --backend AVFOUNDATION --fps 15 --preview

# With frame resize for faster processing
poetry run securevision-capture --source-type device --device 1 --fps 15 --resize 640x480 --preview
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

SecureVision uses YOLOv8 for plate detection and Tesseract for OCR. Configuration is organized into detector, OCR, post-processing, and ROI settings.

#### Basic Settings

```bash
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv
export SECUREVISION__PLATES__BLACKLIST_PATH=./data/plates/blacklist.csv
export SECUREVISION__PLATES__MIN_CONFIDENCE=0.55          # Overall event confidence threshold
```

#### YOLOv8 Detector Settings

```bash
# Model path (download a pre-trained YOLOv8 plate model)
export SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8n_plate.pt

# Detection thresholds
export SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.25    # Detection confidence (0.0-1.0)
export SECUREVISION__PLATES__DETECTOR__IOU_THRESHOLD=0.45     # NMS IoU threshold (0.0-1.0)
export SECUREVISION__PLATES__DETECTOR__MAX_DET=10            # Max detections per frame
export SECUREVISION__PLATES__DETECTOR__INPUT_SIZE=640        # Model input size (square)
```

**Note:** Model weights are not included. Download or train a YOLOv8 plate detection model and place it at the configured path. The model won't be loaded until the plates feature is used, so missing weights with `PLATES__ENABLED=false` won't cause errors.

#### Tesseract OCR Settings

```bash
# Language support (install additional Tesseract language packs as needed)
export SECUREVISION__PLATES__OCR__TESSERACT_LANG=eng         # eng, deu, fra, spa, etc.

# OCR engine configuration
export SECUREVISION__PLATES__OCR__PSM_MODE=7                 # Page segmentation mode (7=line, 8=word)
export SECUREVISION__PLATES__OCR__OEM_MODE=3                 # OCR engine mode (3=default, 1=LSTM)
export SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "

# Preprocessing pipeline (optional, for challenging conditions)
export SECUREVISION__PLATES__OCR__ENABLE_GRAYSCALE=true      # Recommended: always on
export SECUREVISION__PLATES__OCR__ENABLE_BILATERAL=false     # Noise reduction (adds overhead)
export SECUREVISION__PLATES__OCR__ENABLE_ADAPTIVE_THRESHOLD=false  # Uneven lighting
export SECUREVISION__PLATES__OCR__ENABLE_CLAHE=false         # Contrast enhancement (minimal benefit)

# Post-processing
export SECUREVISION__PLATES__OCR__TO_UPPERCASE=true
export SECUREVISION__PLATES__OCR__STRIP_WHITESPACE=true
export SECUREVISION__PLATES__OCR__MIN_TEXT_LENGTH=3
export SECUREVISION__PLATES__OCR__SUBSTITUTE_O_TO_0=false    # Replace letter O with digit 0
export SECUREVISION__PLATES__OCR__SUBSTITUTE_I_TO_1=false    # Replace letter I with digit 1
```

**Tesseract Installation:**
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# For additional languages
brew install tesseract-lang     # macOS
sudo apt-get install tesseract-ocr-deu tesseract-ocr-fra  # Ubuntu (German, French)
```

#### Post-Processing & Validation

```bash
# Regex validation for plate format
export SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9-]{4,10}"  # Customize per region
export SECUREVISION__PLATES__POSTPROCESS__UPPERCASE=true
export SECUREVISION__PLATES__POSTPROCESS__MIN_LENGTH=4
export SECUREVISION__PLATES__POSTPROCESS__MAX_LENGTH=10
```

**Examples by Region:**
- US plates: `"[A-Z0-9]{6,7}"`
- EU plates: `"[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,2}"`
- Custom format: Adjust regex to match your region's plate format

#### Region of Interest (ROI) - Optional

Speed up detection by cropping to a specific region before processing:

```bash
# Enable ROI crop
export SECUREVISION__PLATES__ROI__ENABLED=true
export SECUREVISION__PLATES__ROI__X1=100        # Top-left x coordinate
export SECUREVISION__PLATES__ROI__Y1=200        # Top-left y coordinate
export SECUREVISION__PLATES__ROI__X2=800        # Bottom-right x (0=full width)
export SECUREVISION__PLATES__ROI__Y2=600        # Bottom-right y (0=full height)
```

**ROI Use Cases:**
- Fixed camera angle: Crop to driveway entrance area
- Gate camera: Focus on vehicle height zone only
- Performance: Reduce processing area by 50-75% for faster detection

#### Complete ALPR Example (German Plates)

```bash
# Detector
export SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8s_plate_eu.pt
export SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.30

# OCR for German plates
export SECUREVISION__PLATES__OCR__TESSERACT_LANG=deu
export SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789- "
export SECUREVISION__PLATES__OCR__ENABLE_BILATERAL=true      # Better for outdoor conditions

# German plate format: 1-3 letters + 1-4 digits + 0-2 letters (e.g., "B MW 1234")
export SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-ZÄÖÜ]{1,3}[A-ZÄÖÜ]{1,3}[0-9]{1,4}[A-ZÄÖÜ]{0,2}"

# Lists
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/family_cars.csv
export SECUREVISION__PLATES__BLACKLIST_PATH=./data/plates/blocked.csv
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

## API & Events (PR6)

SecureVision provides a REST API and WebSocket interface for accessing event data. Events are automatically persisted to SQLite and can be queried or streamed in real-time.

### Starting the API Server

```bash
# Basic usage (uses config from environment)
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

Response:
```json
{
  "service": "SecureVision Events API",
  "version": "0.1.0",
  "ws_enabled": true,
  "auth_enabled": false
}
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

# Limit results
curl http://localhost:8000/events?limit=50

# Combine filters
curl http://localhost:8000/events?type=plate_read&since=1700000000000&limit=10
```

Response format:
```json
[
  {
    "id": 1,
    "type": "face_match",
    "ts_ms": 1700000000000,
    "frame_source_id": "camera_1",
    "created_at": "2024-11-15T12:00:00",
    "payload": {
      "person_id": "john_doe",
      "similarity": 0.87,
      "bbox": {"x1": 100, "y1": 150, "x2": 300, "y2": 350},
      "detection_score": 0.95,
      "track_id": 42,
      "detector_metadata": {
        "model_name": "insightface",
        "detector": "retinaface",
        "recognition": "arcface"
      }
    }
  }
]
```

#### Get Face Match by ID
```bash
curl http://localhost:8000/faces/1
```

Response includes `person_id`, `similarity`, `bbox`, `detection_score`, and `detector_metadata`.

#### Get Plate Read by ID
```bash
curl http://localhost:8000/plates/2
```

Response includes OCR fields:
```json
{
  "id": 2,
  "type": "plate_read",
  "ts_ms": 1700000001000,
  "frame_source_id": "camera_1",
  "created_at": "2024-11-15T12:00:01",
  "payload": {
    "text_raw": " ABC 123 ",
    "text_clean": "ABC123",
    "ocr_confidence": 85.5,
    "detector_score": 0.88,
    "matched_list": "whitelist",
    "preprocessing_used": "grayscale,bilateral",
    "bbox": {"x1": 200, "y1": 400, "x2": 500, "y2": 500},
    "track_id": null,
    "detector_metadata": {
      "model_name": "yolov8",
      "detector": "yolov8",
      "ocr_engine": "tesseract",
      "preprocessing": "grayscale,bilateral"
    }
  }
}
```

**OCR Fields Explained:**
- `text_raw`: Original OCR output before cleaning
- `text_clean`: Processed text (uppercase, whitespace removed, substitutions applied)
- `ocr_confidence`: Tesseract confidence score (0-100)
- `detector_score`: YOLOv8 detection confidence (0.0-1.0)
- `matched_list`: "whitelist", "blacklist", or null

#### Cleanup Old Events
```bash
# Manually trigger retention cleanup
curl -X POST http://localhost:8000/cleanup
```

Response:
```json
{
  "deleted": 15,
  "retention_days": 30
}
```

### WebSocket Streaming

Connect to `/stream` to receive real-time event notifications:

**JavaScript Client:**
```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onopen = () => {
  console.log('Connected to SecureVision event stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'face_match') {
    console.log(`Face matched: ${data.payload.person_id} (${data.payload.similarity})`);
  } else if (data.type === 'plate_read') {
    console.log(`Plate read: ${data.payload.text_clean} (list: ${data.payload.matched_list})`);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
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

            if data.get('type') == 'pong':
                continue  # Keep-alive response

            print(f"Event {data['id']}: {data['type']}")
            print(f"Payload: {data['payload']}")

asyncio.run(stream_events())
```

### Authentication

Enable API authentication by setting a bearer token:

```bash
export SECUREVISION__API__AUTH_TOKEN=your-secret-token-here
```

All endpoints except `/` (health check) and `/stream` (WebSocket) require authentication:

```bash
# Without auth (401 Unauthorized)
curl http://localhost:8000/events

# With auth (200 OK)
curl -H "Authorization: Bearer your-secret-token-here" http://localhost:8000/events
```

**Note:** WebSocket does not currently require authentication. This can be added in future updates if needed.

### Event Schema for Analytics

The database schema is optimized for basic analytics queries:

**Time-Series Analysis:**
- `ts_ms` (event timestamp) and `created_at` (DB insertion time) are indexed
- Query events by time range for trend analysis

**Performance Tracking:**
- `detector_score` (YOLO/RetinaFace confidence) vs `ocr_confidence` (Tesseract)
- Separate scores allow quality analysis per stage

**Pipeline Optimization:**
- `preprocessing_used` field shows which OCR preprocessing was applied
- Compare `ocr_confidence` across different preprocessing combinations
- Identify optimal settings for your camera/lighting conditions

**List Effectiveness:**
- `matched_list` field (whitelist/blacklist/null) for hit rate analysis
- Query: "How many blacklist matches in past 24 hours?"
- Query: "What percentage of plates matched whitelist?"

**Detector Comparison (Future):**
- `detector_metadata` JSON field allows A/B testing different models
- Example: Compare YOLOv8n vs YOLOv8s detection rates
- Store model name/version for reproducible results

**Example Analytics Queries:**

```python
# Python example using SQLModel
from sqlmodel import Session, select
from cam_vision.events.store import EventStore, PlateReadRecord

store = EventStore("sqlite:///./data/events.db")

with Session(store.engine) as session:
    # Average OCR confidence by preprocessing method
    stmt = select(PlateReadRecord.preprocessing_used,
                  PlateReadRecord.ocr_confidence)
    results = session.exec(stmt).all()

    # Group by preprocessing
    by_method = {}
    for method, conf in results:
        if method not in by_method:
            by_method[method] = []
        by_method[method].append(conf)

    for method, confs in by_method.items():
        avg = sum(confs) / len(confs)
        print(f"{method}: avg confidence = {avg:.1f}%")
```

### Integration with Pipeline

Events are automatically persisted by adding `EventStoreSink` to your pipeline:

```python
from cam_vision.pipeline.graph import GraphRunner
from cam_vision.events import EventStore, EventStoreSink
from cam_vision.api.app import get_ws_manager

# Create store
store = EventStore(db_url="sqlite:///./data/events.db")

# Create sink (with optional WebSocket broadcasting)
ws_manager = get_ws_manager()  # If API server is running
sink = EventStoreSink(store, ws_manager)

# Add to pipeline
runner = GraphRunner(
    source=video_source,
    processors=[face_recognizer, plate_recognizer],
    sinks=[sink]  # Events auto-saved and broadcast
)

runner.open()
while runner.run_once():
    pass
runner.close()
```

**Note:** Full pipeline integration examples will be provided in PR7 (dashboard) and PR9 (Docker deployment).

## Dashboard (PR7)

SecureVision provides a Streamlit-based dashboard for live testing, source switching, and OCR tuning without code edits.

### Quick Start (MacBook Camera Test)

```bash
# Start dashboard
poetry run securevision-ui

# Browser auto-opens at localhost:8501
# 1. Select "device" source
# 2. Device index: 0
# 3. Backend: AVFOUNDATION (prefilled on macOS)
# 4. Click "Connect"
# 5. View live preview + adjust OCR settings in real-time
```

### Features

**Live Source Switching:**
- Switch between MacBook cam → RTSP → file → HTTP MJPEG without app restart
- Auto-reconnect for network sources (RTSP/HTTP)
- Preview remains responsive at 2-5 FPS (non-blocking UI)
- Dynamic FPS control (1-30 FPS slider)
- Frame resize options (640×480, 800×600, 1280×720)

**Real-Time OCR Tuning:**
- **PSM Mode**: Choose page segmentation (7=line, 6=block, 3=auto, 11=sparse, 13=raw)
- **Character Whitelist**: Customize allowed characters for your region
- **Preprocessing Pipeline**:
  - Grayscale (recommended, always on)
  - Bilateral filter (noise reduction, adds overhead)
  - Adaptive threshold (uneven lighting conditions)
  - CLAHE (minimal benefit per research, disabled by default)
- **Advanced Controls**:
  - Crop margin (0-20px padding around plate)
  - Image upscale factor (1x/2x/3x for small/distant plates)
  - Min text length threshold
  - Character substitutions (O→0, I→1)

**OCR Presets:**
- Built-in presets for common scenarios:
  - **Fast (Grayscale Only)**: Lowest overhead, good for clear plates
  - **Balanced (Adaptive)**: Recommended for most use cases
  - **High Quality (Full Pipeline)**: Maximum accuracy with bilateral + adaptive
  - **Night/Low Light**: CLAHE + adaptive threshold for dark conditions
- Save custom presets for your specific camera/lighting setup

**Plate Detection Panel:**
- View last 5 detected plates with cropped images
- OCR results: raw vs cleaned text side-by-side
- Confidence metrics: OCR confidence + detector score with progress bars
- Whitelist/blacklist match indicators (✓/✗/○)
- Preprocessing used for each detection (debugging aid)

### Usage Examples

**Test Different Video Sources:**

```bash
# MacBook camera
poetry run securevision-ui
# → Select "device", index 0, AVFOUNDATION backend

# RTSP camera
poetry run securevision-ui
# → Select "rtsp", enter rtsp://user:pass@192.168.1.100:554/stream

# Video file (testing)
poetry run securevision-ui
# → Select "file", enter /path/to/sample_video.mp4

# HTTP MJPEG stream
poetry run securevision-ui
# → Select "http_mjpeg", enter http://192.168.1.50:8080/video
```

**Tune OCR for Outdoor Conditions:**

1. Connect to camera
2. Expand "OCR Tuning" in sidebar
3. Select "Balanced (Adaptive)" preset
4. If plates are small/distant, set upscale factor to 2x or 3x
5. If lighting is uneven, enable bilateral filter
6. Watch OCR confidence change in real-time
7. Save as custom preset (e.g., "Outdoor Day")

**Compare Preprocessing Methods:**

1. Process same frame with different settings
2. Note OCR confidence and text_clean results
3. Preprocessing used shown under each detection
4. Iterate to find optimal settings for your camera

### Architecture

The dashboard uses minimal dependencies and Streamlit's built-in state management:

- **State Management**: Streamlit `session_state` (no Redux/Vuex)
- **Background Capture**: Single thread with `queue.Queue` (no asyncio overhead)
- **UI Updates**: Non-blocking via `st.empty()` placeholders at 2-5 FPS
- **Dynamic Reconfiguration**: Stop old capture → create new with updated params → restart

This architecture ensures responsive UI even with slow OCR processing.

### Tips & Troubleshooting

**Preview Lag:**
- Reduce FPS target (sidebar slider)
- Enable frame resize (640×480 for faster processing)
- Disable heavy preprocessing (bilateral filter, CLAHE)

**No Plates Detected:**
- Check source is actually showing vehicles
- Verify YOLO model path (weights/yolov8n_plate.pt)
- Lower detector confidence threshold (config)

**Low OCR Confidence:**
- Try different PSM modes (7 for single line, 6 for block)
- Enable adaptive threshold for uneven lighting
- Increase upscale factor (2x or 3x) for small plates
- Adjust character whitelist to match your region

**Connection Fails:**
- MacBook camera: Grant permissions in System Preferences
- RTSP: Test URL with VLC first
- File: Check path is absolute and file exists

### Configuration vs Dashboard

Dashboard settings are session-only (not persisted to env). For production deployments:

1. Use dashboard to find optimal OCR settings
2. Note preprocessing pipeline that works best
3. Set corresponding environment variables:
   ```bash
   export SECUREVISION__PLATES__OCR__ENABLE_GRAYSCALE=true
   export SECUREVISION__PLATES__OCR__ENABLE_ADAPTIVE_THRESHOLD=true
   export SECUREVISION__PLATES__OCR__PSM_MODE=7
   ```
4. Run production pipeline with `EventStoreSink` instead of UI

## Dashboard Modes: Standalone vs Client

The SecureVision dashboard supports two operational modes to accommodate different deployment scenarios.

### Mode Overview

**Standalone Mode (Local Processing):**
- Captures frames directly from video sources (device/RTSP/HTTP/file)
- Performs face recognition and plate detection locally
- Displays live preview at 2-5 FPS
- Real-time OCR tuning and source switching
- No API server required
- **Use case:** Testing, development, single-machine deployments

**Client Mode (API Consumption):**
- Connects to SecureVision API server
- Consumes events via REST and WebSocket
- Displays event history with filtering
- Shows API health metrics and event rates
- No local processing or video preview
- **Use case:** Remote monitoring, multi-client deployments, production dashboards

### Standalone Mode Setup

#### Prerequisites

1. **Install Dependencies:**
   ```bash
   poetry install
   ```

2. **Face Recognition (Optional):**

   Create a gallery directory and add face images:
   ```bash
   mkdir -p data/faces/trusted

   # Add face images (one or more per person)
   # Filename format: person_name.jpg or person_name_001.jpg
   cp /path/to/john_doe.jpg data/faces/trusted/
   cp /path/to/jane_smith_01.jpg data/faces/trusted/
   cp /path/to/jane_smith_02.jpg data/faces/trusted/
   ```

   Enroll faces to generate embeddings:
   ```bash
   poetry run securevision-face-enroll \
     --gallery data/faces/trusted \
     --output data/faces/gallery.npz
   ```

   The enrollment process:
   - Detects faces in each image
   - Generates 512-dimensional embeddings (ArcFace)
   - Saves embeddings to `.npz` cache for fast loading
   - Supports multiple images per person for better accuracy

3. **License Plate Detection (Optional):**

   Download a pre-trained YOLOv8 plate detection model:
   ```bash
   mkdir -p weights

   # Option 1: Use pre-trained model from Ultralytics (if available)
   # Option 2: Train your own with YOLOv8
   # Option 3: Download from community sources

   # Place model at:
   # weights/yolov8n_plate.pt
   ```

   Create whitelist/blacklist CSV files (optional):
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

4. **Configure Environment:**

   Create a `.env` file or export variables:
   ```bash
   # Face recognition (if enabled)
   export SECUREVISION__FACE__ENABLED=true
   export SECUREVISION__FACE__GALLERY_PATH=./data/faces/trusted
   export SECUREVISION__FACE__GALLERY_CACHE=./data/faces/gallery.npz
   export SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.35

   # Plate detection (if enabled)
   export SECUREVISION__PLATES__ENABLED=true
   export SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8n_plate.pt
   export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv
   export SECUREVISION__PLATES__BLACKLIST_PATH=./data/plates/blacklist.csv
   ```

#### Running Standalone Mode

1. **Start Dashboard:**
   ```bash
   poetry run securevision-ui
   ```

   Browser opens at `http://localhost:8501`

2. **Configure Source:**
   - Mode: Select **"Standalone"** (default)
   - Source Type: Choose device/RTSP/HTTP/file
   - Device Index: 0 for MacBook camera
   - Backend: AVFOUNDATION (auto-filled on macOS)
   - FPS Target: 15 (adjustable 1-30)
   - Frame Resize: Optional (640×480, 800×600, 1280×720)

3. **Connect and Monitor:**
   - Click **"Connect"** to start capture
   - View live preview with overlays (face boxes, plate boxes)
   - See real-time detection results in panels below
   - Adjust OCR settings in sidebar (changes apply immediately)

4. **Face Matches Panel:**
   - Shows detected and matched faces
   - Person ID from gallery
   - Similarity score (0.0-1.0)
   - Confidence badge (🟢 high, 🟡 medium, 🔴 low)
   - Cropped face thumbnail

5. **Plate Detections Panel:**
   - Shows detected plates
   - Raw OCR text vs cleaned text
   - OCR confidence (Tesseract score)
   - Detector confidence (YOLO score)
   - List match indicator (✅ whitelist, 🚫 blacklist, ○ unknown)
   - Preprocessing methods used

### Client Mode Setup

#### Prerequisites

1. **Running API Server:**

   The API server must be running and accessible. See "Running the Full Stack" below.

2. **API URL:**

   Note the API server URL (e.g., `http://localhost:8000` or `http://192.168.1.100:8000`)

3. **Authentication (Optional):**

   If API server has authentication enabled, obtain the bearer token.

#### Running Client Mode

1. **Start Dashboard:**
   ```bash
   poetry run securevision-ui
   ```

2. **Configure Client:**
   - Mode: Select **"Client (API Server)"**
   - API URL: Enter server URL (e.g., `http://localhost:8000`)
   - Auth Token: Enter bearer token if required (optional)

3. **Monitor API Health:**
   - Status indicator (🟢 Online / 🔴 Offline)
   - WebSocket client count
   - Recent events (last 5 minutes)
   - Event rate (events/second)

4. **Fetch Events:**
   - Time Range: All time / Last 5/15/60 minutes
   - Event Type: Both / Face Matches Only / Plate Reads Only
   - Click **"🔄 Fetch Events"** to retrieve from API
   - Events display in expandable panels with full details

5. **Event History Panels:**

   **Face Match History:**
   - Person ID and similarity score
   - Event timestamp (relative time)
   - Detection metrics
   - Expandable for full details

   **Plate Read History:**
   - Clean plate text
   - List match badge
   - OCR + detector confidence
   - Preprocessing used
   - Expandable for full details

6. **Auto-Refresh (Optional):**
   - Enable "Auto-refresh (every 5s)" checkbox
   - Dashboard automatically fetches new events

### Running the Full Stack

For production or multi-client deployments, run both API server and dashboard(s):

#### Terminal 1: API Server

```bash
# Set up environment
export SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
export SECUREVISION__VIDEO__SOURCE__URL=rtsp://user:pass@192.168.1.100:554/stream
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__API__HOST=0.0.0.0
export SECUREVISION__API__PORT=8000

# Start API server
poetry run securevision-api
```

The API server will:
- Start event database (SQLite)
- Initialize WebSocket manager
- Expose REST endpoints at `http://localhost:8000`
- Accept WebSocket connections at `ws://localhost:8000/stream`

#### Terminal 2: Processing Pipeline (Future PR)

```bash
# Run processing pipeline to generate events
# This will capture video, process frames, and send events to API
# (Full pipeline integration coming in future PRs)
```

#### Terminal 3+: Dashboard Client(s)

```bash
# Start dashboard in Client mode
poetry run securevision-ui

# In browser:
# 1. Select "Client (API Server)" mode
# 2. API URL: http://localhost:8000
# 3. Fetch events to view history
```

**Multiple Clients:** You can run multiple dashboard instances pointing to the same API server for distributed monitoring.

### Complete Workflow Examples

#### Example 1: Local Development with MacBook Camera

**Goal:** Test face recognition locally with MacBook camera.

```bash
# 1. Enroll faces
mkdir -p data/faces/trusted
cp ~/photos/john.jpg data/faces/trusted/john_doe.jpg
poetry run securevision-face-enroll --gallery data/faces/trusted --output data/faces/gallery.npz

# 2. Configure
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__FACE__GALLERY_PATH=./data/faces/trusted
export SECUREVISION__FACE__GALLERY_CACHE=./data/faces/gallery.npz
export SECUREVISION__PLATES__ENABLED=false  # Disable plates for indoor use

# 3. Start dashboard
poetry run securevision-ui

# 4. In browser (Standalone mode):
#    - Source: device
#    - Device: 0
#    - Backend: AVFOUNDATION
#    - Connect
#    - Walk in front of camera to see face matches
```

#### Example 2: Driveway Plate Detection with RTSP

**Goal:** Monitor driveway for vehicle plates, match against whitelist.

```bash
# 1. Set up plate lists
mkdir -p data/plates
echo "ABC123" > data/plates/whitelist.csv
echo "XYZ789" >> data/plates/whitelist.csv

# 2. Configure
export SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
export SECUREVISION__VIDEO__SOURCE__URL=rtsp://admin:password@192.168.1.50:554/stream
export SECUREVISION__FACE__ENABLED=false  # Disable faces for outdoor use
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8n_plate.pt
export SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv

# 3. Start dashboard
poetry run securevision-ui

# 4. In browser (Standalone mode):
#    - Source: rtsp
#    - URL: (pre-filled from env)
#    - FPS: 10
#    - Connect
#    - Tune OCR settings for outdoor lighting
```

#### Example 3: Remote Monitoring with API Client

**Goal:** Monitor events from remote location without running capture locally.

```bash
# === On capture server (192.168.1.100) ===

# 1. Configure and start API server
export SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
export SECUREVISION__VIDEO__SOURCE__URL=rtsp://admin:password@192.168.1.50:554/stream
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__PLATES__ENABLED=true
export SECUREVISION__API__HOST=0.0.0.0
export SECUREVISION__API__PORT=8000
export SECUREVISION__API__AUTH_TOKEN=my-secret-token

poetry run securevision-api

# === On monitoring client (laptop/phone) ===

# 2. Start dashboard
poetry run securevision-ui

# 3. In browser (Client mode):
#    - Mode: Client (API Server)
#    - API URL: http://192.168.1.100:8000
#    - Auth Token: my-secret-token
#    - Fetch Events
#    - Enable auto-refresh for live monitoring
```

### Troubleshooting

#### Standalone Mode Issues

**No Face Matches:**
- Verify gallery is enrolled: check `data/faces/gallery.npz` exists
- Check similarity threshold (default 0.35, lower = stricter)
- Ensure faces are visible and well-lit
- Feature status indicator shows: 🟢 Faces enabled

**No Plate Detections:**
- Verify YOLO model exists at configured path
- Check plates are visible in frame (not too small/distant)
- Try lowering detector confidence threshold (config)
- Feature status indicator shows: 🟢 Plates enabled

**Feature Disabled Warning:**
- "⚠️ Face recognition disabled" → Check gallery enrollment
- "⚠️ Plate detection disabled" → Check YOLO model path
- Both features gracefully disable if dependencies missing

**Preview Lag:**
- Reduce FPS target (sidebar slider)
- Enable frame resize (640×480)
- Disable heavy preprocessing (bilateral, CLAHE)

#### Client Mode Issues

**Failed to Connect to API:**
- Verify API server is running: `curl http://localhost:8000/`
- Check API URL is correct (include http://)
- Check network connectivity if remote
- Verify auth token if authentication enabled

**No Events Returned:**
- Click "🔄 Fetch Events" to retrieve from API
- Check time filter (expand to "All time")
- Verify events exist in database: `curl http://localhost:8000/events`

**WebSocket Connection Fails:**
- WebSocket auto-reconnects with exponential backoff
- Check firewall/network allows WebSocket connections
- Verify API server has `WS_ENABLED=true`

### Configuration Persistence

**Standalone Mode:**
- OCR settings are session-only (not saved)
- Use dashboard to find optimal settings
- Copy to environment variables for production

**Client Mode:**
- API URL and auth token persist in session state
- Re-enter when browser session ends or page refreshes

For persistent configuration across sessions:
```bash
# Save to .env file
cat > .env << 'EOF'
SECUREVISION__FACE__ENABLED=true
SECUREVISION__PLATES__ENABLED=true
# ... other settings
EOF

# Load and run
set -a; source .env; set +a
poetry run securevision-ui
```
