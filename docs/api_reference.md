# InnovateOS API Reference

## Overview
InnovateOS provides a comprehensive REST API for controlling and monitoring 3D printers. This document describes all available endpoints, authentication methods, and example usage.

## Authentication
All API requests require authentication using JWT tokens. To obtain a token:

```http
POST /api/v1/auth/login
{
    "username": "your_username",
    "password": "your_password"
}
```

Include the token in subsequent requests:
```http
Authorization: Bearer <your_token>
```

## API Endpoints

### Printer Control
#### Get Printer Status
```http
GET /api/v1/printer/status
```
Returns current printer status including temperatures, positions, and active job.

#### Start Print Job
```http
POST /api/v1/printer/job
{
    "file": "model.gcode",
    "settings": {
        "temperature": 200,
        "bed_temperature": 60
    }
}
```

### File Management
#### Upload File
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data
```

#### List Files
```http
GET /api/v1/files
```

### System Control
#### Get System Info
```http
GET /api/v1/system/info
```

#### Update System
```http
POST /api/v1/system/update
```

## WebSocket API
Real-time updates are available through WebSocket connections:

```javascript
ws://your-printer:8080/ws
```

### Events
- `temperature_update`: Printer temperature changes
- `position_update`: Print head position changes
- `status_change`: Printer status changes
- `error`: Error notifications

## Rate Limits
- Authentication endpoints: 5 requests per minute
- Print control endpoints: 60 requests per minute
- File operations: 30 requests per minute

## Error Handling
All errors follow this format:
```json
{
    "error": true,
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
}
```

## SDK Examples
### Python
```python
from innovateos import InnovateClient

client = InnovateClient('http://your-printer:8080')
client.login('username', 'password')
status = client.get_printer_status()
```

### JavaScript
```javascript
import { InnovateOS } from 'innovateos-js';

const client = new InnovateOS('http://your-printer:8080');
await client.login('username', 'password');
const status = await client.getPrinterStatus();
```
