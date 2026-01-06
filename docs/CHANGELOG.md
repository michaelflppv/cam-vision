# Changelog

All notable changes to SecureVision will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- WebSocket authentication support
- Rate limiting for API endpoints
- GPU acceleration support (CUDA)
- Enhanced multi-camera coordination
- Video clip export for events
- Advanced tracking algorithms (DeepSORT)
- Mobile app (iOS/Android)
- Cloud backup integration (optional)

## [0.1.0] - 2024-01-01

### Added
- Initial release of SecureVision
- Core computer vision pipeline architecture
- Face recognition using InsightFace embeddings
- License plate detection using YOLOv8
- License plate OCR using Tesseract
- Multi-source video capture (USB, RTSP, HTTP MJPEG, file)
- Event storage with SQLite database
- REST API for event queries
- WebSocket API for real-time event streaming
- Multi-frame tracking and confirmation logic
- PySide6 desktop application with live preview
- Configuration via environment variables
- Pydantic-based settings validation
- Face enrollment CLI tool
- ONVIF camera discovery utility
- Comprehensive test suite
- Performance benchmarking tools
- Interactive Jupyter notebook for analysis
- Docker support (Dockerfile)
- Systemd service integration
- Complete documentation suite:
  - README.md - Project overview
  - USER_GUIDE.md - End-user documentation
  - API.md - API reference
  - CONFIG.md - Configuration reference
  - DEPLOYMENT.md - Deployment guide
  - TROUBLESHOOTING.md - Troubleshooting guide
  - FAQ.md - Frequently asked questions
  - CONTRIBUTING.md - Contribution guidelines
  - SECURITY.md - Security policy
  - CLAUDE.md - Developer/AI assistant guide
  - AGENTS.md - Repository guidelines
  - BENCHMARKING_QUICKSTART.md - Performance testing
  - CODE_OF_CONDUCT.md - Community guidelines

### Features

#### Video Processing
- Support for multiple video sources (device, RTSP, HTTP, file, RTMP)
- Configurable FPS targeting with frame dropping
- Frame resizing and rotation
- Network stream reconnection handling
- Timeout configuration for network sources

#### Face Recognition
- InsightFace-based face detection and recognition
- Face gallery management with enrollment tool
- Adjustable similarity thresholds
- Minimum face size filtering
- Pre-computed embedding cache
- Multiple photos per person support

#### License Plate Recognition
- YOLOv8-based plate detection
- Tesseract OCR with multi-language support (Latin, Cyrillic)
- Configurable preprocessing pipeline
- Region-specific validation (US, EU, etc.)
- Whitelist and blacklist management
- ROI (Region of Interest) cropping
- Plate format validation with regex

#### Event Management
- SQLite-based event storage
- Configurable retention period
- Automatic cleanup of old events
- Event querying with filters (type, timestamp, limit)
- Unique event deduplication

#### Tracking
- IoU-based multi-frame confirmation
- Configurable confirmation thresholds
- Cooldown period for duplicate events
- Track aging and cleanup
- OCR text agreement validation

#### API
- FastAPI-based REST API
- WebSocket streaming for real-time events
- Optional bearer token authentication
- CORS middleware support
- Health check endpoint with metrics
- OpenAPI/Swagger documentation

#### Desktop Application
- Qt-based GUI with PySide6
- Live video preview with detection overlays
- Event log display
- Start/Stop controls
- Asynchronous video processing

#### CLI Tools
- `securevision-capture` - Frame capture utility
- `securevision-face-enroll` - Face enrollment
- `securevision-face-demo` - Face recognition demo
- `securevision-preview` - Video preview
- `securevision-plates` - Plate recognition demo
- `securevision-api` - API server
- `securevision-qt` - Desktop application
- `securevision-onvif-discover` - ONVIF camera discovery

### Developer Experience
- Poetry-based dependency management
- Pre-commit hooks (ruff, black, isort)
- Comprehensive pytest test suite
- Type hints throughout codebase
- Modular, extensible architecture
- GitHub Actions CI/CD workflows
- Benchmarking infrastructure
- Code coverage reporting

### Documentation
- Complete user guide for non-technical users
- API documentation with examples (Python, JavaScript)
- Configuration reference with all options
- Deployment guide for production use
- Troubleshooting guide with common issues
- FAQ covering common questions
- Security policy and best practices
- Contributing guidelines
- Architectural documentation for developers

### Configuration
- Environment-based configuration (no config files)
- Nested settings with double-underscore delimiter
- Pydantic validation with clear error messages
- Example configuration templates for common scenarios
- Support for .env files

### Security
- Local-only processing (no cloud)
- Optional API authentication
- Configurable CORS policies
- Input validation via Pydantic
- SQL injection protection
- Secure default settings

## [0.0.1] - 2023-12-01

### Added
- Project scaffolding
- Basic repository structure
- Initial dependencies setup
- CI/CD pipeline setup
- Pre-commit hooks configuration
- License (MIT)
- Initial README

---

## Release Notes

### Version 0.1.0 Notes

This is the first production-ready release of SecureVision. It includes all core functionality:
- Face recognition with InsightFace
- License plate detection and OCR
- Multi-source video capture
- Event storage and API
- Desktop application
- Comprehensive documentation

**Breaking Changes:** None (initial release)

**Migration Guide:** N/A (initial release)

**Known Issues:**
- WebSocket endpoint does not require authentication (planned for 0.2.0)
- No built-in rate limiting (planned for 0.2.0)
- GPU acceleration not yet supported (planned for 0.3.0)
- Raspberry Pi not officially supported (limited testing)

**Upgrade Instructions:** N/A (initial release)

### Version 0.0.1 Notes

Early development scaffolding. Not for production use.

---

## Versioning Strategy

SecureVision follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New functionality (backward-compatible)
- **PATCH** version (0.0.X): Bug fixes (backward-compatible)

### Pre-release Versions

- **Alpha** (0.X.0-alpha.Y): Early testing, unstable
- **Beta** (0.X.0-beta.Y): Feature-complete, testing
- **RC** (0.X.0-rc.Y): Release candidate, final testing

## Deprecation Policy

- Features marked as deprecated will be supported for at least 2 minor versions
- Deprecation warnings will be logged
- Migration guides will be provided
- Breaking changes will only occur in major version updates

## How to Upgrade

### From 0.0.x to 0.1.0

This is the first production release. Follow installation instructions in [README.md](../README.md).

### Future Upgrades

```bash
# Update codebase
git pull origin main

# Update dependencies
poetry install

# Check for configuration changes
cat CHANGELOG.md

# Restart services
sudo systemctl restart securevision-api
```

## Contributing to Changelog

When contributing, please update this changelog:

1. Add your changes to the **[Unreleased]** section
2. Categorize changes:
   - **Added**: New features
   - **Changed**: Changes to existing functionality
   - **Deprecated**: Soon-to-be removed features
   - **Removed**: Removed features
   - **Fixed**: Bug fixes
   - **Security**: Security improvements

3. Format: `- Description (PR #123, @username)`

Example:
```markdown
### Added
- GPU acceleration support for YOLOv8 detection (PR #45, @johndoe)

### Fixed
- RTSP reconnection handling on network timeout (PR #46, @janedoe)
```

## Links

- [Repository](https://github.com/yourusername/cam-vision)
- [Documentation](https://github.com/yourusername/cam-vision/tree/main/docs)
- [Issues](https://github.com/yourusername/cam-vision/issues)
- [Releases](https://github.com/yourusername/cam-vision/releases)

---

**Note:** Dates and version numbers are examples. Actual releases will follow the project's release schedule.
