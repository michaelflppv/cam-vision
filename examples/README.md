# SecureVision Configuration Examples

This directory contains pre-configured environment variable examples for different use cases.

## Directory Structure

```
examples/
└── env/              # Environment variable configurations
    ├── Video Sources
    │   ├── video-device.env         # MacBook/USB camera
    │   ├── video-rtsp.env           # RTSP network camera
    │   ├── video-http-mjpeg.env     # HTTP MJPEG stream
    │   ├── video-file.env           # Video file (testing)
    │   └── video-processing.env     # Frame processing options
    │
    ├── Features
    │   ├── face-recognition.env     # Face recognition settings
    │   ├── alpr-basic.env           # Basic ALPR configuration
    │   ├── alpr-german.env          # German plate example
    │   ├── alpr-roi.env             # Region of Interest settings
    │   ├── tracking.env             # Multi-frame tracking
    │   └── api.env                  # Event storage and API
    │
    └── Complete Examples
        ├── complete-home.env        # Home setup (USB + faces)
        ├── complete-driveway.env    # Driveway (RTSP + plates)
        └── complete-full-stack.env  # Full deployment (API server)
```

## Using These Examples

### Quick Start

```bash
# Load a complete configuration
set -a; source examples/env/complete-home.env; set +a

# Run the application
poetry run securevision-ui
```

### Creating Custom Configuration

```bash
# Copy an example as starting point
cp examples/env/complete-home.env .env

# Edit as needed
nano .env

# Load and run
set -a; source .env; set +a
poetry run securevision-ui
```

### Combining Multiple Configs

```bash
# Load video source
source examples/env/video-rtsp.env

# Add face recognition
source examples/env/face-recognition.env

# Add tracking
source examples/env/tracking.env

# Add API server
source examples/env/api.env

# Run
poetry run securevision-api
```

## Configuration Tips

**Video Sources:**
- Use `video-device.env` for local development with MacBook camera
- Use `video-rtsp.env` for outdoor cameras (driveway, parking)
- Use `video-file.env` for testing with recorded video

**Features:**
- Enable face recognition for indoor monitoring
- Enable ALPR for vehicle monitoring
- Enable both for comprehensive surveillance

**Tracking:**
- Default settings work well for most use cases
- Increase `FRAMES_REQUIRED` for more conservative confirmation
- Decrease `COOLDOWN_SECONDS` for high-security scenarios

**API Server:**
- Use `127.0.0.1` for local-only access
- Use `0.0.0.0` to allow network access
- Always set `AUTH_TOKEN` for production deployments

## Regional Customization

**US Plates:**
```bash
export SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z0-9]{6,7}"
```

**EU Plates:**
```bash
export SECUREVISION__PLATES__POSTPROCESS__REGEX="[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,2}"
```

**German Plates:**
See `examples/env/alpr-german.env` for full configuration including Tesseract language settings.

## Troubleshooting

**Configuration not loading:**
- Ensure you use `set -a` before sourcing: `set -a; source config.env; set +a`
- Verify environment variables: `env | grep SECUREVISION`

**Invalid configuration:**
- Check for typos in variable names (case-sensitive)
- Ensure URLs include protocol (rtsp://, http://)
- Verify file paths are absolute or relative to project root

**Feature not working:**
- Check model/gallery files exist at configured paths
- Verify Tesseract is installed for ALPR
- Review logs for specific error messages

## More Information

See main [README.md](../README.md) for:
- Installation instructions
- Feature setup guides
- API documentation
- Dashboard usage
- Development guidelines
