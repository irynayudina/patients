# Notification Service

The Notification Service consumes `alerts.raised` events from Kafka and creates notifications for patients via multiple channels (EMAIL, SMS, PUSH).

## Features

- **Multi-channel notifications**: Supports EMAIL, SMS, and PUSH notifications
- **Severity-based routing**: Automatically determines channels based on alert severity:
  - Critical: EMAIL + SMS + PUSH
  - High: EMAIL + PUSH
  - Medium: EMAIL
  - Low: EMAIL
- **Rate limiting**: Prevents notification spam per patient using Redis (with in-memory fallback)
- **PostgreSQL persistence**: All notifications are stored in PostgreSQL for audit and retrieval
- **REST API**: Query notifications by patient ID, channel, status, etc.

## API Endpoints

### GET /notifications

Query notifications with optional filters.

Query parameters:
- `patientId` (optional): Filter by patient ID
- `channel` (optional): Filter by channel (EMAIL, SMS, PUSH)
- `status` (optional): Filter by status (PENDING, SENT, FAILED)
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

Example:
```bash
GET /notifications?patientId=patient_78901&page=1&limit=20
```

### GET /notifications/:id

Get a specific notification by ID.

### GET /health

Health check endpoint that reports the status of the database, Kafka, and Redis connections.

## Configuration

Environment variables:

- `PORT`: HTTP server port (default: 3004)
- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BROKERS`: Kafka broker addresses (comma-separated)
- `KAFKA_CLIENT_ID`: Kafka client ID
- `KAFKA_CONSUMER_GROUP`: Kafka consumer group ID
- `KAFKA_TOPIC_ALERTS`: Kafka topic for alerts (default: alerts.raised)
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password (optional)
- `REDIS_ENABLED`: Enable/disable Redis (default: true)
- `RATE_LIMIT_WINDOW_MS`: Rate limit window in milliseconds (default: 60000 = 1 minute)
- `RATE_LIMIT_MAX_NOTIFICATIONS`: Max notifications per window per patient (default: 10)
- `LOG_LEVEL`: Logging level (default: info)

## Rate Limiting

The service implements rate limiting per patient to prevent notification spam. By default:
- Maximum 10 notifications per patient per minute
- Uses Redis for distributed rate limiting (falls back to in-memory if Redis is unavailable)
- When rate limit is exceeded, notifications are still created but marked as FAILED

## Database Schema

The service uses Prisma with the following schema:

```prisma
model Notification {
  id          String   @id @default(uuid())
  patientId   String
  alertId     String?
  channel     String   // EMAIL, SMS, PUSH
  status      String   // PENDING, SENT, FAILED
  subject     String?
  message     String
  metadata    Json?
  sentAt      DateTime?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

## Development

```bash
# Install dependencies
npm install

# Generate Prisma client
npm run prisma:generate

# Run migrations
npm run prisma:migrate

# Start in development mode
npm run start:dev
```

## Docker

The service includes a Dockerfile and is configured in `docker-compose.yml`. To build and run:

```bash
docker-compose up notification-service
```

## Notification Simulation

Currently, the service simulates sending notifications (95% success rate). In production, you would integrate with actual providers:
- Email: SendGrid, AWS SES, etc.
- SMS: Twilio, AWS SNS, etc.
- Push: Firebase Cloud Messaging, Apple Push Notification Service, etc.

