# SecureVision

> Privacy-first, self-hosted computer vision for face recognition and license plate detection

SecureVision is an open-source, self-hosted computer vision platform that processes live camera feeds to identify trusted faces and license plates. All processing happens locally on your device—no cloud, no subscriptions, complete privacy.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-2b5b84)](https://www.python.org/)
[![Poetry](https://img.shields.io/badge/poetry-managed-60a5fa)](https://python-poetry.org/)
[![FastAPI](https://img.shields.io/badge/api-fastapi-009688)](https://fastapi.tiangolo.com/)
[![PySide6](https://img.shields.io/badge/ui-pyside6-4a90e2)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0b7285)](LICENSE)

## Highlights

- **Multi-source capture** - USB webcams, RTSP/HTTP network cameras, video files
- **Face recognition** - Identify trusted people using InsightFace embeddings (no training required)
- **License plate recognition** - Detect and read plates with YOLOv8 + Tesseract OCR
- **Desktop application** - Cross-platform Qt UI with live preview and event monitoring
- **REST & WebSocket API** - Real-time event streaming and integration support
- **Privacy-first** - All processing happens locally, no cloud dependencies
- **Modular design** - Easy to extend and customize for your use case

## Use Cases

- **Home Security**: Recognize family members at front door, track visitor arrivals
- **Parking Management**: Monitor authorized vehicles in garage or parking lot
- **Business Access Control**: Log employee entry/exit via face recognition
- **Property Monitoring**: Track license plates entering/leaving property
- **Smart Home Integration**: Trigger automations based on detected people or vehicles

## Requirements

**Minimum:**
- Python 3.10, 3.11, or 3.12 (3.13 not yet supported)
- 4-core CPU, 8 GB RAM, 20 GB storage
- Poetry for dependency management
- Optional: Tesseract OCR (for license plate recognition)
- Optional: YOLOv8 plate model at `weights/yolov8n_plate.pt`

**Recommended:**
- 8+ core CPU, 16 GB RAM, SSD storage
- Dedicated computer (repurposed laptop works great)
- Wired network connection for IP cameras

## Quick Start

### 1. Install Dependencies

```bash
# Install Poetry
pipx install poetry

# Install SecureVision
git clone https://github.com/yourusername/cam-vision.git
cd cam-vision
poetry install
```

### 2. Install Optional Components

**Tesseract OCR (for plate recognition):**

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 3. Choose Configuration

```bash
# For MacBook/USB webcam
cp examples/env/complete-home.env .env

# For IP camera (RTSP)
cp examples/env/rtsp-doorbell.env .env

# Edit as needed
nano .env
```

### 4. Launch Desktop Application

```bash
set -a; source .env; set +a
poetry run securevision-qt
```

The desktop app provides live camera preview with detection overlays and real-time event log.

### 5. Set Up Face Recognition (Optional)

```bash
# Create face gallery
mkdir -p data/faces/trusted/john_doe
# Add 3-5 photos of each person to their folder

# Enroll faces
poetry run securevision-face-enroll ./data/faces/trusted
```

### 6. Set Up License Plates (Optional)

```bash
# Create whitelist
echo "ABC1234,Family car" > data/plates/whitelist.csv
echo "XYZ9876,Guest pass" >> data/plates/whitelist.csv
```

## Configuration

SecureVision uses environment variables for configuration (no config files needed).

**Quick examples:**

```bash
# Video source
export SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
export SECUREVISION__VIDEO__SOURCE__URL=rtsp://user:pass@camera.local:554/stream
export SECUREVISION__VIDEO__FPS_TARGET=15

# Enable/disable features
export SECUREVISION__FACE__ENABLED=true
export SECUREVISION__PLATES__ENABLED=true

# API settings
export SECUREVISION__API__PORT=8000
export SECUREVISION__API__AUTH_TOKEN=your-secret-token
```

**Configuration templates** are available in `examples/env/` for common scenarios:
- `complete-home.env` - Full home security setup
- `rtsp-doorbell.env` - RTSP doorbell camera
- `parking-lot.env` - Parking garage monitoring
- `usb-webcam.env` - USB/MacBook webcam

See [docs/CONFIG.md](docs/CONFIG.md) for complete configuration reference.

## API & Integration

SecureVision provides REST and WebSocket APIs for integration with other systems.

### REST API

```bash
# Start API server
poetry run securevision-api

# Query recent events
curl http://localhost:8000/events?limit=20

# Get system health
curl http://localhost:8000/health
```

### WebSocket API

Real-time event streaming:

```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'face_match') {
    console.log(`Person detected: ${data.payload.person_name}`);
  } else if (data.type === 'plate_read') {
    console.log(`Plate detected: ${data.payload.plate_text}`);
  }
};
```

See [docs/API.md](docs/API.md) for complete API documentation.

## CLI Tools

SecureVision includes several command-line tools:

- `securevision-qt` - Desktop application with GUI
- `securevision-api` - REST/WebSocket API server
- `securevision-face-enroll` - Enroll faces into gallery
- `securevision-capture` - Frame capture utility
- `securevision-preview` - Video preview without GUI
- `securevision-onvif-discover` - Discover ONVIF cameras on network

## Project Structure

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
docs/           Documentation
examples/env/   Environment templates
tests/          Pytest suite mirroring cam_vision/
weights/        Pretrained model weights
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete user guide for setup and usage |
| [API Reference](docs/API.md) | REST and WebSocket API reference |
| [Configuration](docs/CONFIG.md) | Configuration options reference |
| [Deployment](docs/DEPLOYMENT.md) | Production deployment guide |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |
| [FAQ](docs/FAQ.md) | Frequently asked questions |
| [Security](docs/SECURITY.md) | Security policy and best practices |
| [Changelog](docs/CHANGELOG.md) | Version history and changes |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=cam_vision

# Run benchmarks
poetry run pytest tests/benchmarks/ --benchmark-only
```

### Code Quality

```bash
# Run all checks (linting, formatting, type checking)
poetry run pre-commit run --all-files

# Individual tools
poetry run ruff check .
poetry run black .
poetry run isort .
```

### Development Setup

```bash
# Install dependencies (including dev tools)
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## Security and Privacy

SecureVision is designed with privacy as a core principle:

- **Local processing** - All data stays on your device
- **No cloud** - No external API calls or data transmission
- **Open source** - Transparent, auditable code
- **Optional authentication** - Secure your API with bearer tokens
- **Data control** - You own and control all data

**Best Practices:**
- Never commit camera URLs or API tokens to git
- Use strong passwords for network cameras
- Enable API authentication in production
- Regularly review and clean up old events
- Follow local surveillance laws and regulations

See [docs/SECURITY.md](docs/SECURITY.md) for security policy and reporting vulnerabilities.

## Contributing

We welcome contributions! Here's how you can help:

- **Report bugs** - Open an issue with reproduction steps
- **Request features** - Share your ideas in discussions
- **Improve docs** - Fix typos, add examples, clarify instructions
- **Write tests** - Increase test coverage
- **Submit code** - Fix bugs or implement features

**Getting Started:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run tests and linters (`poetry run pytest && poetry run pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

SecureVision is released under the **MIT License**. See [LICENSE](LICENSE) for details.

You are free to:
- Use commercially
- Modify and distribute
- Use privately
- Sublicense

Under the conditions of:
- Include original license and copyright notice
- No liability or warranty

## Acknowledgments

SecureVision is built with excellent open-source projects:

- [InsightFace](https://github.com/deepinsight/insightface) - Face recognition models
- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Optical character recognition
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [PySide6](https://doc.qt.io/qtforpython/) - Qt bindings for Python
- [OpenCV](https://opencv.org/) - Computer vision library
- [Pydantic](https://pydantic.dev/) - Data validation

## Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/cam-vision/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cam-vision/discussions)
