# SecureVision Deployment Guide

This guide covers deploying SecureVision in various environments, from local development to production deployments.

## Table of Contents

- [System Requirements](#system-requirements)
- [Deployment Options](#deployment-options)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Security Hardening](#security-hardening)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

**Hardware:**
- CPU: 4 cores (Intel i5/AMD Ryzen 5 or better)
- RAM: 8 GB
- Storage: 20 GB available space
- Network: 100 Mbps for RTSP streams

**Software:**
- OS: Linux (Ubuntu 20.04+, Debian 11+), macOS 12+, Windows 10/11
- Python: 3.10, 3.11, or 3.12 (3.13 not yet supported)
- Optional: Docker 20.10+ and Docker Compose 2.0+

### Recommended Requirements

**Hardware:**
- CPU: 8+ cores with AVX2 support
- RAM: 16 GB (32 GB for multi-camera setups)
- Storage: 100 GB SSD (faster model loading and event storage)
- GPU: Optional NVIDIA GPU with CUDA 11.8+ for acceleration
- Network: Gigabit Ethernet for multiple HD streams

**Software:**
- OS: Ubuntu 22.04 LTS or Debian 12
- Python: 3.11 (best compatibility)
- Tesseract: 5.0+ for OCR

### Per-Camera Resource Usage

Approximate resources per camera stream (720p @ 15 FPS with face + plate detection):

- CPU: ~1.5 cores
- RAM: ~2 GB
- Network: ~5 Mbps (RTSP H.264)
- Storage: ~100 MB/day (events only, not video)

## Deployment Options

### Option 1: Native Installation

Best for: Development, single machine deployments, maximum performance

- Direct Python installation via Poetry
- Full control over dependencies
- Easiest debugging
- No containerization overhead

See [Local Development](#local-development)

### Option 2: Docker Compose

Best for: Production deployments, multi-container setups, easy updates

- Isolated environment
- Easy scaling and orchestration
- Consistent across environments
- Simplified dependency management

See [Docker Deployment](#docker-deployment)

### Option 3: Systemd Service

Best for: Headless servers, automatic startup, system integration

- Native system service
- Automatic restart on failure
- Boot-time startup
- System logging integration

See [Production Deployment](#production-deployment)

## Local Development

### 1. Install Dependencies

**Install Poetry:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
# Or use pipx
pipx install poetry
```

**Install Tesseract (for plate recognition):**

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
# Add to PATH after installation
```

### 2. Clone and Setup

```bash
git clone https://github.com/yourusername/cam-vision.git
cd cam-vision

# Install dependencies
poetry install

# Install pre-commit hooks (optional, for development)
poetry run pre-commit install
```

### 3. Configuration

Create environment configuration:

```bash
# Copy example configuration
cp examples/env/complete-home.env .env

# Edit configuration
nano .env
```

See [Configuration](#configuration) section for details.

### 4. Run Application

**Desktop UI:**
```bash
set -a; source .env; set +a
poetry run securevision-qt
```

**API Server:**
```bash
set -a; source .env; set +a
poetry run securevision-api
```

**Face Enrollment:**
```bash
poetry run securevision-face-enroll /path/to/face/images
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev deps)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY cam_vision ./cam_vision
COPY data ./data
COPY weights ./weights
COPY examples ./examples

# Expose API port
EXPOSE 8000

# Run API server
CMD ["poetry", "run", "securevision-api"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  securevision-api:
    build: .
    container_name: securevision-api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./weights:/app/weights
      - ./logs:/app/logs
    environment:
      - SECUREVISION__API__HOST=0.0.0.0
      - SECUREVISION__API__PORT=8000
      - SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
      - SECUREVISION__VIDEO__SOURCE__URL=rtsp://camera:554/stream
      - SECUREVISION__FACE__ENABLED=true
      - SECUREVISION__PLATES__ENABLED=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  securevision-dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    container_name: securevision-dashboard
    ports:
      - "8501:8501"
    depends_on:
      - securevision-api
    environment:
      - SECUREVISION_API_URL=http://securevision-api:8000
    restart: unless-stopped

volumes:
  data:
  weights:
  logs:
```

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### GPU Support (Optional)

For GPU acceleration, modify `docker-compose.yml`:

```yaml
services:
  securevision-api:
    # ... existing config ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

Requires:
- NVIDIA GPU
- NVIDIA Container Toolkit installed
- CUDA-compatible base image

## Production Deployment

### 1. System User Setup

Create dedicated user for security:

```bash
sudo useradd -r -s /bin/false securevision
sudo mkdir -p /opt/securevision
sudo chown securevision:securevision /opt/securevision
```

### 2. Application Installation

```bash
cd /opt/securevision
sudo -u securevision git clone https://github.com/yourusername/cam-vision.git .
sudo -u securevision poetry install --no-dev
```

### 3. Create Systemd Service

Create `/etc/systemd/system/securevision-api.service`:

```ini
[Unit]
Description=SecureVision Events API
After=network.target

[Service]
Type=simple
User=securevision
Group=securevision
WorkingDirectory=/opt/securevision
Environment="PATH=/opt/securevision/.venv/bin:/usr/bin"
EnvironmentFile=/opt/securevision/.env
ExecStart=/opt/securevision/.venv/bin/python -m uvicorn cam_vision.api.app:create_app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/securevision/data /opt/securevision/logs

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable securevision-api

# Start service
sudo systemctl start securevision-api

# Check status
sudo systemctl status securevision-api

# View logs
sudo journalctl -u securevision-api -f
```

### 5. Reverse Proxy (Nginx)

For production, use a reverse proxy:

Create `/etc/nginx/sites-available/securevision`:

```nginx
upstream securevision {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name securevision.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name securevision.example.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/securevision.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/securevision.example.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy settings
    location / {
        proxy_pass http://securevision;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /stream {
        proxy_pass http://securevision;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/securevision-access.log;
    error_log /var/log/nginx/securevision-error.log;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/securevision /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Configuration

### Environment Variables

Create `/opt/securevision/.env`:

```bash
# Video source
SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
SECUREVISION__VIDEO__SOURCE__URL=rtsp://user:pass@192.168.1.100:554/stream
SECUREVISION__VIDEO__FPS_TARGET=15

# Face recognition
SECUREVISION__FACE__ENABLED=true
SECUREVISION__FACE__GALLERY_PATH=/opt/securevision/data/faces
SECUREVISION__FACE__THRESHOLD=0.35

# License plates
SECUREVISION__PLATES__ENABLED=true
SECUREVISION__PLATES__CONFIDENCE_THRESHOLD=0.55
SECUREVISION__PLATES__WHITELIST=/opt/securevision/data/plates/whitelist.txt
SECUREVISION__PLATES__BLACKLIST=/opt/securevision/data/plates/blacklist.txt

# API
SECUREVISION__API__HOST=0.0.0.0
SECUREVISION__API__PORT=8000
SECUREVISION__API__AUTH_TOKEN=your-secure-random-token-here
SECUREVISION__API__WS_ENABLED=true

# Events database
SECUREVISION__EVENTS__DB_URL=sqlite:////opt/securevision/data/events.db
SECUREVISION__EVENTS__RETENTION_DAYS=30
```

See [CONFIG.md](CONFIG.md) for complete configuration reference.

### Generating Secure Tokens

```bash
# Generate random auth token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Security Hardening

### 1. Network Security

**Firewall Rules:**
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS only (if using Nginx)
sudo ufw allow 443/tcp

# Deny direct API access (proxied via Nginx)
sudo ufw deny 8000/tcp

# Enable firewall
sudo ufw enable
```

**Camera Network Isolation:**
- Place cameras on separate VLAN
- Restrict internet access for cameras
- Use strong camera passwords

### 2. Application Security

**Authentication:**
```bash
# Always use auth tokens in production
export SECUREVISION__API__AUTH_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

**File Permissions:**
```bash
# Restrict data directory
sudo chown -R securevision:securevision /opt/securevision/data
sudo chmod 700 /opt/securevision/data

# Protect environment file
sudo chmod 600 /opt/securevision/.env
```

**CORS Configuration:**

Edit `cam_vision/api/app.py` to restrict origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
)
```

### 3. SSL/TLS

**Use Let's Encrypt:**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d securevision.example.com
```

**Auto-renewal:**
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Monitoring & Logging

### Application Logs

**Systemd Journal:**
```bash
# Real-time logs
sudo journalctl -u securevision-api -f

# Last 100 lines
sudo journalctl -u securevision-api -n 100

# Filter by priority
sudo journalctl -u securevision-api -p err
```

**Log Rotation:**

Create `/etc/logrotate.d/securevision`:
```
/opt/securevision/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 securevision securevision
}
```

### Health Monitoring

**Check Health Endpoint:**
```bash
curl http://localhost:8000/health
```

**Uptime Monitoring:**

Use external monitoring services:
- UptimeRobot (free tier available)
- Pingdom
- StatusCake

### Performance Metrics

**System Metrics:**
```bash
# CPU and memory usage
htop

# Disk I/O
iotop

# Network traffic
iftop
```

**Application Metrics:**

Monitor via health endpoint:
```bash
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

## Backup & Recovery

### Database Backup

**Manual Backup:**
```bash
# Stop service
sudo systemctl stop securevision-api

# Backup database
sudo -u securevision cp /opt/securevision/data/events.db \
  /opt/securevision/backups/events-$(date +%Y%m%d).db

# Start service
sudo systemctl start securevision-api
```

**Automated Backup Script:**

Create `/opt/securevision/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/opt/securevision/backups"
DB_PATH="/opt/securevision/data/events.db"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

# SQLite backup (hot backup)
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/events-$DATE.db'"

# Compress
gzip "$BACKUP_DIR/events-$DATE.db"

# Keep only last 30 days
find "$BACKUP_DIR" -name "events-*.db.gz" -mtime +30 -delete

echo "Backup completed: events-$DATE.db.gz"
```

**Cron Job:**
```bash
# Edit crontab
sudo -u securevision crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/securevision/backup.sh >> /opt/securevision/logs/backup.log 2>&1
```

### Face Gallery Backup

```bash
# Backup face gallery
sudo -u securevision tar -czf \
  /opt/securevision/backups/faces-$(date +%Y%m%d).tar.gz \
  /opt/securevision/data/faces
```

### Recovery

**Restore Database:**
```bash
sudo systemctl stop securevision-api
sudo -u securevision cp /opt/securevision/backups/events-20240101.db \
  /opt/securevision/data/events.db
sudo systemctl start securevision-api
```

## Scaling

### Vertical Scaling

**Increase Resources:**
- Add more CPU cores
- Increase RAM
- Use faster storage (NVMe SSD)
- Add GPU for acceleration

**Optimize Settings:**
```bash
# Reduce FPS for more cameras
export SECUREVISION__VIDEO__FPS_TARGET=10

# Increase worker threads (if implemented)
export SECUREVISION__API__WORKERS=4
```

### Horizontal Scaling

**Multi-Process API:**

Use Gunicorn instead of Uvicorn:
```bash
gunicorn cam_vision.api.app:create_app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**Load Balancing:**

Deploy multiple instances with Nginx load balancing:
```nginx
upstream securevision_cluster {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location / {
        proxy_pass http://securevision_cluster;
    }
}
```

**Multi-Camera Distribution:**
- Run separate instances per camera
- Use message queue (Redis, RabbitMQ) for event aggregation
- Centralized event database

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u securevision-api -n 50
```

**Common issues:**
- Missing environment file
- Database file permissions
- Port already in use
- Missing dependencies

### High CPU Usage

**Diagnosis:**
```bash
# Check per-process CPU
top -u securevision

# Profile Python process
sudo py-spy top --pid <pid>
```

**Solutions:**
- Reduce FPS target
- Disable unused features (face or plates)
- Resize video input
- Add GPU acceleration

### High Memory Usage

**Check memory:**
```bash
sudo -u securevision ps aux | grep securevision
```

**Solutions:**
- Reduce frame buffer size
- Lower camera resolution
- Enable model quantization
- Add swap space (temporary)

### Camera Connection Issues

**Test RTSP stream:**
```bash
ffplay rtsp://user:pass@camera-ip:554/stream
```

**Common fixes:**
- Verify camera credentials
- Check network connectivity
- Ensure camera is on same network
- Try different RTSP URL paths

### Database Corruption

**Verify database:**
```bash
sqlite3 /opt/securevision/data/events.db "PRAGMA integrity_check;"
```

**Recover if possible:**
```bash
sqlite3 /opt/securevision/data/events.db ".recover" | \
  sqlite3 /opt/securevision/data/events-recovered.db
```

---

## See Also

- [Configuration Reference](CONFIG.md) - Complete configuration options
- [API Documentation](API.md) - API endpoints and usage
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Detailed troubleshooting
- [User Guide](USER_GUIDE.md) - End-user documentation
