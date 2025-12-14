# Telemetry Gateway Service

Entrypoint service that accepts telemetry data from medical devices and publishes it to Kafka.

## Features

- **REST API**: POST `/api/telemetry` endpoint for receiving telemetry data
- **gRPC API**: `TelemetryGateway.SendMeasurements` method for device communication
- **Input Validation**: Uses class-validator for request validation
- **Device Verification**: Optional Registry service integration to verify device exists
- **Kafka Integration**: Produces events to `telemetry.raw` topic using KafkaJS
- **Retry Logic**: Automatic retry with exponential backoff for Kafka operations
- **Graceful Shutdown**: Handles SIGTERM/SIGINT signals properly
- **Structured Logging**: Uses Winston for JSON-formatted logs

## API

### REST Endpoint

**POST** `/api/telemetry`

Request body:
```json
{
  "deviceId": "device_12345",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "metrics": {
    "hr": 72,
    "spo2": 98,
    "temp": 98.6
  },
  "meta": {
    "battery": 85,
    "firmware": "v1.0.0"
  }
}
```

Response:
```json
{
  "success": true,
  "eventId": "evt_550e8400-e29b-41d4-a716-446655440000",
  "message": "Telemetry received and processed"
}
```

### gRPC Endpoint

**Service**: `telemetry.gateway.TelemetryGateway`  
**Method**: `SendMeasurements`

See `proto/telemetry_gateway.proto` for the full schema.

## Configuration

Environment variables (see `.env.example`):

- `PORT`: HTTP server port (default: 3000)
- `GRPC_PORT`: gRPC server port (default: 50052)
- `KAFKA_BROKERS`: Comma-separated Kafka broker addresses (default: localhost:29092)
- `KAFKA_CLIENT_ID`: Kafka client identifier (default: telemetry-gateway)
- `KAFKA_TOPIC_RAW`: Kafka topic for raw telemetry (default: telemetry.raw)
- `REGISTRY_GRPC_URL`: Registry service gRPC URL (default: localhost:50051)
- `REGISTRY_ENABLED`: Enable/disable device verification (default: true)
- `LOG_LEVEL`: Logging level (default: info)

## Development

```bash
# Install dependencies
npm install

# Generate proto stubs
npm run proto:generate

# Run in development mode
npm run start:dev

# Run tests
npm test
```

## Docker

```bash
# Build image
docker build -t telemetry-gateway -f services/telemetry-gateway/Dockerfile .

# Run container
docker run -p 3000:3000 -p 50052:50052 \
  -e KAFKA_BROKERS=kafka:29092 \
  -e REGISTRY_GRPC_URL=registry:50051 \
  telemetry-gateway
```

## Testing

Unit tests are located in `src/**/*.spec.ts`. Run with:

```bash
npm test
```

