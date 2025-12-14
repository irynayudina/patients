# Rules Engine Service

FastAPI service that consumes enriched telemetry, applies rules, calls AnomalyService via gRPC, and produces scored telemetry and alerts.

## Overview

The Rules Engine Service:
- Consumes `telemetry.enriched` events from Kafka
- Applies rule-based evaluation on vital signs
- Calls AnomalyService via gRPC to get anomaly scores
- Produces `telemetry.scored` events (always)
- Produces `alerts.raised` events (only when severity != OK)

## Rules

The service evaluates the following rules:

1. **HR > hr_max** => `warning`
   - Heart rate exceeds maximum threshold

2. **SpO2 < spo2_min** => `critical`
   - Oxygen saturation below minimum threshold

3. **Temp > temp_max** => `warning`
   - Temperature exceeds maximum threshold

4. **HR very high AND SpO2 low** => `critical` (combined)
   - Critical combination: Heart rate > hr_very_high AND SpO2 < spo2_low

## Alert Payload

Alerts include:
- `event_id` (alertId)
- `patient_id` (patientId)
- `device_id` (deviceId)
- `severity` (OK, warning, critical)
- `alert_type` (type)
- `timestamp`
- `details`:
  - `metrics`: Current vital sign values
  - `rulesTriggered`: List of rule IDs that triggered
  - `anomalyScore`: Overall anomaly score from AnomalyService

## Configuration

Environment variables:

- `PORT`: Service port (default: 8004)
- `KAFKA_BROKERS`: Kafka broker addresses (default: localhost:9092)
- `KAFKA_CLIENT_ID`: Kafka client ID (default: rules-engine)
- `KAFKA_CONSUMER_GROUP`: Kafka consumer group (default: rules-engine-group)
- `KAFKA_TOPIC_ENRICHED`: Input topic (default: telemetry.enriched)
- `KAFKA_TOPIC_SCORED`: Output topic for scored events (default: telemetry.scored)
- `KAFKA_TOPIC_ALERTS`: Output topic for alerts (default: alerts.raised)
- `ANOMALY_SERVICE_GRPC_URL`: AnomalyService gRPC URL (default: anomaly-service:50053)
- `ANOMALY_SERVICE_TIMEOUT`: gRPC timeout in seconds (default: 5)
- `HR_MAX`: Maximum heart rate threshold (default: 100.0)
- `SPO2_MIN`: Minimum SpO2 threshold (default: 95.0)
- `TEMP_MAX`: Maximum temperature threshold in Fahrenheit (default: 100.4)
- `HR_VERY_HIGH`: Very high heart rate threshold for combined rule (default: 120.0)
- `SPO2_LOW`: Low SpO2 threshold for combined rule (default: 90.0)

## Endpoints

- `GET /`: Service information
- `GET /health`: Health check (checks Kafka and gRPC connectivity)

## Development

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate protobuf stubs:
   ```bash
   make proto
   ```

3. Run the service:
   ```bash
   uvicorn main:app --reload --port 8004
   ```

### Docker

Build and run with Docker Compose:
```bash
docker compose -f infra/docker-compose.yml up rules-engine
```

## Dependencies

- FastAPI
- aiokafka (Kafka consumer/producer)
- grpcio (gRPC client)
- pydantic (settings management)

