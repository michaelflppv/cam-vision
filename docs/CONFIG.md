# SecureVision Configuration Reference

Complete reference for all SecureVision configuration options using environment variables.

## Table of Contents

- [Overview](#overview)
- [Configuration Format](#configuration-format)
- [Video Source Settings](#video-source-settings)
- [Face Recognition Settings](#face-recognition-settings)
- [License Plate Settings](#license-plate-settings)
- [Event Storage Settings](#event-storage-settings)
- [Tracking Settings](#tracking-settings)
- [API Settings](#api-settings)
- [Example Configurations](#example-configurations)
- [Configuration Validation](#configuration-validation)

## Overview

SecureVision uses environment variables for all configuration. This approach:
- Works seamlessly with Docker and containerized deployments
- Integrates with systemd service units
- Supports `.env` files for local development
- Follows 12-factor app principles

**Key Features:**
- Type validation via Pydantic
- Nested configuration using double underscore (`__`)
- Sensible defaults for all optional settings
- Clear error messages on invalid configuration

## Configuration Format

### Environment Variable Naming

All settings use the prefix `SECUREVISION__` followed by nested sections:

```
SECUREVISION__<SECTION>__<SUBSECTION>__<KEY>
```

**Examples:**
```bash
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__FPS_TARGET=15
SECUREVISION__FACE__ENABLED=true
SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.25
```

### Using .env Files

For local development, create a `.env` file:

```bash
# Video source
SECUREVISION__VIDEO__SOURCE__TYPE=device
SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0
SECUREVISION__VIDEO__FPS_TARGET=15

# Enable/disable features
SECUREVISION__FACE__ENABLED=true
SECUREVISION__PLATES__ENABLED=true
```

Load environment file:
```bash
set -a; source .env; set +a
poetry run securevision-qt
```

### Configuration Precedence

1. Environment variables (highest priority)
2. `.env` file (if using `source` or docker-compose)
3. Default values (lowest priority)

## Video Source Settings

### Video Source Type

**Section:** `SECUREVISION__VIDEO__SOURCE__`

Configure the video input source. SecureVision supports multiple source types.

#### Device (USB/Built-in Camera)

```bash
SECUREVISION__VIDEO__SOURCE__TYPE=device
SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0      # 0 = first camera, 1 = second, etc.
SECUREVISION__VIDEO__SOURCE__BACKEND=AVFOUNDATION  # Optional: macOS hint
```

**Device Index:**
- `0`: First camera (MacBook built-in, or first USB)
- `1`: Second camera
- `2`: Third camera, etc.

**Backend (Optional):**
- `AVFOUNDATION`: macOS (recommended for MacBook)
- `DSHOW`: Windows
- `V4L2`: Linux
- Leave empty for auto-detection

#### RTSP Network Stream

```bash
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://user:password@192.168.1.100:554/stream
```

**URL Format:**
```
rtsp://[username:password@]host:port/path
```

**Examples:**
```bash
# Camera with authentication
SECUREVISION__VIDEO__SOURCE__URL=rtsp://admin:12345@192.168.1.50:554/h264

# Camera without authentication
SECUREVISION__VIDEO__SOURCE__URL=rtsp://192.168.1.50:554/stream1

# Custom port
SECUREVISION__VIDEO__SOURCE__URL=rtsp://cam:pass@10.0.0.100:8554/live
```

#### HTTP MJPEG Stream

```bash
SECUREVISION__VIDEO__SOURCE__TYPE=http_mjpeg
SECUREVISION__VIDEO__SOURCE__URL=http://192.168.1.100:8080/video
```

**Examples:**
```bash
# Basic MJPEG stream
SECUREVISION__VIDEO__SOURCE__URL=http://camera.local:8080/mjpeg

# With authentication in URL
SECUREVISION__VIDEO__SOURCE__URL=http://user:pass@192.168.1.50:8080/stream
```

#### Video File

```bash
SECUREVISION__VIDEO__SOURCE__TYPE=file
SECUREVISION__VIDEO__SOURCE__URL=/path/to/video.mp4
```

**Supported Formats:**
- MP4 (H.264, H.265)
- AVI
- MKV
- MOV

#### RTMP Stream

```bash
SECUREVISION__VIDEO__SOURCE__TYPE=rtmp
SECUREVISION__VIDEO__SOURCE__URL=rtmp://server:port/app/streamkey
```

### Video Processing Settings

```bash
# Target processing FPS (frames will be dropped to achieve this rate)
SECUREVISION__VIDEO__FPS_TARGET=15
# Default: 15
# Range: 1-60
# Lower values reduce CPU usage

# Resize frames before processing (width, height)
SECUREVISION__VIDEO__FRAME_RESIZE=1280,720
# Default: None (no resizing)
# Format: "width,height"
# Example: "640,480" for VGA resolution

# Rotate frame 180 degrees (for upside-down cameras)
SECUREVISION__VIDEO__ROTATE_180=false
# Default: false

# Enable ONVIF discovery helpers
SECUREVISION__VIDEO__ONVIF_DISCOVERY_ENABLED=false
# Default: false

# Network source timeouts
SECUREVISION__VIDEO__READ_TIMEOUT_S=5.0
# Default: 5.0 seconds
# Per-frame read timeout for network sources

SECUREVISION__VIDEO__RECONNECT_INTERVAL_S=3.0
# Default: 3.0 seconds
# Delay before reconnection attempts
```

## Face Recognition Settings

**Section:** `SECUREVISION__FACE__`

### Basic Settings

```bash
# Enable/disable face recognition
SECUREVISION__FACE__ENABLED=true
# Default: true

# Path to trusted faces gallery (directory with subdirectories per person)
SECUREVISION__FACE__GALLERY_PATH=./data/faces/trusted
# Default: ./data/faces/trusted
# Structure: gallery_path/person_name/*.jpg

# Gallery cache file (pre-computed embeddings)
SECUREVISION__FACE__GALLERY_CACHE=./data/faces/gallery.npz
# Default: ./data/faces/gallery.npz
# Auto-generated on first run

# Similarity threshold for face matching
SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.35
# Default: 0.35
# Range: 0.0-1.0 (lower = stricter matching)
# Recommended: 0.30-0.40

# Minimum face size to process (pixels)
SECUREVISION__FACE__MIN_FACE_SIZE=40
# Default: 40
# Faces smaller than this will be ignored
```

### Face Gallery Structure

Organize face images in subdirectories by person name:

```
data/faces/trusted/
  ├── john_doe/
  │   ├── photo1.jpg
  │   ├── photo2.jpg
  │   └── photo3.jpg
  ├── jane_smith/
  │   ├── image1.jpg
  │   └── image2.jpg
  └── alex_wilson/
      └── profile.jpg
```

**Recommendations:**
- 3-5 images per person
- Different angles and lighting
- Clear, front-facing photos
- Minimum 200x200 pixels
- JPEG or PNG format

## License Plate Settings

**Section:** `SECUREVISION__PLATES__`

### Enable/Disable

```bash
# Enable/disable license plate recognition
SECUREVISION__PLATES__ENABLED=true
# Default: true
```

### Detector Settings (YOLOv8)

**Section:** `SECUREVISION__PLATES__DETECTOR__`

```bash
# Path to YOLOv8 plate detection model
SECUREVISION__PLATES__DETECTOR__MODEL_PATH=./weights/yolov8n_plate.pt
# Default: ./weights/yolov8n_plate.pt
# Use yolov8n (nano) for CPU, yolov8s or yolov8m for GPU

# Detection confidence threshold
SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.25
# Default: 0.25
# Range: 0.0-1.0 (higher = stricter)

# Non-maximum suppression IoU threshold
SECUREVISION__PLATES__DETECTOR__IOU_THRESHOLD=0.45
# Default: 0.45
# Range: 0.0-1.0

# Maximum detections per frame
SECUREVISION__PLATES__DETECTOR__MAX_DET=10
# Default: 10
# Increase for multi-lane scenarios

# Model input size (square)
SECUREVISION__PLATES__DETECTOR__INPUT_SIZE=640
# Default: 640
# Options: 320, 416, 640 (higher = more accurate but slower)
```

### OCR Settings (Tesseract)

**Section:** `SECUREVISION__PLATES__OCR__`

```bash
# Tesseract language packs
SECUREVISION__PLATES__OCR__TESSERACT_LANG=eng+rus
# Default: eng+rus
# Options: eng, rus, deu, fra, etc. (combine with +)
# Install with: sudo apt-get install tesseract-ocr-rus

# Page segmentation mode (PSM)
SECUREVISION__PLATES__OCR__PSM_MODE=7
# Default: 7 (single line)
# Options: 6=block, 7=line, 8=word, 13=raw line

# OCR Engine mode (OEM)
SECUREVISION__PLATES__OCR__OEM_MODE=3
# Default: 3 (default)
# Options: 0=legacy, 1=LSTM, 2=legacy+LSTM, 3=default

# Character whitelist (allowed characters)
SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "
# Default: "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "

# Crop margin around detected plate (pixels)
SECUREVISION__PLATES__OCR__CROP_MARGIN_PX=8
# Default: 8

# Preprocessing pipeline
SECUREVISION__PLATES__OCR__ENABLE_GRAYSCALE=true
# Default: true (recommended)

SECUREVISION__PLATES__OCR__ENABLE_BILATERAL=false
# Default: false (adds overhead)

SECUREVISION__PLATES__OCR__ENABLE_ADAPTIVE_THRESHOLD=false
# Default: false (good for uneven lighting)

SECUREVISION__PLATES__OCR__ENABLE_CLAHE=false
# Default: false (minimal benefit for plates)
```

### Post-Processing Settings

**Section:** `SECUREVISION__PLATES__POSTPROCESS__`

```bash
# Regex pattern for valid plate format
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9\\u0410-\\u042F\\u0401-]{4,10}"
# Default: "[A-Z0-9\\u0410-\\u042F\\u0401-]{4,10}"
# Supports Latin + Cyrillic uppercase

# Convert to uppercase before validation
SECUREVISION__PLATES__POSTPROCESS__UPPERCASE=true
# Default: true

# Minimum plate text length
SECUREVISION__PLATES__POSTPROCESS__MIN_LENGTH=4
# Default: 4

# Maximum plate text length
SECUREVISION__PLATES__POSTPROCESS__MAX_LENGTH=10
# Default: 10
```

### Region of Interest (ROI)

**Section:** `SECUREVISION__PLATES__ROI__`

Crop frame to region of interest before detection (performance optimization).

```bash
# Enable ROI cropping
SECUREVISION__PLATES__ROI__ENABLED=false
# Default: false

# ROI coordinates (pixels)
SECUREVISION__PLATES__ROI__X1=0
SECUREVISION__PLATES__ROI__Y1=400
SECUREVISION__PLATES__ROI__X2=1920
SECUREVISION__PLATES__ROI__Y2=800
# Default: 0,0,0,0 (full frame)
# Format: top-left (x1,y1), bottom-right (x2,y2)
```

**Use Case:** Fixed camera angle where plates always appear in lower portion of frame.

### Plate Validation

```bash
# Whitelist CSV file (authorized plates)
SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/whitelist.csv
# Default: ./data/plates/whitelist.csv
# Format: plate_text,description

# Blacklist CSV file (blocked plates)
SECUREVISION__PLATES__BLACKLIST_PATH=./data/plates/blacklist.csv
# Default: ./data/plates/blacklist.csv

# Overall event confidence threshold
SECUREVISION__PLATES__MIN_CONFIDENCE=0.55
# Default: 0.55
# Combined detection + OCR confidence

# Plate aspect ratio constraints (width/height)
SECUREVISION__PLATES__MIN_ASPECT_RATIO=1.2
SECUREVISION__PLATES__MAX_ASPECT_RATIO=8.5
# Defaults: 1.2 - 8.5
# Filters out non-plate detections

# Minimum plate size (pixels)
SECUREVISION__PLATES__MIN_WIDTH_PX=60
SECUREVISION__PLATES__MIN_HEIGHT_PX=18
# Defaults: 60x18
# Reject small/distant plates
```

## Event Storage Settings

**Section:** `SECUREVISION__EVENTS__`

```bash
# Database URL (SQLite)
SECUREVISION__EVENTS__DB_URL=sqlite:///./data/events.db
# Default: sqlite:///./data/events.db
# Format: sqlite:///path/to/events.db

# Event retention period (days)
SECUREVISION__EVENTS__RETENTION_DAYS=30
# Default: 30
# Events older than this are automatically deleted
```

## Tracking Settings

**Section:** `SECUREVISION__TRACKING__`

Multi-frame confirmation to reduce false positives.

```bash
# Enable tracking and multi-frame confirmation
SECUREVISION__TRACKING__ENABLED=true
# Default: true

# Consecutive frames required for confirmation
SECUREVISION__TRACKING__FRAMES_REQUIRED=3
# Default: 3
# Range: 1-10 (higher = fewer false positives, slower reaction)

# Frame window for tracking (lookback)
SECUREVISION__TRACKING__FRAMES_WINDOW=5
# Default: 5
# Must be >= frames_required

# Minimum IoU for bbox matching across frames
SECUREVISION__TRACKING__IOU_THRESHOLD=0.5
# Default: 0.5
# Range: 0.0-1.0 (higher = stricter tracking)

# Maximum frames without match before track removal
SECUREVISION__TRACKING__MAX_AGE_FRAMES=30
# Default: 30

# OCR text agreement ratio for plate confirmation
SECUREVISION__TRACKING__OCR_AGREEMENT_THRESHOLD=0.6
# Default: 0.6
# Minimum fraction of frames with matching OCR text

# Cooldown period between duplicate events (seconds)
SECUREVISION__TRACKING__COOLDOWN_SECONDS=30.0
# Default: 30.0
# Prevent duplicate alerts for same person/plate
```

## API Settings

**Section:** `SECUREVISION__API__`

```bash
# API server host
SECUREVISION__API__HOST=0.0.0.0
# Default: 0.0.0.0 (all interfaces)
# Use 127.0.0.1 for localhost only

# API server port
SECUREVISION__API__PORT=8000
# Default: 8000

# Enable WebSocket streaming
SECUREVISION__API__WS_ENABLED=true
# Default: true

# Authentication bearer token (optional)
SECUREVISION__API__AUTH_TOKEN=your-secret-token-here
# Default: None (no authentication)
# Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Example Configurations

### Home Security (Single Camera)

```bash
# .env for home security setup
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://admin:password@192.168.1.50:554/stream
SECUREVISION__VIDEO__FPS_TARGET=10

SECUREVISION__FACE__ENABLED=true
SECUREVISION__FACE__GALLERY_PATH=./data/faces/family
SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.30

SECUREVISION__PLATES__ENABLED=true
SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/family_cars.csv

SECUREVISION__TRACKING__FRAMES_REQUIRED=3
SECUREVISION__TRACKING__COOLDOWN_SECONDS=60

SECUREVISION__API__AUTH_TOKEN=my-secret-token-123
SECUREVISION__API__WS_ENABLED=true
```

### Parking Garage (Plate Recognition Only)

```bash
# .env for parking garage
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://camera:pass@10.0.0.100:554/h264
SECUREVISION__VIDEO__FPS_TARGET=15
SECUREVISION__VIDEO__FRAME_RESIZE=1280,720

SECUREVISION__FACE__ENABLED=false

SECUREVISION__PLATES__ENABLED=true
SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.30
SECUREVISION__PLATES__OCR__TESSERACT_LANG=eng
SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/authorized.csv
SECUREVISION__PLATES__MIN_CONFIDENCE=0.60

# ROI for entrance gate area
SECUREVISION__PLATES__ROI__ENABLED=true
SECUREVISION__PLATES__ROI__Y1=500
SECUREVISION__PLATES__ROI__Y2=900

SECUREVISION__TRACKING__FRAMES_REQUIRED=5
SECUREVISION__EVENTS__RETENTION_DAYS=90
```

### Development (MacBook Webcam)

```bash
# .env for local development
SECUREVISION__VIDEO__SOURCE__TYPE=device
SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0
SECUREVISION__VIDEO__SOURCE__BACKEND=AVFOUNDATION
SECUREVISION__VIDEO__FPS_TARGET=10

SECUREVISION__FACE__ENABLED=true
SECUREVISION__FACE__GALLERY_PATH=./data/faces/test
SECUREVISION__FACE__MIN_FACE_SIZE=60

SECUREVISION__PLATES__ENABLED=false

SECUREVISION__API__HOST=127.0.0.1
SECUREVISION__API__PORT=8000
SECUREVISION__API__AUTH_TOKEN=
```

### European Plates (Germany)

```bash
# .env for German license plates
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://cam:pass@192.168.1.50:554/stream

SECUREVISION__FACE__ENABLED=false

SECUREVISION__PLATES__ENABLED=true
SECUREVISION__PLATES__OCR__TESSERACT_LANG=deu+eng
SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789- "
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}[0-9]{1,4}"
SECUREVISION__PLATES__POSTPROCESS__MIN_LENGTH=5
SECUREVISION__PLATES__POSTPROCESS__MAX_LENGTH=10
```

### Multi-Language (Cyrillic + Latin)

```bash
# .env for EU border region (supports Russian and Latin plates)
SECUREVISION__PLATES__OCR__TESSERACT_LANG=eng+rus
SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ- "
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9\\u0410-\\u042F\\u0401-]{4,10}"
```

## Configuration Validation

### Checking Configuration

Test configuration without running the full pipeline:

```python
from cam_vision.config import load_settings

try:
    settings = load_settings()
    print("Configuration valid!")
    print(f"Video source: {settings.video.source.type}")
    print(f"Face recognition: {settings.face.enabled}")
    print(f"Plate recognition: {settings.plates.enabled}")
except Exception as e:
    print(f"Configuration error: {e}")
```

### Common Validation Errors

**Missing RTSP URL:**
```
ValidationError: RTSP url required
```
Solution: Set `SECUREVISION__VIDEO__SOURCE__URL`

**Invalid FPS:**
```
ValidationError: fps_target must be positive integer
```
Solution: Use positive integer (1-60)

**Invalid threshold:**
```
ValidationError: similarity_threshold must be between 0.0 and 1.0
```
Solution: Use value in valid range

### Environment Variable Debugging

Print all SecureVision environment variables:

```bash
env | grep SECUREVISION
```

Verify specific setting:

```bash
echo $SECUREVISION__VIDEO__SOURCE__TYPE
```

## See Also

- [User Guide](USER_GUIDE.md) - End-user documentation
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Documentation](API.md) - API reference
- [Examples Directory](examples/env/) - Pre-configured environment templates
