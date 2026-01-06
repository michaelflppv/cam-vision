# SecureVision FAQ (Frequently Asked Questions)

Common questions about SecureVision setup, usage, and capabilities.

## General Questions

### What is SecureVision?

SecureVision is an open-source, self-hosted computer vision platform for processing live camera feeds. It performs face recognition and license plate recognition (ALPR) to identify trusted people and vehicles, all while keeping your data private and local.

### Is SecureVision free?

Yes! SecureVision is completely free and open-source under the MIT License. There are no subscription fees, cloud services, or hidden costs.

### Does SecureVision require an internet connection?

No. SecureVision runs entirely locally on your device. An internet connection is only needed for:
- Initial installation and updates
- Accessing network cameras (RTSP/HTTP streams) on your local network

All processing happens on your device, and no data is sent to external servers.

### Can I use SecureVision commercially?

Yes. The MIT License allows commercial use. However, please review local regulations regarding surveillance and privacy before deploying in a business environment.

### Is SecureVision cloud-based?

No. SecureVision is deliberately designed as a self-hosted, privacy-first solution. All your data stays on your device or local network.

## System Requirements

### What are the minimum system requirements?

- **CPU:** 4 cores (Intel i5/AMD Ryzen 5 or better)
- **RAM:** 8 GB
- **Storage:** 20 GB available
- **OS:** Windows 10+, macOS 12+, or Linux (Ubuntu 20.04+)
- **Python:** 3.10, 3.11, or 3.12

### Do I need a GPU?

No. SecureVision is designed to work on CPU-only systems. A GPU (NVIDIA with CUDA) can improve performance but is entirely optional.

### How many cameras can I run on one computer?

It depends on your hardware:
- **Entry system (4-core, 8GB RAM):** 1-2 cameras
- **Mid-range system (8-core, 16GB RAM):** 3-5 cameras
- **High-end system (16+ cores, 32GB RAM):** 6-10+ cameras

You can also run multiple SecureVision instances across different computers.

### Does SecureVision work on Raspberry Pi?

Potentially, but not officially supported. A Raspberry Pi 4 with 8GB RAM might handle 1 camera at low FPS. Performance will be limited.

## Camera Compatibility

### What types of cameras does SecureVision support?

- **USB webcams** (built-in laptop cameras, USB cameras)
- **RTSP network cameras** (most IP cameras)
- **HTTP MJPEG streams**
- **RTMP streams**
- **Video files** (MP4, AVI, MKV, MOV)

### Do I need a special camera?

No. Any camera that provides a standard video stream works. Most modern IP cameras support RTSP.

### How do I find my camera's RTSP URL?

Check your camera's documentation or manufacturer website. Common patterns:

- **Generic:** `rtsp://username:password@camera-ip:554/stream`
- **Hikvision:** `rtsp://username:password@camera-ip:554/Streaming/Channels/101`
- **Dahua:** `rtsp://username:password@camera-ip:554/cam/realmonitor?channel=1&subtype=0`
- **Reolink:** `rtsp://username:password@camera-ip:554/h264Preview_01_main`

### Can SecureVision work with WiFi cameras?

Yes, but wired (Ethernet) connection is strongly recommended for reliability. WiFi cameras may experience:
- Connection drops
- Increased latency
- Bandwidth limitations

## Face Recognition

### Does SecureVision require training face recognition models?

No! SecureVision uses pre-trained InsightFace models. You simply provide photos of people you want to recognize (no training needed).

### How many photos do I need per person?

**Recommended:** 3-5 clear, front-facing photos with good lighting.

More photos improve accuracy, but quality matters more than quantity.

### Can SecureVision recognize faces through masks?

Partially. Face masks significantly reduce recognition accuracy since they cover key facial features. Performance depends on:
- Mask coverage (surgical mask vs. N95)
- Eye visibility
- Photo gallery (if gallery photos include masks)

### How accurate is face recognition?

With good quality photos and proper configuration:
- **True positive rate:** ~95% (correctly identifies known people)
- **False positive rate:** ~1-2% (incorrectly identifies strangers)

Accuracy depends on camera quality, lighting, angle, and threshold settings.

### Can I recognize multiple faces in one frame?

Yes. SecureVision can detect and recognize multiple faces simultaneously.

### What is the similarity threshold?

The similarity threshold determines how strict face matching is:
- **Lower (0.25-0.30):** Stricter matching, fewer false positives, may miss some matches
- **Default (0.35):** Balanced
- **Higher (0.40-0.50):** Looser matching, more matches, more false positives

Configure via: `SECUREVISION__FACE__SIMILARITY_THRESHOLD`

## License Plate Recognition

### What regions/countries are supported for license plates?

SecureVision supports any region where Tesseract OCR has language packs:
- **North America** (eng)
- **Europe** (deu, fra, ita, esp, etc.)
- **Cyrillic regions** (rus, ukr, bel)
- **Multi-language** (combine with +, e.g., eng+rus)

You configure the region via OCR settings.

### How accurate is license plate recognition?

Under good conditions (clear view, good lighting):
- **Detection rate:** ~90-95%
- **OCR accuracy:** ~85-90%

Multi-frame confirmation significantly improves accuracy.

### Can SecureVision read plates at night?

Yes, but you need proper lighting:
- Camera with good low-light performance
- IR illuminators (invisible to human eye)
- Headlight illumination (if vehicles are moving toward camera)

### What is the optimal distance for plate recognition?

**Optimal:** 10-30 feet (3-10 meters)
- **Too close (<10 ft):** Plate may be too large or skewed
- **Too far (>30 ft):** Plate pixels too small for reliable OCR

### Can I customize plate format validation?

Yes! Use regex patterns for your region:

US format (ABC1234):
```bash
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z]{3}[0-9]{4}"
```

EU format (XX-YY 1234):
```bash
SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z]{2}-[A-Z]{2}[0-9]{4}"
```

## Performance

### How much CPU does SecureVision use?

Per camera (720p @ 15 FPS with face + plate detection):
- **CPU:** ~1.5 cores
- **RAM:** ~2 GB

You can reduce CPU usage by:
- Lowering FPS target
- Resizing frames to lower resolution
- Disabling face or plate recognition
- Using ROI (region of interest)

### My video is slow/laggy. How can I improve performance?

1. **Reduce FPS target:** `SECUREVISION__VIDEO__FPS_TARGET=10`
2. **Resize frames:** `SECUREVISION__VIDEO__FRAME_RESIZE=1280,720`
3. **Disable unused features:** Set `FACE__ENABLED=false` or `PLATES__ENABLED=false`
4. **Use ROI:** Crop to region where plates appear
5. **Upgrade hardware:** More CPU cores, faster storage

### Does SecureVision record video?

No. SecureVision processes video in real-time and stores only:
- Detection events (timestamp, name, confidence)
- Metadata (bounding boxes, coordinates)

It does NOT store full video frames or recordings.

## Configuration

### Where are configuration files stored?

SecureVision uses environment variables (no config files by default). You can:
- Use `.env` files for local development
- Set environment variables directly
- Use example templates in `examples/env/`

### How do I change the camera source?

Edit environment variables:

```bash
# From USB camera to RTSP
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://camera:554/stream
```

### Can I use multiple configuration profiles?

Yes. Create different `.env` files:

```bash
# Front door camera
source front-door.env
poetry run securevision-qt

# Garage camera
source garage.env
poetry run securevision-qt
```

### How do I disable face or plate recognition?

```bash
# Disable face recognition
SECUREVISION__FACE__ENABLED=false

# Disable plate recognition
SECUREVISION__PLATES__ENABLED=false
```

## Events and Data

### Where are events stored?

In a local SQLite database at `data/events.db` (configurable).

### How long are events retained?

Default: 30 days. Configure with:

```bash
SECUREVISION__EVENTS__RETENTION_DAYS=90  # Keep for 90 days
```

Old events are automatically deleted.

### Can I export events?

Yes. Events are stored in SQLite, which you can query:

```bash
sqlite3 data/events.db "SELECT * FROM events ORDER BY ts_ms DESC LIMIT 100"
```

Or use the REST API to fetch events as JSON.

### How do I manually delete old events?

Via API:
```bash
curl -X POST http://localhost:8000/cleanup
```

Or delete database and restart:
```bash
rm data/events.db
```

## API and Integration

### Does SecureVision have an API?

Yes! SecureVision includes:
- **REST API** for querying events
- **WebSocket API** for live event streaming

See [API.md](API.md) for complete documentation.

### Can I integrate SecureVision with home automation?

Yes. Use the WebSocket API to receive real-time events and trigger automations (e.g., Home Assistant, Node-RED).

Example:
```javascript
const ws = new WebSocket('ws://localhost:8000/stream');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'face_match' && data.payload.person_name === 'john_doe') {
    // Trigger: Unlock door, turn on lights, etc.
  }
};
```

### Is the API authenticated?

Optional. Configure bearer token authentication:

```bash
SECUREVISION__API__AUTH_TOKEN=your-secret-token
```

### Can I access the API remotely?

Yes, but **not recommended** without proper security:
- Use VPN (WireGuard, OpenVPN)
- Use reverse proxy with HTTPS (Nginx + Let's Encrypt)
- Enable authentication
- Restrict firewall rules

## Privacy and Security

### Is my data sent to the cloud?

**No.** All processing and storage happens locally. SecureVision never sends data to external servers.

### How secure is SecureVision?

SecureVision is designed with privacy in mind:
- Local processing only
- No external API calls
- Optional authentication for API
- Open-source code (auditable)

However, **you are responsible for:**
- Securing your network
- Using strong camera passwords
- Enabling API authentication
- Following local surveillance laws

### Can I run SecureVision without internet?

Yes. After initial installation, SecureVision works completely offline.

### Does SecureVision comply with GDPR?

SecureVision itself is GDPR-compliant as a tool (no data leaves your control). However, **you** must ensure GDPR compliance when using it:
- Inform individuals about surveillance (signage)
- Document legal basis for processing
- Limit data retention
- Provide data access/deletion on request

Consult legal counsel for specific requirements.

## Troubleshooting

### SecureVision won't start. What should I check?

1. **Python version:** Must be 3.10, 3.11, or 3.12
2. **Dependencies:** Run `poetry install`
3. **Camera access:** Check camera permissions (macOS/Linux)
4. **Port availability:** Ensure port 8000 is not in use
5. **Logs:** Check error messages in terminal

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

### My camera won't connect. What should I do?

1. **Test camera separately:**
   ```bash
   ffplay rtsp://user:pass@camera-ip:554/stream
   ```
2. **Verify network:** Ping camera IP
3. **Check credentials:** Ensure username/password correct
4. **Try different RTSP paths:** See camera documentation
5. **Increase timeout:** `SECUREVISION__VIDEO__READ_TIMEOUT_S=10.0`

### Face recognition isn't working. Why?

1. **Check gallery:** Ensure photos are in `data/faces/trusted/`
2. **Re-enroll:** `poetry run securevision-face-enroll ./data/faces/trusted`
3. **Adjust threshold:** Try `SECUREVISION__FACE__SIMILARITY_THRESHOLD=0.40`
4. **Check lighting:** Ensure faces are well-lit
5. **Verify minimum size:** Lower `MIN_FACE_SIZE` if faces are distant

### Plate recognition returns gibberish. What's wrong?

1. **Install language pack:**
   ```bash
   sudo apt-get install tesseract-ocr-eng
   ```
2. **Configure for your region:** See [CONFIG.md](CONFIG.md)
3. **Enable preprocessing:**
   ```bash
   SECUREVISION__PLATES__OCR__ENABLE_ADAPTIVE_THRESHOLD=true
   ```
4. **Check camera angle:** Ensure plates are perpendicular
5. **Improve lighting:** Add IR illuminators for night

## Contributing

### How can I contribute to SecureVision?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Reporting bugs
- Requesting features
- Submitting code
- Improving documentation

### Where can I get help?

- **Documentation:** Check guides in repository
- **GitHub Issues:** Report bugs or ask questions
- **Discussions:** Community Q&A and ideas

### Is there a roadmap?

Yes! See [CLAUDE.md](../CLAUDE.md) for the development roadmap and planned features.

## Licensing

### Can I modify SecureVision?

Yes! SecureVision is open-source under the MIT License. You can:
- Modify the code
- Use it commercially
- Distribute modified versions

Just maintain the original license notice.

### Can I sell SecureVision?

You can sell services/support around SecureVision, but the software itself remains open-source and free.
