# Telemetry Normalizer Service

First stage of the telemetry processing pipeline. Consumes raw telemetry events from Kafka, normalizes and validates metrics, then produces normalized events.

## Features

- **Kafka Consumer**: Consumes from `telemetry.raw` topic using aiokafka (async)
- **Metric Normalization**:
  - Clamps heart rate to 20-240 bpm
  - Clamps SpO2 to 50-100%
  - Clamps temperature to 30-45°C
  - Validates and normalizes timestamps to ISO 8601 format
  - Maps various metric name variations to standard names
- **Kafka Producer**: Produces to `telemetry.normalized` topic
- **Idempotency**: Uses event_id for idempotency (no exactly-once, but idempotent processing)
- **Health Endpoint**: `/health` endpoint for service health checks
- **Logging**: Clear logging of consumed offsets and produced event IDs

## Configuration

Environment variables:

- `PORT`: Service port (default: 8001)
- `KAFKA_BROKERS`: Kafka broker addresses (default: localhost:9092)
- `KAFKA_CLIENT_ID`: Kafka client ID (default: telemetry-normalizer)
- `KAFKA_CONSUMER_GROUP`: Consumer group ID (default: telemetry-normalizer-group)
- `KAFKA_TOPIC_RAW`: Raw telemetry topic (default: telemetry.raw)
- `KAFKA_TOPIC_NORMALIZED`: Normalized telemetry topic (default: telemetry.normalized)
- `HR_MIN`, `HR_MAX`: Heart rate bounds (default: 20-240)
- `SPO2_MIN`, `SPO2_MAX`: SpO2 bounds (default: 50-100)
- `TEMP_MIN`, `TEMP_MAX`: Temperature bounds (default: 30-45)

## Running

### With Docker Compose

```bash
docker compose -f infra/docker-compose.yml up telemetry-normalizer
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Kafka (if not already running):
```bash
docker compose -f infra/docker-compose.yml up kafka
```

3. Run the service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

- `GET /`: Service information
- `GET /health`: Health check endpoint

## Normalization Rules

### Metric Name Mapping

The service maps various metric name variations to standard names:
- `hr`, `heartrate`, `pulse` → `heart_rate`
- `spo2`, `o2sat`, `o2` → `oxygen_saturation`
- `temp`, `body_temp` → `temperature`
- `bp`, `blood_pressure` → `blood_pressure`
- `rr`, `respiration` → `respiratory_rate`

### Value Clamping

- **Heart Rate**: Clamped to 20-240 bpm
- **SpO2**: Clamped to 50-100%
- **Temperature**: Clamped to 30-45°C

### Timestamp Normalization

- Accepts ISO 8601 strings, Unix timestamps (seconds or milliseconds)
- Always outputs ISO 8601 format with UTC timezone
- Falls back to current time if parsing fails

## Event Structure

### Input (telemetry.raw)

```json
{
  "event_id": "evt_...",
  "event_type": "telemetry.raw",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "device_id": "device_12345",
  "measurements": [
    {
      "metric": "heart_rate",
      "value": 75,
      "unit": "bpm"
    }
  ]
}
```

### Output (telemetry.normalized)

```json
{
  "event_id": "evt_...",
  "event_type": "telemetry.normalized",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source_event_id": "evt_...",
  "device_id": "device_12345",
  "patient_id": "patient_...",
  "vitals": {
    "heart_rate": {
      "value": 75,
      "unit": "bpm",
      "timestamp": "2024-01-15T10:30:00.000Z"
    }
  },
  "validation_status": "valid",
  "normalization_metadata": {
    "normalized_at": "2024-01-15T10:30:01.000Z",
    "normalization_rules_version": "1.0.0"
  }
}
```

## Logging

The service logs:
- Consumed message offset and partition
- Source event ID from raw telemetry
- Produced normalized event ID
- Warnings for clamped values
- Errors for processing failures

Example log output:
```
2024-01-15 10:30:00 - __main__ - INFO - Consumed message from offset 123 (partition 0), event_id: evt_550e8400...
2024-01-15 10:30:00 - __main__ - INFO - Produced normalized event, event_id: evt_660e8400..., source_event_id: evt_550e8400...
```

