# Contributing to SecureVision

Thank you for your interest in contributing to SecureVision! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cam-vision.git
   cd cam-vision
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/michaelflppv/cam-vision.git
   ```

## Development Environment

### Requirements

- Python 3.10–3.12 (Python 3.13 not yet supported)
- Poetry for dependency management
- Pre-commit hooks for code quality
- Optional: Tesseract OCR (for plate recognition)
- Optional: GPU with CUDA (for acceleration)

### Setup

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   # Or use pipx
   pipx install poetry
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Install pre-commit hooks**:
   ```bash
   poetry run pre-commit install
   ```

4. **Verify installation**:
   ```bash
   poetry run pytest -q
   poetry run pre-commit run --all-files
   ```

## Project Structure

```
cam_vision/
  api/          # FastAPI services and WebSocket streaming
  cli/          # CLI entrypoints
  config.py     # Pydantic settings and configuration
  face/         # Face recognition models and enrollment
  io/           # Video capture and device adapters
  pipeline/     # Orchestration, state, and triggers
  plates/       # Plate detection and OCR
  qt_ui/        # PySide6 desktop application
  tracking/     # Multi-frame confirmation logic
  utils/        # Shared helpers and utilities
  types.py      # Core dataclasses and enums

data/           # Local runtime assets (faces, plates)
examples/env/   # Environment templates
tests/          # Pytest suite mirroring cam_vision/
weights/        # Pretrained model weights
```

## Development Workflow

### Branching Strategy

- **main**: Production-ready code
- **feature/\***: New features
- **fix/\***: Bug fixes
- **docs/\***: Documentation updates
- **refactor/\***: Code refactoring

### Making Changes

1. **Sync with upstream**:
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit regularly with meaningful messages

4. **Run tests and linters**:
   ```bash
   poetry run pre-commit run --all-files
   poetry run pytest
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub

## Coding Standards

### Code Style

- **Line length**: 100 characters maximum
- **Formatter**: Black
- **Import sorting**: isort (black profile)
- **Linter**: Ruff
- **Type hints**: Use type annotations for function signatures
- **Python version**: Target Python 3.10+ features

### Running Code Quality Tools

```bash
# Run all checks
poetry run pre-commit run --all-files

# Individual tools
poetry run ruff check .          # Linting
poetry run ruff check --fix .    # Auto-fix linting issues
poetry run black .               # Format code
poetry run isort .               # Sort imports
```

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Modules**: `snake_case.py`

### Code Documentation

- Add docstrings to all public modules, classes, and functions
- Use Google-style docstrings:
  ```python
  def process_frame(frame: Frame) -> list[Event]:
      """Process a single frame and emit detection events.

      Args:
          frame: Input frame to process

      Returns:
          List of events generated from detections

      Raises:
          ValueError: If frame is invalid
      """
      pass
  ```

## Testing

### Test Structure

- Tests mirror the `cam_vision/` structure in `tests/`
- Use pytest for all tests
- Maintain test coverage above 80%

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=cam_vision --cov-report=html

# Run specific test file
poetry run pytest tests/test_config.py

# Run with verbose output
poetry run pytest -v

# Run quietly
poetry run pytest -q
```

### Writing Tests

- Use descriptive test names: `test_face_detection_with_valid_image`
- Use fixtures for common setup
- Mock external dependencies (cameras, models)
- Test edge cases and error conditions

Example:
```python
def test_frame_source_handles_disconnection():
    """Test that FrameSource recovers from network disconnection."""
    # Arrange
    source = RTSPSource(url="rtsp://example.com/stream")

    # Act & Assert
    with pytest.raises(ConnectionError):
        source.read()
```

## Pull Request Process

### Before Submitting

1. **Update documentation** if adding features or changing behavior
2. **Add tests** for new functionality
3. **Run full test suite** and ensure all tests pass
4. **Update docs/CHANGELOG.md** with your changes
5. **Ensure pre-commit hooks pass**
6. **Rebase on latest main** to avoid merge conflicts

### PR Requirements

- **Title**: Clear, descriptive title (e.g., "Add multi-camera support")
- **Description**: Use the PR template (see `.github/pull_request_template.md`)
  - What changes were made
  - Why these changes were necessary
  - How to test the changes
  - Related issues (e.g., "Fixes #123")
- **Tests**: Include tests for new code
- **Documentation**: Update relevant docs
- **No breaking changes** without discussion

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why are these changes needed?

## Changes Made
- Change 1
- Change 2

## Testing
How to test these changes

## Checklist
- [ ] Tests pass locally
- [ ] Pre-commit hooks pass
- [ ] Documentation updated
- [ ] docs/CHANGELOG.md updated
- [ ] No breaking changes (or discussed in issue)
```

### Review Process

1. Maintainers will review your PR within 3-5 business days
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR
4. **Do not force push** after requesting review (makes review harder)

## Commit Message Guidelines

Follow these conventions for clear commit history:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```
feat(face): add multi-face detection support

Implement ability to detect and track multiple faces in a single frame.
Uses IoU-based tracking to maintain face identities across frames.

Closes #45

---

fix(plates): handle missing Tesseract installation gracefully

Check for Tesseract availability at runtime and provide clear error
message if not installed, rather than crashing.

---

docs(api): add OpenAPI schema examples

Add comprehensive examples to API documentation for all endpoints.
```

### Best Practices

- Use **imperative mood**: "Add feature" not "Added feature"
- Keep **subject line under 72 characters**
- Separate subject from body with a blank line
- Explain **what and why**, not how (code shows how)
- Reference issues and PRs where relevant

## Documentation

### What to Document

- **New features**: Update docs/USER_GUIDE.md, README.md, and relevant docs
- **API changes**: Update docs/API.md and OpenAPI schema
- **Configuration**: Update docs/CONFIG.md with new settings
- **Breaking changes**: Clearly document in docs/CHANGELOG.md

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams where helpful (use Mermaid for diagrams)
- Keep line length under 100 characters

### Documentation Structure

- **README.md**: Quick start and overview
- **docs/USER_GUIDE.md**: Comprehensive user documentation
- **docs/API.md**: API reference and examples
- **docs/CONFIG.md**: Configuration reference
- **docs/DEPLOYMENT.md**: Deployment and operations
- **docs/TROUBLESHOOTING.md**: Common issues and solutions

## Community

### Getting Help

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions or share ideas
- **Documentation**: Check existing docs first

### Reporting Bugs

Use the bug report template and include:

- SecureVision version
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

### Feature Requests

Use the feature request template and include:

- Use case description
- Proposed solution
- Alternative approaches considered
- Willingness to implement

### Security Issues

**Do not open public issues for security vulnerabilities.**

See [docs/SECURITY.md](docs/SECURITY.md) for responsible disclosure process.

## Recognition

Contributors will be recognized in:

- **docs/CHANGELOG.md**: For significant contributions
- **README.md**: Contributors section (if added)
- **GitHub**: Automatic contribution tracking

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SecureVision! Your efforts help make computer vision accessible and privacy-focused for everyone
