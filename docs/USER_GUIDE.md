# SecureVision User Guide

Complete guide for setting up and using SecureVision for home and business security.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Desktop Application](#desktop-application)
- [Setting Up Face Recognition](#setting-up-face-recognition)
- [Setting Up License Plate Recognition](#setting-up-license-plate-recognition)
- [Viewing Events](#viewing-events)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)
- [Privacy and Data](#privacy-and-data)

## Introduction

### What is SecureVision?

SecureVision is a self-hosted computer vision platform that helps you monitor your property using:
- **Face Recognition**: Identify trusted family members and friends
- **License Plate Recognition**: Track authorized and unauthorized vehicles
- **Real-time Alerts**: Get notified when specific people or plates are detected
- **Event History**: Search and review past detections

### Key Features

- **Privacy-First**: All processing happens locally on your device
- **No Cloud**: Your images and data never leave your network
- **Open Source**: Transparent, auditable code
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Multi-Camera**: Support for USB, RTSP, and HTTP cameras
- **Easy Setup**: Desktop app with live preview

## Getting Started

### System Requirements

**Minimum:**
- Computer with 4-core CPU
- 8 GB RAM
- 20 GB available storage
- Python 3.10 or newer
- Network connection for IP cameras (optional)

**Recommended:**
- 8+ core CPU (Intel i7/AMD Ryzen 7 or better)
- 16 GB RAM
- SSD storage
- Dedicated computer (old laptop works great)

### Installation

#### Step 1: Install Python

**Windows:**
- Download Python 3.11 from python.org
- Run installer and check "Add Python to PATH"

**macOS:**
```bash
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.11 python3-pip
```

#### Step 2: Install Poetry

```bash
pip install pipx
pipx install poetry
```

#### Step 3: Install SecureVision

```bash
# Download SecureVision
git clone https://github.com/yourusername/cam-vision.git
cd cam-vision

# Install dependencies
poetry install
```

#### Step 4: Install Optional Components

**For License Plate Recognition (Tesseract):**

Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr
```

macOS:
```bash
brew install tesseract
```

Windows:
- Download from https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH

### Quick Start

1. **Choose a configuration template:**
   ```bash
   # For MacBook webcam
   cp examples/env/complete-home.env .env

   # Or for IP camera
   cp examples/env/rtsp-doorbell.env .env
   ```

2. **Edit configuration:**
   ```bash
   # Edit .env file with your camera details
   nano .env
   ```

3. **Start desktop app:**
   ```bash
   set -a; source .env; set +a
   poetry run securevision-qt
   ```

## Desktop Application

### Main Window

The desktop application provides:
- **Live camera preview** with detection boxes
- **Event log** showing recent detections
- **Start/Stop controls**
- **Configuration access**

### Starting Video Processing

1. Click **Start** button
2. Video preview will show live camera feed
3. Green boxes appear around detected faces
4. Blue boxes appear around detected license plates
5. Events appear in the event log panel

### Stopping Processing

Click **Stop** button to pause video processing and close camera connection.

### Understanding Detection Boxes

**Green Box (Face):**
- Person's name shown if recognized
- "Unknown" shown for unrecognized faces
- Confidence percentage displayed

**Blue Box (Plate):**
- License plate text shown
- Confidence percentage displayed
- "Whitelist" or "Blacklist" badge if matched

### Event Log

Shows recent detections with:
- Timestamp
- Detection type (Face/Plate)
- Person name or plate text
- Confidence score
- Camera source

Click on event to view details.

## Setting Up Face Recognition

### Creating Your Face Gallery

1. **Create directory structure:**
   ```bash
   mkdir -p data/faces/trusted/john_doe
   mkdir -p data/faces/trusted/jane_smith
   ```

2. **Add photos for each person:**
   - Copy 3-5 clear photos of each person
   - Name folders exactly as you want names to appear
   - Use underscores for spaces (john_doe, not john doe)

   ```
   data/faces/trusted/
     ├── john_doe/
     │   ├── photo1.jpg
     │   ├── photo2.jpg
     │   └── photo3.jpg
     └── jane_smith/
         ├── img1.jpg
         └── img2.jpg
   ```

### Photo Guidelines

**Good Photos:**
- Clear, front-facing view
- Good lighting (avoid shadows on face)
- Person looking at camera
- Minimum 200x200 pixels
- JPEG or PNG format
- Different expressions and angles

**Avoid:**
- Blurry photos
- Side profiles
- Sunglasses or hats
- Heavy shadows
- Group photos (crop to single face)

### Enrolling Faces

```bash
poetry run securevision-face-enroll ./data/faces/trusted
```

This command:
1. Scans all subdirectories
2. Detects faces in each photo
3. Creates face embeddings
4. Saves to gallery cache file

### Adjusting Face Matching

Edit `.env` file:

```bash
# Stricter matching (fewer false positives)
SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.30

# Looser matching (fewer false negatives)
SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.40
```

Default: 0.35 (balanced)

## Setting Up License Plate Recognition

### Creating Plate Lists

#### Whitelist (Authorized Vehicles)

Create `data/plates/whitelist.csv`:

```csv
plate_text,description
ABC1234,Family car
XYZ9876,Guest parking pass
DEF5678,Service vehicle
```

#### Blacklist (Blocked Vehicles)

Create `data/plates/blacklist.csv`:

```csv
plate_text,description
BAD1234,Suspicious vehicle
OLD9999,Former resident
```

### Regional Configuration

#### US Plates

```bash
SECUREVISION__PLATES__OCR__TESSERACT_LANG=eng
SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9]{4,8}"
```

#### European Plates (Germany)

```bash
SECUREVISION__PLATES__OCR__TESSERACT_LANG=deu+eng
SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789- "
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}[0-9]{1,4}"
```

#### Multi-Language (Cyrillic)

```bash
SECUREVISION__PLATES__OCR__TESSERACT_LANG=eng+rus
SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ- "
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9\\u0410-\\u042F\\u0401-]{4,10}"
```

### Adjusting Plate Detection

```bash
# Detect more plates (may increase false positives)
SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.20

# Stricter detection (fewer false positives)
SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.35

# Overall confidence threshold
SECUREVISION__PLATES__MIN_CONFIDENCE=0.55
```

## Viewing Events

### Using the Desktop App

Events appear in real-time in the event log panel:
- Click on event to view details
- Filter by type (Face/Plate)
- Search by name or plate text

### Using the Web API

Access events via REST API:

```bash
# View recent events
curl http://localhost:8000/events?limit=20

# View only face matches
curl http://localhost:8000/events?type=face_match

# View only plate reads
curl http://localhost:8000/events?type=plate_read
```

### Using WebSocket for Live Updates

Connect to WebSocket for real-time event streaming:

```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'face_match') {
    console.log(`Face detected: ${data.payload.person_name}`);
  }
};
```

## Common Use Cases

### Home Security

**Goal:** Recognize family members at front door

**Setup:**
1. Position camera at front door
2. Enroll family members' faces
3. Enable face recognition
4. Disable plate recognition if not needed

**Configuration:**
```bash
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://doorbell-camera:554/stream
SECUREVISION__FACE__ENABLED=true
SECUREVISION__PLATES__ENABLED=false
SECUREVISION__TRACKING__COOLDOWN_SECONDS=60
```

### Parking Garage

**Goal:** Track authorized vehicles entering/exiting

**Setup:**
1. Position camera to capture license plates
2. Create whitelist of authorized plates
3. Enable plate recognition
4. Disable face recognition

**Configuration:**
```bash
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://garage-camera:554/stream
SECUREVISION__FACE__ENABLED=false
SECUREVISION__PLATES__ENABLED=true
SECUREVISION__PLATES__WHITELIST_PATH=./data/plates/residents.csv
```

### Business Entrance

**Goal:** Log employee arrivals via face recognition

**Setup:**
1. Camera at main entrance
2. Enroll all employees
3. Track entry events

**Configuration:**
```bash
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://entrance-camera:554/stream
SECUREVISION__FACE__ENABLED=true
SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.30
SECUREVISION__TRACKING__FRAMES_REQUIRED=5
SECUREVISION__EVENTS__RETENTION_DAYS=90
```

### Multi-Camera Setup

Run separate SecureVision instances for each camera:

```bash
# Camera 1 (front door)
SECUREVISION__VIDEO__SOURCE__URL=rtsp://front:554/stream \
SECUREVISION__API__PORT=8001 \
poetry run securevision-api &

# Camera 2 (back door)
SECUREVISION__VIDEO__SOURCE__URL=rtsp://back:554/stream \
SECUREVISION__API__PORT=8002 \
poetry run securevision-api &
```

## Best Practices

### Camera Placement

**Face Recognition:**
- Height: 5-6 feet (eye level)
- Angle: Perpendicular to face (not from above)
- Distance: 3-10 feet optimal
- Lighting: Avoid direct sunlight and backlighting

**License Plate Recognition:**
- Height: Low angle (capture front/rear plates)
- Angle: Perpendicular to plates (minimize skew)
- Distance: 10-30 feet optimal
- Lighting: Consider IR illuminator for night

### Performance Optimization

**For slower computers:**
- Reduce FPS target (10 or even 5)
- Resize frames to lower resolution
- Use ROI (region of interest) for plates
- Disable unused feature (face or plates)

**For multiple cameras:**
- Use dedicated computer per 2-3 cameras
- Lower FPS per camera
- Use GPU if available

### Reducing False Positives

**Face Recognition:**
- Use 3-5 photos per person
- Set stricter threshold (0.30)
- Enable multi-frame confirmation

**Plate Recognition:**
- Increase confidence threshold
- Use regex patterns specific to your region
- Enable multi-frame confirmation
- Set cooldown period (30-60 seconds)

### Network Cameras

**For reliable RTSP streams:**
- Use wired Ethernet (not WiFi)
- Configure camera for H.264 (not H.265)
- Set camera bitrate to 2-4 Mbps
- Disable camera motion detection
- Use camera's sub-stream for lower resolution

## Privacy and Data

### What Data is Stored?

**Face Recognition:**
- Face embeddings (not original photos)
- Person names
- Detection timestamps
- Bounding box coordinates

**License Plates:**
- Plate text
- Detection timestamps
- Confidence scores
- Whitelist/blacklist matches

**NOT Stored:**
- Full video frames
- Original camera footage
- Unrecognized faces (unless configured)

### Data Location

All data stored locally:
- Events database: `data/events.db` (SQLite)
- Face gallery: `data/faces/trusted/`
- Plate lists: `data/plates/*.csv`

### Data Retention

Configure automatic cleanup:

```bash
# Keep events for 30 days
SECUREVISION__EVENTS__RETENTION_DAYS=30
```

Manual cleanup:
```bash
# Delete all events older than retention period
curl -X POST http://localhost:8000/cleanup
```

### Privacy Best Practices

1. **Don't expose API publicly** - Use localhost only or secure with auth token
2. **Use strong auth tokens** - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
3. **Regularly review events** - Delete old events you don't need
4. **Secure camera credentials** - Never commit passwords to git
5. **Inform visitors** - Post signage about video surveillance

### GDPR Compliance (EU)

If subject to GDPR:
- Inform individuals about surveillance (signage)
- Limit retention to necessary period
- Provide data access/deletion on request
- Document legitimate interest or legal basis
- Consider privacy impact assessment for high-risk processing

## Getting Help

**Documentation:**
- [Configuration Reference](CONFIG.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [FAQ](FAQ.md)
- [API Documentation](API.md)

**Support:**
- GitHub Issues: https://github.com/yourusername/cam-vision/issues
- Discussions: https://github.com/yourusername/cam-vision/discussions

**Contributing:**
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
