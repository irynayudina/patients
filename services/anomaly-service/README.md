# Anomaly Detection Service

A FastAPI service that hosts a gRPC server for scoring vital signs and detecting anomalies using z-score based analysis with rolling baselines.

## Overview

This service implements the `AnomalyDetection` gRPC service defined in `proto/anomaly.proto`. It provides:

- **ScoreVitals**: Scores vital signs (HR, SpO2, Temperature) for anomalies
- **Z-score based detection**: Uses rolling baselines per patient to compute z-scores
- **Baseline storage**: Stores patient baselines in Redis (or in-memory as fallback)
- **Health endpoint**: FastAPI `/health` endpoint for service health checks

## Features

- **Rolling baselines**: Maintains per-patient baselines for each vital sign
- **Z-score calculation**: Computes z-scores against patient-specific baselines
- **Insufficient history handling**: Returns low scores when baseline data is insufficient
- **Redis integration**: Uses Redis for persistent baseline storage (configurable)
- **In-memory fallback**: Falls back to in-memory storage if Redis is unavailable

## Architecture

```
┌─────────────────┐
│   FastAPI App   │  ← HTTP /health endpoint
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
┌────────▼────────┐  ┌─────▼──────────┐
│  gRPC Server    │  │ Scoring Service │
│  (Port 50053)   │  │                 │
└─────────────────┘  └────────┬────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Baseline Store    │
                    │  (Redis or Memory)  │
                    └─────────────────────┘
```

## Configuration

Environment variables:

- `PORT`: FastAPI HTTP port (default: 8003)
- `GRPC_PORT`: gRPC server port (default: 50053)
- `REDIS_ENABLED`: Enable Redis for baseline storage (default: true)
- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password (default: redis)
- `BASELINE_WINDOW_SIZE`: Number of measurements to keep in baseline (default: 100)
- `MIN_BASELINE_SAMPLES`: Minimum samples required for scoring (default: 10)

## Scoring Algorithm

### Z-Score Calculation

For each vital sign measurement:
1. Retrieve patient's baseline (mean and standard deviation)
2. Calculate z-score: `z = |value - mean| / std_dev`
3. Map z-score to anomaly score (0-1):
   - z ≤ 1.0: score 0.0-0.2 (normal)
   - z ≤ 2.0: score 0.2-0.4 (low severity)
   - z ≤ 3.0: score 0.4-0.6 (medium severity)
   - z ≤ 4.0: score 0.6-0.8 (high severity)
   - z > 4.0: score 0.8-1.0 (critical)

### Insufficient History

When a patient has fewer than `MIN_BASELINE_SAMPLES` measurements:
- Returns a low-moderate score (0.2-0.5)
- Falls back to normal range checks if available
- Adds measurement to baseline for future calculations

### Overall Score

The overall risk score is a weighted average:
- Heart Rate: 35%
- SpO2: 35%
- Temperature: 30%

## API

### gRPC Service

**Service**: `anomaly.AnomalyDetection`

**Method**: `ScoreVitals`

**Request**:
```protobuf
message ScoreVitalsRequest {
  string patient_id = 2;
  VitalSigns vitals = 5;
  // ... other fields
}
```

**Response**:
```protobuf
message ScoreVitalsResponse {
  Status status = 2;
  string patient_id = 3;
  AnomalyScores anomaly_scores = 5;
  RiskScore overall_risk_score = 6;
  string message = 7;
  // ... other fields
}
```

### HTTP Endpoint

**GET** `/health`

Returns service health status:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "service": "anomaly-service",
  "grpc_port": 50053
}
```

## Development

### Local Development

1. **Install dependencies**:
   ```bash
   cd services/anomaly-service
   pip install -r requirements.txt
   ```

2. **Generate protobuf stubs**:
   ```bash
   # From project root
   make proto
   # Or manually:
   python -m grpc_tools.protoc \
     --proto_path=../../proto \
     --python_out=./generated \
     --grpc_python_out=./generated \
     ../../proto/anomaly.proto
   ```

3. **Run the service**:
   ```bash
   # Set environment variables
   export PORT=8003
   export GRPC_PORT=50053
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   export REDIS_PASSWORD=redis
   
   # Run with uvicorn
   uvicorn main:app --reload --port 8003
   ```

### Docker

Build and run with Docker Compose (see main project README):

```bash
docker compose -f infra/docker-compose.yml up anomaly-service
```

Or build manually:

```bash
docker build -f services/anomaly-service/Dockerfile -t anomaly-service .
docker run -p 8003:8003 -p 50053:50053 anomaly-service
```

## Testing

### Test with gRPC client

You can use `grpcurl` or a Python client to test the service:

```python
import grpc
from generated import anomaly_pb2, anomaly_pb2_grpc

channel = grpc.insecure_channel('localhost:50053')
stub = anomaly_pb2_grpc.AnomalyDetectionStub(channel)

request = anomaly_pb2.ScoreVitalsRequest(
    version="1.0.0",
    patient_id="patient-123",
    vitals=anomaly_pb2.VitalSigns(
        heart_rate=anomaly_pb2.VitalMeasurement(value=75.0, unit="bpm"),
        oxygen_saturation=anomaly_pb2.VitalMeasurement(value=98.0, unit="%"),
        temperature=anomaly_pb2.VitalMeasurement(value=36.5, unit="°C")
    )
)

response = stub.ScoreVitals(request)
print(f"Score: {response.overall_risk_score.score}")
print(f"Anomaly: {response.overall_risk_score.severity}")
```

## Dependencies

- `fastapi`: HTTP framework for health endpoint
- `uvicorn`: ASGI server
- `grpcio`: gRPC framework
- `grpcio-tools`: Protobuf compiler tools
- `redis`: Redis client for baseline storage

## Notes

- The service maintains rolling baselines per patient and vital type
- Baselines are stored in Redis with 7-day expiration
- If Redis is unavailable, falls back to in-memory storage (data lost on restart)
- First few measurements for a patient will have low scores until baseline is established

