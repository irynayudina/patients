# Analytics Service

Real-time analytics service for patient monitoring platform. Consumes telemetry and alert events from Kafka and maintains aggregates in Redis.

## Features

- Consumes `telemetry.scored` and `alerts.raised` events from Kafka
- Maintains per-patient aggregates:
  - Last vitals
  - Rolling averages for heart rate, SpO2, and temperature (15m and 1h windows)
- Maintains global aggregates:
  - Alerts per minute by severity
- REST API endpoints for querying statistics

## Endpoints

- `GET /health` - Health check
- `GET /stats/patients/{patient_id}/summary` - Get patient summary with last vitals and rolling averages
- `GET /stats/global/alerts` - Get global alert statistics per minute by severity

## Configuration

Environment variables:
- `PORT` - Service port (default: 8005)
- `KAFKA_BROKERS` - Kafka broker addresses (default: localhost:9092)
- `KAFKA_CLIENT_ID` - Kafka client ID (default: analytics)
- `KAFKA_CONSUMER_GROUP` - Kafka consumer group (default: analytics-group)
- `KAFKA_TOPIC_SCORED` - Topic for telemetry.scored (default: telemetry.scored)
- `KAFKA_TOPIC_ALERTS` - Topic for alerts.raised (default: alerts.raised)
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `REDIS_PASSWORD` - Redis password (default: redis)
- `REDIS_DB` - Redis database number (default: 0)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn main:app --reload --port 8005
```

## Docker

```bash
docker build -t analytics-service .
docker run -p 8005:8005 analytics-service
```

