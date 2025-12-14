# Telemetry Enrichment Service

NestJS service that enriches normalized telemetry events with patient context and thresholds.

## Overview

This service:
- Consumes `telemetry.normalized` events from Kafka
- Calls Registry service via gRPC to:
  - Map `deviceId` → `patientId`
  - Fetch patient information (age, sex)
  - Fetch threshold profiles
- Produces `telemetry.enriched` events to Kafka
- Handles orphan events (devices not linked to patients) by marking `orphan=true`

## Features

- **Kafka Consumer**: Consumes normalized telemetry events
- **Kafka Producer**: Produces enriched telemetry events
- **gRPC Client**: Communicates with Registry service with retries and timeouts
- **Graceful Shutdown**: Handles SIGTERM/SIGINT signals properly
- **Error Handling**: Retries for gRPC calls, continues processing on errors
- **Orphan Detection**: Marks events as orphan when device is not linked to patient

## Environment Variables

- `PORT`: HTTP port for health checks (default: 3002)
- `KAFKA_BROKERS`: Comma-separated Kafka broker addresses (default: localhost:29092)
- `KAFKA_CLIENT_ID`: Kafka client ID (default: telemetry-enrichment)
- `KAFKA_CONSUMER_GROUP`: Kafka consumer group (default: telemetry-enrichment-group)
- `KAFKA_TOPIC_NORMALIZED`: Input topic (default: telemetry.normalized)
- `KAFKA_TOPIC_ENRICHED`: Output topic (default: telemetry.enriched)
- `REGISTRY_GRPC_URL`: Registry gRPC service URL (default: localhost:50051)
- `REGISTRY_ENABLED`: Enable/disable registry calls (default: true)
- `REGISTRY_TIMEOUT_MS`: gRPC timeout in milliseconds (default: 5000)
- `REGISTRY_MAX_RETRIES`: Maximum retries for gRPC calls (default: 3)
- `REGISTRY_RETRY_DELAY_MS`: Initial retry delay in milliseconds (default: 1000)
- `GRACEFUL_SHUTDOWN_TIMEOUT_MS`: Graceful shutdown timeout (default: 30000)
- `LOG_LEVEL`: Logging level (default: info)

## Development

```bash
# Install dependencies
npm install

# Generate protobuf stubs
npm run proto:generate

# Run in development mode
npm run start:dev

# Build
npm run build

# Run production build
npm run start:prod
```

## Docker

```bash
# Build image
docker build -t telemetry-enrichment -f services/telemetry-enrichment/Dockerfile .

# Run container
docker run -p 3002:3002 \
  -e KAFKA_BROKERS=kafka:29092 \
  -e REGISTRY_GRPC_URL=registry:50051 \
  telemetry-enrichment
```

