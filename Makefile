.PHONY: help install test lint format api ui qt streamlit run-all clean kill-api

# Default target
help:
	@echo "SecureVision Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make install          Install dependencies via Poetry"
	@echo "  make install-dev      Install with dev dependencies"
	@echo ""
	@echo "Running Services:"
	@echo "  make api              Start API server (port 8000)"
	@echo "  make qt               Start Qt dashboard (monochromatic UI)"
	@echo "  make streamlit        Start Streamlit dashboard (legacy)"
	@echo "  make run-all          Start API + Qt UI together"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run tests"
	@echo "  make lint             Run linting (ruff)"
	@echo "  make format           Format code (black + isort)"
	@echo "  make pre-commit       Run pre-commit hooks"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Clean cache files"
	@echo "  make kill-api         Kill API server process"
	@echo ""

# ============================================================================
# Installation
# ============================================================================

install:
	poetry install

install-dev:
	poetry install --with dev
	poetry run pre-commit install

# ============================================================================
# Run Services
# ============================================================================

api:
	@echo "Starting SecureVision API server on http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	@poetry run securevision-api

qt:
	@echo "Starting SecureVision Qt Dashboard (Monochromatic UI)"
	@poetry run securevision-qt

streamlit:
	@echo "Starting SecureVision Streamlit Dashboard (Legacy)"
	@poetry run securevision-ui

# Run API and Qt UI together
run-all:
	@echo "Starting SecureVision API + Qt Dashboard"
	@echo "========================================"
	@echo ""
	@echo "Starting API server in background..."
	@poetry run securevision-api > /tmp/securevision-api.log 2>&1 & echo $$! > /tmp/securevision-api.pid
	@sleep 2
	@echo "API server started (PID: $$(cat /tmp/securevision-api.pid))"
	@echo "API available at http://localhost:8000"
	@echo "Logs: tail -f /tmp/securevision-api.log"
	@echo ""
	@echo "Starting Qt Dashboard..."
	@poetry run securevision-qt || (make kill-api && exit 1)
	@make kill-api

# ============================================================================
# Testing & Quality
# ============================================================================

test:
	@echo "Running tests..."
	@poetry run pytest -v

test-quiet:
	@echo "Running tests (quiet mode)..."
	@poetry run pytest -q

test-coverage:
	@echo "Running tests with coverage..."
	@poetry run pytest --cov=cam_vision --cov-report=html --cov-report=term

lint:
	@echo "Running linting..."
	@poetry run ruff check .

lint-fix:
	@echo "Running linting with auto-fix..."
	@poetry run ruff check --fix .

format:
	@echo "Formatting code..."
	@poetry run black .
	@poetry run isort .

pre-commit:
	@echo "Running pre-commit hooks..."
	@poetry run pre-commit run --all-files

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "Cleaning cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "Cleanup complete"

kill-api:
	@if [ -f /tmp/securevision-api.pid ]; then \
		echo "Stopping API server (PID: $$(cat /tmp/securevision-api.pid))..."; \
		kill $$(cat /tmp/securevision-api.pid) 2>/dev/null || true; \
		rm /tmp/securevision-api.pid; \
		echo "API server stopped"; \
	else \
		echo "No API server PID file found"; \
	fi

# ============================================================================
# Additional CLI Tools
# ============================================================================

face-enroll:
	@echo "Starting face enrollment..."
	@poetry run securevision-face-enroll

preview:
	@echo "Starting lightweight preview..."
	@poetry run securevision-preview

plates:
	@echo "Starting plate recognition demo..."
	@poetry run securevision-plates

onvif-discover:
	@echo "Discovering ONVIF cameras..."
	@poetry run securevision-onvif-discover

# ============================================================================
# Docker (future)
# ============================================================================

docker-build:
	@echo "Building Docker image..."
	@docker build -t securevision:latest .

docker-run:
	@echo "Running Docker container..."
	@docker run -p 8000:8000 -p 8501:8501 securevision:latest
