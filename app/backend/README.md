# Backend API - Task Management

## Overview

Minimal Flask API for task management with PostgreSQL integration.

## Features

- RESTful API endpoints
- PostgreSQL database integration
- Prometheus metrics export
- Health check endpoint
- Structured JSON logging
- CORS support for frontend

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create new task |
| GET | `/api/tasks/<id>` | Get specific task |
| PUT | `/api/tasks/<id>` | Update task |
| DELETE | `/api/tasks/<id>` | Delete task |

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_NAME=tasks
export DB_USER=taskapp
export DB_PASSWORD=taskpass

# Run application
python main.py
```

### Build Docker Image

```bash
# Build
docker build -t task-app-backend:1.0.0 .

# Run
docker run -p 5000:5000 \
  -e DB_HOST=postgres \
  -e DB_NAME=tasks \
  -e DB_USER=taskapp \
  -e DB_PASSWORD=taskpass \
  task-app-backend:1.0.0
```

## API Examples

### Get All Tasks
```bash
curl http://localhost:5000/api/tasks
```

### Create Task
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "From the store"}'
```

### Health Check
```bash
curl http://localhost:5000/health
```

### Metrics
```bash
curl http://localhost:5000/metrics
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | postgres | Database host |
| `DB_PORT` | 5432 | Database port |
| `DB_NAME` | tasks | Database name |
| `DB_USER` | taskapp | Database user |
| `DB_PASSWORD` | taskpass | Database password |
| `LOG_LEVEL` | INFO | Logging level |

## Database Schema

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Logging

All logs are output as JSON to stdout:

```json
{"timestamp": "2024-01-15 10:30:45,123", "level": "INFO", "message": "Retrieved 5 tasks"}
```

This enables easy integration with log aggregation systems.

## Performance

- Built with Gunicorn (production WSGI server)
- 4 worker processes
- 60-second timeout
- Health checks every 30 seconds
- Connection pooling from psycopg2

## Monitoring

Health check endpoint returns:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "database": "connected"
}
```

Metrics endpoint exports Prometheus-format metrics:
```
http_requests_total{method="GET",endpoint="/api/tasks"} 100
http_request_duration_seconds_bucket{endpoint="/api/tasks",le="0.005"} 45
```

## Troubleshooting

### Database Connection Failed
- Check DB_HOST is correct
- Verify PostgreSQL is running
- Confirm credentials (DB_USER, DB_PASSWORD)
- Check network connectivity

### 500 Internal Server Error
- Check application logs
- Verify database schema exists
- Check environment variables

### Slow Response Times
- Monitor CPU and memory usage
- Check database query performance
- Review Prometheus metrics
- Consider scaling (HPA in K8s)
