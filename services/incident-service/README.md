# Incident Service

A NestJS microservice that manages incidents created from alerts raised by the rules engine.

## Overview

The Incident Service:
- Consumes `alerts.raised` events from Kafka
- Creates and manages Incident records in PostgreSQL using Prisma
- Provides REST API endpoints for querying and updating incidents
- Supports pagination for efficient data retrieval
- Can start even if Kafka is temporarily unavailable (with retry logic)

## Features

- **Kafka Consumer**: Consumes `alerts.raised` events and automatically creates incidents
- **REST API**: Query and update incidents via HTTP endpoints
- **Pagination**: Efficient pagination support for large datasets
- **Resilient**: Service can start without Kafka connection and will retry automatically
- **Prisma ORM**: Type-safe database access with Prisma

## Database Schema

The Incident model includes:
- `id`: UUID primary key
- `patientId`: Patient identifier
- `deviceId`: Device identifier (optional)
- `severity`: Alert severity (low, medium, high, critical)
- `type`: Alert type
- `status`: Incident status (OPEN, ACK, RESOLVED)
- `details`: JSON field containing alert details
- `createdAt`: Timestamp when incident was created
- `updatedAt`: Timestamp when incident was last updated

## API Endpoints

### GET /incidents

Query incidents with optional filters and pagination.

**Query Parameters:**
- `status` (optional): Filter by status (OPEN, ACK, RESOLVED)
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `patientId` (optional): Filter by patient ID
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Example:**
```bash
GET /incidents?status=OPEN&severity=high&page=1&limit=20
```

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "patientId": "patient_123",
      "deviceId": "device_456",
      "severity": "high",
      "type": "vital_sign_anomaly",
      "status": "OPEN",
      "details": {...},
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T10:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### GET /incidents/:id

Get a specific incident by ID.

**Example:**
```bash
GET /incidents/123e4567-e89b-12d3-a456-426614174000
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "patientId": "patient_123",
  "deviceId": "device_456",
  "severity": "high",
  "type": "vital_sign_anomaly",
  "status": "OPEN",
  "details": {...},
  "createdAt": "2024-01-15T10:30:00.000Z",
  "updatedAt": "2024-01-15T10:30:00.000Z"
}
```

### PATCH /incidents/:id

Update the status of an incident.

**Request Body:**
```json
{
  "status": "ACK"
}
```

**Valid Status Values:**
- `OPEN`: Incident is open
- `ACK`: Incident has been acknowledged
- `RESOLVED`: Incident has been resolved

**Example:**
```bash
PATCH /incidents/123e4567-e89b-12d3-a456-426614174000
Content-Type: application/json

{
  "status": "ACK"
}
```

## Environment Variables

- `PORT`: HTTP server port (default: 3003)
- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BROKERS`: Comma-separated list of Kafka brokers (default: localhost:29092)
- `KAFKA_CLIENT_ID`: Kafka client ID (default: incident-service)
- `KAFKA_CONSUMER_GROUP`: Kafka consumer group (default: incident-service-group)
- `KAFKA_TOPIC_ALERTS`: Kafka topic for alerts (default: alerts.raised)
- `KAFKA_CONNECTION_RETRY_ATTEMPTS`: Number of retry attempts for Kafka connection (default: 10)
- `KAFKA_CONNECTION_RETRY_DELAY`: Delay between retry attempts in ms (default: 5000)
- `LOG_LEVEL`: Logging level (default: info)

## Development

### Prerequisites

- Node.js 18+
- PostgreSQL 16+
- Kafka (for consuming alerts)

### Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   Create a `.env` file or set environment variables:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/patient_monitoring
   KAFKA_BROKERS=localhost:29092
   ```

3. **Run Prisma migrations:**
   ```bash
   npm run prisma:migrate
   ```

4. **Generate Prisma Client:**
   ```bash
   npm run prisma:generate
   ```

5. **Start the service:**
   ```bash
   npm run start:dev
   ```

### Database Migrations

**Create a new migration:**
```bash
npm run prisma:migrate
```

**Apply migrations in production:**
```bash
npm run prisma:migrate:deploy
```

**Open Prisma Studio (database GUI):**
```bash
npm run prisma:studio
```

## Docker

The service is containerized and can be run with Docker Compose:

```bash
docker compose -f infra/docker-compose.yml up incident-service
```

The Dockerfile:
- Builds the NestJS application
- Generates Prisma Client
- Runs migrations on startup
- Starts the service

## Kafka Resilience

The service is designed to be resilient to Kafka connection failures:

1. **Retry Logic**: Automatically retries Kafka connection with exponential backoff
2. **Non-blocking Startup**: Service starts even if Kafka is unavailable
3. **Background Retry**: Continues attempting to connect in the background
4. **Graceful Degradation**: Service remains functional for REST API even without Kafka

If Kafka is unavailable at startup, the service will:
- Log a warning
- Continue starting up
- Retry connection in the background
- Start consuming messages once connected

## Architecture

```
Kafka (alerts.raised)
    ↓
KafkaConsumerService
    ↓
IncidentService.createFromAlert()
    ↓
Prisma → PostgreSQL
```

The service listens to `alerts.raised` events and automatically creates Incident records. The REST API allows external systems to query and update incidents.

## Testing

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:cov
```

## License

[Add your license here]

