# SecureVision API Documentation

This document provides comprehensive documentation for the SecureVision Events API, including REST endpoints and WebSocket streaming.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [REST API Endpoints](#rest-api-endpoints)
  - [Root & Health](#root--health)
  - [Events](#events)
  - [Face Matches](#face-matches)
  - [Plate Reads](#plate-reads)
  - [Cleanup](#cleanup)
- [WebSocket API](#websocket-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The SecureVision Events API provides REST and WebSocket interfaces for:
- Querying face recognition and license plate detection events
- Real-time event streaming via WebSocket
- System health monitoring and metrics
- Event retention management

**API Version:** 0.1.0

**Technology Stack:**
- Framework: FastAPI
- Database: SQLite (via EventStore)
- WebSocket: Native WebSocket support
- Authentication: Bearer token (optional)

## Authentication

### Bearer Token Authentication

Authentication is optional and configured via environment variables. When enabled, most endpoints require a Bearer token in the Authorization header.

**Configuration:**
```bash
export SECUREVISION__API__AUTH_TOKEN="your-secret-token-here"
```

**Making Authenticated Requests:**
```bash
curl -H "Authorization: Bearer your-secret-token-here" \
  http://localhost:8000/events
```

**Public Endpoints** (no auth required):
- `GET /` - Root info
- `GET /health` - Health check

**Protected Endpoints** (auth required when enabled):
- `GET /events` - Query events
- `GET /faces/{event_id}` - Get face match
- `GET /plates/{event_id}` - Get plate read
- `POST /cleanup` - Trigger cleanup

**Note:** WebSocket endpoint (`/stream`) currently does not require authentication. Add authentication if deploying publicly.

## Base URL

Default local development:
```
http://localhost:8000
```

Configure host and port via environment:
```bash
export SECUREVISION__API__HOST="0.0.0.0"
export SECUREVISION__API__PORT="8000"
```

## REST API Endpoints

### Root & Health

#### GET /

Basic service information.

**Response:**
```json
{
  "service": "SecureVision Events API",
  "version": "0.1.0",
  "ws_enabled": true,
  "auth_enabled": false
}
```

**Example:**
```bash
curl http://localhost:8000/
```

---

#### GET /health

Comprehensive health check with system metrics and event statistics.

**Response:**
```json
{
  "ok": true,
  "timestamp": 1704067200000,
  "service": "SecureVision Events API",
  "version": "0.1.0",
  "ws_clients": 2,
  "recent_events": {
    "total": 42,
    "face_matches": 15,
    "plate_reads": 27
  },
  "event_rate": {
    "events_per_second": 0.14,
    "sample_duration_seconds": 300.0
  }
}
```

**Fields:**
- `ok` (boolean): Overall health status
- `timestamp` (int): Current server time in milliseconds
- `ws_clients` (int): Number of connected WebSocket clients
- `recent_events` (object): Event counts from last 5 minutes
  - `total`: Total events
  - `face_matches`: Face recognition events
  - `plate_reads`: License plate events
- `event_rate` (object): Processing rate metrics
  - `events_per_second`: Average event rate
  - `sample_duration_seconds`: Measurement window

**Example:**
```bash
curl http://localhost:8000/health
```

---

### Events

#### GET /events

Query events with optional filtering.

**Authentication:** Required (if enabled)

**Query Parameters:**
- `type` (optional): Filter by event type
  - Values: `face_match` or `plate_read`
- `since` (optional): Only return events after this timestamp (milliseconds)
- `limit` (optional): Maximum events to return
  - Default: 100
  - Range: 1-1000

**Response:**
```json
[
  {
    "id": 123,
    "type": "face_match",
    "ts_ms": 1704067200000,
    "frame_source_id": "camera_front_door",
    "created_at": "2024-01-01T00:00:00",
    "payload": {
      "person_name": "John Doe",
      "similarity": 0.92,
      "bbox": [100, 150, 250, 300]
    }
  },
  {
    "id": 124,
    "type": "plate_read",
    "ts_ms": 1704067205000,
    "frame_source_id": "camera_driveway",
    "created_at": "2024-01-01T00:00:05",
    "payload": {
      "plate_text": "ABC1234",
      "confidence": 0.88,
      "region": "US-CA",
      "list_match": "whitelist"
    }
  }
]
```

**Examples:**

Get all recent events:
```bash
curl -H "Authorization: Bearer token" \
  http://localhost:8000/events?limit=50
```

Get only face matches:
```bash
curl -H "Authorization: Bearer token" \
  "http://localhost:8000/events?type=face_match&limit=100"
```

Get events since timestamp:
```bash
curl -H "Authorization: Bearer token" \
  "http://localhost:8000/events?since=1704067200000"
```

Get recent plate reads:
```bash
curl -H "Authorization: Bearer token" \
  "http://localhost:8000/events?type=plate_read&since=1704067200000&limit=20"
```

---

### Face Matches

#### GET /faces/{event_id}

Retrieve a specific face match event by ID.

**Authentication:** Required (if enabled)

**Path Parameters:**
- `event_id` (int): Event ID

**Response:**
```json
{
  "id": 123,
  "type": "face_match",
  "ts_ms": 1704067200000,
  "frame_source_id": "camera_front_door",
  "created_at": "2024-01-01T00:00:00",
  "payload": {
    "person_name": "John Doe",
    "similarity": 0.92,
    "bbox": [100, 150, 250, 300],
    "embedding_distance": 0.35
  }
}
```

**Payload Fields:**
- `person_name` (string): Matched person's name from gallery
- `similarity` (float): Similarity score (0.0-1.0, higher is better)
- `bbox` (array): Bounding box [x1, y1, x2, y2]
- `embedding_distance` (float): Face embedding distance (lower is better)

**Error Responses:**
- `404 Not Found`: Event ID does not exist or is not a face match

**Example:**
```bash
curl -H "Authorization: Bearer token" \
  http://localhost:8000/faces/123
```

---

### Plate Reads

#### GET /plates/{event_id}

Retrieve a specific license plate read event by ID.

**Authentication:** Required (if enabled)

**Path Parameters:**
- `event_id` (int): Event ID

**Response:**
```json
{
  "id": 124,
  "type": "plate_read",
  "ts_ms": 1704067205000,
  "frame_source_id": "camera_driveway",
  "created_at": "2024-01-01T00:00:05",
  "payload": {
    "plate_text": "ABC1234",
    "confidence": 0.88,
    "region": "US-CA",
    "list_match": "whitelist",
    "bbox": [300, 400, 450, 480]
  }
}
```

**Payload Fields:**
- `plate_text` (string): OCR'd license plate text
- `confidence` (float): OCR confidence score (0.0-1.0)
- `region` (string): Detected plate region (e.g., "US-CA", "EU-DE")
- `list_match` (string): Match status
  - Values: `"whitelist"`, `"blacklist"`, or `null`
- `bbox` (array): Bounding box [x1, y1, x2, y2]

**Error Responses:**
- `404 Not Found`: Event ID does not exist or is not a plate read

**Example:**
```bash
curl -H "Authorization: Bearer token" \
  http://localhost:8000/plates/124
```

---

### Cleanup

#### POST /cleanup

Manually trigger cleanup of old events based on retention policy.

**Authentication:** Required (if enabled)

**Description:**
Deletes events older than the configured retention period. Typically runs as a background task, but can be triggered manually for testing or immediate cleanup.

**Response:**
```json
{
  "deleted": 150,
  "retention_days": 30
}
```

**Fields:**
- `deleted` (int): Number of events deleted
- `retention_days` (int): Configured retention period

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer token" \
  http://localhost:8000/cleanup
```

**Configuration:**
```bash
export SECUREVISION__EVENTS__RETENTION_DAYS=30
```

---

## WebSocket API

### WebSocket /stream

Real-time event streaming endpoint.

**URL:** `ws://localhost:8000/stream`

**Authentication:** Currently not required (add if deploying publicly)

**Protocol:**
1. Client connects to WebSocket endpoint
2. Server accepts connection
3. Server pushes events as JSON messages when they occur
4. Client can send ping messages, server responds with pong

**Event Message Format:**
```json
{
  "type": "face_match",
  "id": 125,
  "ts_ms": 1704067210000,
  "frame_source_id": "camera_front_door",
  "payload": {
    "person_name": "Jane Smith",
    "similarity": 0.95,
    "bbox": [120, 160, 270, 320]
  }
}
```

**Keep-Alive (Ping/Pong):**
```javascript
// Client sends
ws.send("ping");

// Server responds
{
  "type": "pong",
  "data": "ping"
}
```

**Example Client (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onopen = () => {
  console.log('Connected to SecureVision stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'face_match') {
    console.log(`Face detected: ${data.payload.person_name}`);
  } else if (data.type === 'plate_read') {
    console.log(`Plate detected: ${data.payload.plate_text}`);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from stream');
};

// Keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  }
}, 30000); // Every 30 seconds
```

**Example Client (Python):**
```python
import asyncio
import websockets
import json

async def stream_events():
    uri = "ws://localhost:8000/stream"

    async with websockets.connect(uri) as websocket:
        print("Connected to SecureVision stream")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if data.get("type") == "face_match":
                    name = data["payload"]["person_name"]
                    print(f"Face detected: {name}")
                elif data.get("type") == "plate_read":
                    plate = data["payload"]["plate_text"]
                    print(f"Plate detected: {plate}")

            except websockets.ConnectionClosed:
                print("Connection closed")
                break

asyncio.run(stream_events())
```

**Connection Limits:**
- No hard limit on concurrent connections
- Monitor connection count via `GET /health` endpoint

**Error Codes:**
- `1008`: WebSocket not enabled (check configuration)

**Configuration:**
```bash
export SECUREVISION__API__WS_ENABLED=true
```

---

## Data Models

### Event

Base event model for all event types.

```typescript
interface Event {
  id: number;                    // Unique event ID
  type: "face_match" | "plate_read";  // Event type
  ts_ms: number;                 // Event timestamp (milliseconds)
  frame_source_id: string;       // Camera/source identifier
  created_at: string;            // ISO 8601 timestamp
  payload: FaceMatchPayload | PlateReadPayload;
}
```

### FaceMatchPayload

Face recognition event payload.

```typescript
interface FaceMatchPayload {
  person_name: string;           // Matched person's name
  similarity: number;            // Similarity score (0.0-1.0)
  bbox: [number, number, number, number];  // [x1, y1, x2, y2]
  embedding_distance?: number;   // Face embedding distance
}
```

### PlateReadPayload

License plate detection event payload.

```typescript
interface PlateReadPayload {
  plate_text: string;            // OCR'd plate text
  confidence: number;            // OCR confidence (0.0-1.0)
  region: string;                // Plate region (e.g., "US-CA")
  list_match: "whitelist" | "blacklist" | null;
  bbox: [number, number, number, number];  // [x1, y1, x2, y2]
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Resource not found (event ID does not exist)
- `500 Internal Server Error`: Server error (database unavailable, etc.)
- `501 Not Implemented`: Feature not implemented

### Error Response Format

```json
{
  "detail": "Authentication required"
}
```

### Common Errors

**401 Unauthorized**
```json
{
  "detail": "Authentication required"
}
```
Solution: Include Bearer token in Authorization header.

**404 Not Found**
```json
{
  "detail": "Face match event not found"
}
```
Solution: Verify event ID exists and is the correct type.

**500 Internal Server Error**
```json
{
  "detail": "Event store not initialized"
}
```
Solution: Check server logs, ensure database is accessible.

---

## Rate Limiting

**Current Status:** No rate limiting implemented.

**Recommendations for Production:**
- Implement rate limiting per IP address
- Typical limit: 100 requests/minute for REST API
- Monitor via middleware (e.g., slowapi)

---

## Examples

### Complete Integration Example (Python)

```python
import requests
import json
from datetime import datetime, timedelta

class SecureVisionClient:
    """Client for SecureVision Events API."""

    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get_health(self):
        """Get system health and metrics."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_events(self, event_type=None, since_ms=None, limit=100):
        """Query events with filters."""
        params = {"limit": limit}
        if event_type:
            params["type"] = event_type
        if since_ms:
            params["since"] = since_ms

        response = requests.get(
            f"{self.base_url}/events",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def get_recent_face_matches(self, minutes=5):
        """Get face matches from last N minutes."""
        since_ms = int((datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)
        return self.get_events(event_type="face_match", since_ms=since_ms)

    def get_recent_plate_reads(self, minutes=5):
        """Get plate reads from last N minutes."""
        since_ms = int((datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)
        return self.get_events(event_type="plate_read", since_ms=since_ms)

    def cleanup_old_events(self):
        """Trigger manual cleanup of old events."""
        response = requests.post(
            f"{self.base_url}/cleanup",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SecureVisionClient(token="your-token-here")

# Check system health
health = client.get_health()
print(f"System OK: {health['ok']}")
print(f"Events/second: {health.get('event_rate', {}).get('events_per_second', 0):.2f}")

# Get recent face matches
faces = client.get_recent_face_matches(minutes=10)
for event in faces:
    name = event['payload']['person_name']
    similarity = event['payload']['similarity']
    print(f"Face: {name} (similarity: {similarity:.2f})")

# Get recent plate reads
plates = client.get_recent_plate_reads(minutes=10)
for event in plates:
    plate_text = event['payload']['plate_text']
    list_match = event['payload'].get('list_match', 'unknown')
    print(f"Plate: {plate_text} ({list_match})")
```

### Complete Integration Example (JavaScript/Node.js)

```javascript
const axios = require('axios');

class SecureVisionClient {
  constructor(baseUrl = 'http://localhost:8000', token = null) {
    this.baseUrl = baseUrl;
    this.headers = {};
    if (token) {
      this.headers['Authorization'] = `Bearer ${token}`;
    }
  }

  async getHealth() {
    const response = await axios.get(`${this.baseUrl}/health`);
    return response.data;
  }

  async getEvents(options = {}) {
    const { type, since, limit = 100 } = options;
    const params = { limit };
    if (type) params.type = type;
    if (since) params.since = since;

    const response = await axios.get(`${this.baseUrl}/events`, {
      headers: this.headers,
      params
    });
    return response.data;
  }

  async getRecentFaceMatches(minutes = 5) {
    const since = Date.now() - minutes * 60 * 1000;
    return this.getEvents({ type: 'face_match', since });
  }

  async getRecentPlateReads(minutes = 5) {
    const since = Date.now() - minutes * 60 * 1000;
    return this.getEvents({ type: 'plate_read', since });
  }

  async cleanupOldEvents() {
    const response = await axios.post(`${this.baseUrl}/cleanup`, null, {
      headers: this.headers
    });
    return response.data;
  }
}

// Usage
const client = new SecureVisionClient('http://localhost:8000', 'your-token-here');

(async () => {
  // Check health
  const health = await client.getHealth();
  console.log(`System OK: ${health.ok}`);

  // Get recent faces
  const faces = await client.getRecentFaceMatches(10);
  faces.forEach(event => {
    const { person_name, similarity } = event.payload;
    console.log(`Face: ${person_name} (similarity: ${similarity.toFixed(2)})`);
  });

  // Get recent plates
  const plates = await client.getRecentPlateReads(10);
  plates.forEach(event => {
    const { plate_text, list_match } = event.payload;
    console.log(`Plate: ${plate_text} (${list_match || 'unknown'})`);
  });
})();
```

---

## OpenAPI Schema

The API provides an interactive OpenAPI (Swagger) documentation at:

```
http://localhost:8000/docs
```

Alternative ReDoc documentation:

```
http://localhost:8000/redoc
```

Download OpenAPI JSON schema:

```
http://localhost:8000/openapi.json
```

---

## Configuration Reference

### API Settings

```bash
# API server configuration
export SECUREVISION__API__HOST="0.0.0.0"           # Default: 127.0.0.1
export SECUREVISION__API__PORT="8000"              # Default: 8000
export SECUREVISION__API__WS_ENABLED=true          # Enable WebSocket (default: true)
export SECUREVISION__API__AUTH_TOKEN="secret"      # Optional bearer token

# Event storage
export SECUREVISION__EVENTS__DB_URL="sqlite:///data/events.db"  # Database URL
export SECUREVISION__EVENTS__RETENTION_DAYS=30     # Event retention period
```

See [CONFIG.md](CONFIG.md) for complete configuration reference.

---

## See Also

- [User Guide](USER_GUIDE.md) - End-user documentation
- [Configuration Reference](CONFIG.md) - Complete configuration options
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
