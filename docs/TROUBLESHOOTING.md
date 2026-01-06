# SecureVision Troubleshooting Guide

Common issues and their solutions for SecureVision deployment and operation.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Camera Connection Issues](#camera-connection-issues)
- [Face Recognition Issues](#face-recognition-issues)
- [License Plate Recognition Issues](#license-plate-recognition-issues)
- [Performance Issues](#performance-issues)
- [API and WebSocket Issues](#api-and-websocket-issues)
- [Desktop UI Issues](#desktop-ui-issues)
- [Database Issues](#database-issues)
- [Logging and Debugging](#logging-and-debugging)

## Installation Issues

### Poetry Installation Fails

**Symptom:** `poetry install` fails with dependency resolution errors

**Solutions:**

1. **Update Poetry:**
   ```bash
   pip install --upgrade poetry
   ```

2. **Clear Poetry cache:**
   ```bash
   poetry cache clear . --all
   poetry install
   ```

3. **Check Python version:**
   ```bash
   python --version  # Must be 3.10, 3.11, or 3.12
   ```

4. **Use specific Python version:**
   ```bash
   poetry env use python3.11
   poetry install
   ```

### Tesseract Not Found

**Symptom:** `TesseractNotFoundError` when running plate recognition

**Solutions:**

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr libtesseract-dev
```

macOS:
```bash
brew install tesseract
```

Windows:
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install and add to PATH
```

Verify installation:
```bash
tesseract --version
```

### Missing Model Weights

**Symptom:** `FileNotFoundError: ./weights/yolov8n_plate.pt`

**Solution:**

Download YOLOv8 plate detection model:
```bash
mkdir -p weights
# Place your trained YOLOv8 plate model in weights/
# Or use Ultralytics hub to download a model
```

Temporary workaround (disable plates):
```bash
export SECUREVISION__PLATES__ENABLED=false
```

## Camera Connection Issues

### Cannot Open Camera Device

**Symptom:** `Failed to open video source` with device camera

**Solutions:**

1. **Check device index:**
   ```bash
   # List available cameras (Linux)
   v4l2-ctl --list-devices

   # Try different indices
   export SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX=0  # or 1, 2, etc.
   ```

2. **Check camera permissions (Linux):**
   ```bash
   sudo usermod -a -G video $USER
   # Logout and login again
   ```

3. **macOS: Grant camera permissions:**
   - System Preferences → Security & Privacy → Camera
   - Enable for Terminal or your application

4. **Specify backend (macOS):**
   ```bash
   export SECUREVISION__VIDEO__SOURCE__BACKEND=AVFOUNDATION
   ```

### RTSP Stream Connection Fails

**Symptom:** `Connection refused` or timeout when connecting to RTSP stream

**Solutions:**

1. **Test RTSP URL with ffplay:**
   ```bash
   ffplay rtsp://user:pass@192.168.1.100:554/stream
   ```

2. **Verify camera network settings:**
   - Check IP address
   - Ensure camera is on same network
   - Try ping: `ping 192.168.1.100`

3. **Check firewall:**
   ```bash
   # Allow RTSP port (554)
   sudo ufw allow 554/tcp
   ```

4. **Try different RTSP paths:**
   ```bash
   # Common paths
   rtsp://ip:554/
   rtsp://ip:554/stream
   rtsp://ip:554/h264
   rtsp://ip:554/live
   rtsp://ip:554/Streaming/Channels/101
   ```

5. **Increase timeout:**
   ```bash
   export SECUREVISION__VIDEO__READ_TIMEOUT_S=10.0
   ```

### RTSP Stream Constantly Reconnecting

**Symptom:** Log shows repeated `Reconnecting to RTSP stream...`

**Solutions:**

1. **Check network stability:**
   ```bash
   ping -c 100 camera-ip
   ```

2. **Reduce FPS to lower bandwidth:**
   ```bash
   export SECUREVISION__VIDEO__FPS_TARGET=10
   ```

3. **Check camera stream settings:**
   - Lower camera bitrate
   - Use H.264 instead of H.265
   - Reduce camera resolution

4. **Use TCP instead of UDP (if supported):**
   ```bash
   export SECUREVISION__VIDEO__SOURCE__URL=rtsp://ip:554/stream?tcp
   ```

## Face Recognition Issues

### No Faces Detected

**Symptom:** Face recognition enabled but no faces detected in frames

**Solutions:**

1. **Check minimum face size:**
   ```bash
   # Lower threshold for distant faces
   export SECUREVISION__FACE__MIN_FACE_SIZE=30
   ```

2. **Verify camera view:**
   - Ensure faces are visible and well-lit
   - Check camera angle
   - Verify image is not upside down (use `ROTATE_180=true`)

3. **Test with preview:**
   ```bash
   poetry run securevision-preview
   # Visually verify face detection boxes
   ```

### Face Matches Are Inaccurate

**Symptom:** Wrong people matched or no matches for known faces

**Solutions:**

1. **Adjust similarity threshold:**
   ```bash
   # Lower = stricter matching (fewer false positives)
   export SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.30

   # Higher = looser matching (fewer false negatives)
   export SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.40
   ```

2. **Improve gallery images:**
   - Add more photos per person (3-5 recommended)
   - Use clear, front-facing photos
   - Ensure good lighting
   - Minimum 200x200 pixels

3. **Rebuild gallery cache:**
   ```bash
   rm ./data/faces/gallery.npz
   poetry run securevision-face-enroll ./data/faces/trusted
   ```

4. **Check gallery structure:**
   ```
   data/faces/trusted/
     ├── person1/
     │   ├── img1.jpg
     │   └── img2.jpg
     └── person2/
         └── img1.jpg
   ```

### Face Gallery Not Loading

**Symptom:** `No faces loaded from gallery` error

**Solutions:**

1. **Verify gallery path:**
   ```bash
   ls -R $SECUREVISION__FACE__GALLERY_PATH
   ```

2. **Check image formats:**
   - Use JPEG or PNG
   - Verify images are not corrupted

3. **Re-enroll faces:**
   ```bash
   poetry run securevision-face-enroll ./data/faces/trusted
   ```

## License Plate Recognition Issues

### No Plates Detected

**Symptom:** Plates visible but not detected

**Solutions:**

1. **Lower detection threshold:**
   ```bash
   export SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD=0.20
   ```

2. **Check plate size constraints:**
   ```bash
   # Lower minimum size
   export SECUREVISION__PLATES__MIN_WIDTH_PX=40
   export SECUREVISION__PLATES__MIN_HEIGHT_PX=15
   ```

3. **Verify model file:**
   ```bash
   ls -lh ./weights/yolov8n_plate.pt
   ```

4. **Test with different input size:**
   ```bash
   export SECUREVISION__PLATES__DETECTOR__INPUT_SIZE=640  # or 416, 320
   ```

### OCR Returns Gibberish

**Symptom:** Plates detected but OCR text is incorrect

**Solutions:**

1. **Install correct language pack:**
   ```bash
   # For English plates
   sudo apt-get install tesseract-ocr-eng

   # For German plates
   sudo apt-get install tesseract-ocr-deu

   # For Russian plates
   sudo apt-get install tesseract-ocr-rus
   ```

2. **Adjust OCR preprocessing:**
   ```bash
   # Enable preprocessing
   export SECUREVISION__PLATES__OCR__ENABLE_ADAPTIVE_THRESHOLD=true
   export SECUREVISION__PLATES__OCR__ENABLE_BILATERAL=true
   ```

3. **Update character whitelist:**
   ```bash
   # For specific plate format (e.g., German: XX-YY 1234)
   export SECUREVISION__PLATES__OCR__CHAR_WHITELIST="ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ0123456789- "
   ```

4. **Adjust post-processing regex:**
   ```bash
   # For US plates (ABC1234 format)
   export SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z]{3}[0-9]{4}"
   ```

### Plate Confidence Too Low

**Symptom:** Plates detected and OCR'd but confidence below threshold

**Solutions:**

1. **Lower confidence threshold:**
   ```bash
   export SECUREVISION__PLATES__MIN_CONFIDENCE=0.45
   ```

2. **Improve camera positioning:**
   - Ensure plates are perpendicular to camera
   - Improve lighting (avoid glare)
   - Reduce motion blur (increase shutter speed)

3. **Enable multi-frame confirmation:**
   ```bash
   export SECUREVISION__TRACKING__ENABLED=true
   export SECUREVISION__TRACKING__FRAMES_REQUIRED=3
   ```

## Performance Issues

### High CPU Usage

**Symptom:** CPU usage 90-100%, system slow

**Solutions:**

1. **Reduce FPS target:**
   ```bash
   export SECUREVISION__VIDEO__FPS_TARGET=10  # or even 5
   ```

2. **Resize input frames:**
   ```bash
   export SECUREVISION__VIDEO__FRAME_RESIZE=1280,720  # or 640,480
   ```

3. **Disable unused features:**
   ```bash
   # Disable face recognition if not needed
   export SECUREVISION__FACE__ENABLED=false

   # Or disable plate recognition
   export SECUREVISION__PLATES__ENABLED=false
   ```

4. **Use ROI (Region of Interest):**
   ```bash
   export SECUREVISION__PLATES__ROI__ENABLED=true
   export SECUREVISION__PLATES__ROI__Y1=400
   export SECUREVISION__PLATES__ROI__Y2=800
   ```

5. **Reduce plate detector input size:**
   ```bash
   export SECUREVISION__PLATES__DETECTOR__INPUT_SIZE=416  # instead of 640
   ```

### High Memory Usage

**Symptom:** Memory usage growing over time, potential leak

**Solutions:**

1. **Reduce frame window:**
   ```bash
   export SECUREVISION__TRACKING__FRAMES_WINDOW=3
   export SECUREVISION__TRACKING__MAX_AGE_FRAMES=15
   ```

2. **Enable event cleanup:**
   ```bash
   export SECUREVISION__EVENTS__RETENTION_DAYS=7
   ```

3. **Monitor memory:**
   ```bash
   watch -n 1 'ps aux | grep securevision'
   ```

4. **Restart service periodically (systemd):**
   ```ini
   [Service]
   RuntimeMaxSec=86400  # Restart daily
   ```

### Low FPS / Slow Processing

**Symptom:** Processing FPS much lower than target

**Solutions:**

1. **Check CPU utilization:**
   ```bash
   htop
   ```

2. **Profile bottlenecks:**
   ```bash
   poetry run python -m cProfile -o profile.stats your_script.py
   ```

3. **GPU acceleration (if available):**
   - Install CUDA-enabled PyTorch
   - Use GPU-optimized model

4. **Reduce processing load:**
   - Lower video resolution
   - Reduce FPS target
   - Use smaller model (`yolov8n` instead of `yolov8m`)

## API and WebSocket Issues

### API Server Won't Start

**Symptom:** `Address already in use` or API fails to start

**Solutions:**

1. **Check port availability:**
   ```bash
   lsof -i :8000
   # Or
   netstat -tulpn | grep 8000
   ```

2. **Kill existing process:**
   ```bash
   kill <PID>
   ```

3. **Use different port:**
   ```bash
   export SECUREVISION__API__PORT=8001
   ```

### Cannot Connect to WebSocket

**Symptom:** WebSocket connection fails or immediately closes

**Solutions:**

1. **Verify WebSocket is enabled:**
   ```bash
   export SECUREVISION__API__WS_ENABLED=true
   ```

2. **Check WebSocket URL:**
   ```javascript
   // Correct format
   const ws = new WebSocket('ws://localhost:8000/stream');
   ```

3. **Check CORS settings** (if connecting from browser)

4. **Test with simple client:**
   ```bash
   npm install -g wscat
   wscat -c ws://localhost:8000/stream
   ```

### 401 Unauthorized Errors

**Symptom:** API returns 401 on authenticated endpoints

**Solutions:**

1. **Include auth token:**
   ```bash
   curl -H "Authorization: Bearer your-token" \
     http://localhost:8000/events
   ```

2. **Verify token matches:**
   ```bash
   echo $SECUREVISION__API__AUTH_TOKEN
   ```

3. **Disable auth for testing:**
   ```bash
   export SECUREVISION__API__AUTH_TOKEN=
   ```

## Desktop UI Issues

### Qt UI Won't Start

**Symptom:** `ImportError: PySide6` or Qt application crashes

**Solutions:**

1. **Reinstall PySide6:**
   ```bash
   poetry add PySide6 --force
   ```

2. **Check Qt platform plugin (Linux):**
   ```bash
   export QT_QPA_PLATFORM=xcb  # or wayland
   ```

3. **Install Qt dependencies (Linux):**
   ```bash
   sudo apt-get install libxcb-xinerama0 libxcb-cursor0
   ```

### Blank Preview Window

**Symptom:** Qt UI opens but video preview is black/blank

**Solutions:**

1. **Check camera connection first:**
   ```bash
   poetry run securevision-preview  # Test without Qt
   ```

2. **Verify OpenGL support:**
   ```bash
   glxinfo | grep "OpenGL"
   ```

3. **Try software rendering:**
   ```bash
   export QT_XCB_GL_INTEGRATION=none
   ```

## Database Issues

### Database Locked Error

**Symptom:** `database is locked` when accessing SQLite

**Solutions:**

1. **Close other connections:**
   - Ensure only one process accesses database
   - Stop duplicate API instances

2. **Increase timeout:**
   ```python
   # In code: increase timeout when creating engine
   db_url = "sqlite:///./data/events.db?timeout=30"
   ```

3. **Check file permissions:**
   ```bash
   ls -l data/events.db
   chmod 644 data/events.db
   ```

### Database Corruption

**Symptom:** `database disk image is malformed`

**Solutions:**

1. **Verify database integrity:**
   ```bash
   sqlite3 data/events.db "PRAGMA integrity_check;"
   ```

2. **Attempt recovery:**
   ```bash
   sqlite3 data/events.db ".recover" | sqlite3 data/events-recovered.db
   ```

3. **Restore from backup:**
   ```bash
   cp backups/events-20240101.db data/events.db
   ```

4. **Last resort (delete and recreate):**
   ```bash
   rm data/events.db
   # Database will be recreated on next start
   ```

## Logging and Debugging

### Enable Debug Logging

```bash
# Set Python logging level
export PYTHONUNBUFFERED=1
export SECUREVISION_LOG_LEVEL=DEBUG
```

### View Logs

**Systemd service:**
```bash
sudo journalctl -u securevision-api -f
```

**Docker:**
```bash
docker-compose logs -f securevision-api
```

**File logs:**
```bash
tail -f logs/securevision.log
```

### Common Log Messages

**`WARNING: Frame dropped (FPS limit)`**
- Normal: Frame dropping to achieve target FPS
- Action: No action needed unless FPS too low

**`ERROR: Failed to read frame, reconnecting...`**
- Cause: Network stream disconnected
- Action: Check camera network connection

**`WARNING: No face matches above threshold`**
- Cause: No known faces detected
- Action: Check similarity threshold and gallery

**`ERROR: Tesseract failed with return code 1`**
- Cause: OCR preprocessing issue
- Action: Check image quality and preprocessing settings

### Performance Profiling

**CPU profiling:**
```bash
poetry run python -m cProfile -o profile.stats -m cam_vision.cli.run_api
python -m pstats profile.stats
```

**Memory profiling:**
```bash
poetry run python -m memory_profiler your_script.py
```

**Benchmarking:**
```bash
poetry run pytest tests/benchmarks/ --benchmark-only
```

## Getting Help

If none of these solutions work:

1. **Check existing issues:**
   - GitHub Issues: https://github.com/yourusername/cam-vision/issues

2. **Create new issue with:**
   - SecureVision version
   - Python version (`python --version`)
   - Operating system
   - Complete error message and stack trace
   - Configuration (sanitize sensitive data)
   - Steps to reproduce

3. **Include logs:**
   ```bash
   # Capture logs to file
   poetry run securevision-api 2>&1 | tee debug.log
   ```

## See Also

- [Configuration Reference](CONFIG.md) - All configuration options
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [FAQ](FAQ.md) - Frequently asked questions
- [User Guide](USER_GUIDE.md) - End-user documentation
