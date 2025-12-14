# Patient Monitoring System

A production-ready microservices-based patient monitoring platform for medical telemetry data processing. The system processes real-time vital signs from medical devices, enriches data with patient context, detects anomalies, and generates alerts and incidents.

## Architecture Overview

The system follows an event-driven microservices architecture:

- **Event Pipeline**: Kafka for asynchronous event streaming between services
- **Service Communication**: gRPC for synchronous service-to-service calls
- **Services**: Mix of NestJS (TypeScript) and FastAPI (Python) microservices
- **Infrastructure**: Dockerized services orchestrated with Docker Compose

### Data Flow

```
Device → Telemetry Gateway → [Kafka: telemetry.raw]
  ↓
Telemetry Normalizer → [Kafka: telemetry.normalized]
  ↓
Telemetry Enrichment → [Kafka: telemetry.enriched]
  ↓
Rules Engine → [Kafka: telemetry.scored, alerts.raised]
  ↓
Incident Service + Notification Service + Analytics Service
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Services

| Service | Language | Port | Description |
|---------|----------|------|-------------|
| **telemetry-gateway** | TypeScript/NestJS | 3000 (HTTP), 50052 (gRPC) | Entry point for device telemetry data |
| **telemetry-normalizer** | Python/FastAPI | 8001 | Normalizes and validates raw telemetry |
| **telemetry-enrichment** | TypeScript/NestJS | 3002 | Enriches telemetry with patient context |
| **rules-engine** | Python/FastAPI | 8004 | Applies rules and calls anomaly detection |
| **anomaly-service** | Python/FastAPI | 8003 (HTTP), 50053 (gRPC) | ML-based anomaly scoring service |
| **incident-service** | TypeScript/NestJS | 3003 | Creates and manages incidents from alerts |
| **notification-service** | TypeScript/NestJS | 3004 | Sends notifications with rate limiting |
| **analytics** | Python/FastAPI | 8005 | Aggregates telemetry and alert data |
| **registry** | Python/FastAPI | 8000 (HTTP), 50051 (gRPC) | Device and patient registry |
| **device-simulator** | Python | - | Simulates medical devices for testing |

## Kafka Topics

| Topic | Description | Producer | Consumers |
|-------|-------------|----------|-----------|
| `telemetry.raw` | Raw telemetry from devices | telemetry-gateway | telemetry-normalizer |
| `telemetry.normalized` | Normalized telemetry | telemetry-normalizer | telemetry-enrichment |
| `telemetry.enriched` | Enriched telemetry with context | telemetry-enrichment | rules-engine |
| `telemetry.scored` | Telemetry with anomaly scores | rules-engine | analytics |
| `alerts.raised` | Alert events | rules-engine | incident-service, notification-service, analytics |

See [docs/events.md](docs/events.md) for event schemas.

## Prerequisites

- Docker & Docker Compose
- Make (or use individual commands from Makefile)
- Node.js 18+ (for local NestJS development)
- Python 3.10+ (for local FastAPI development)
- Protocol Buffers compiler (`protoc`)

## How to Run

### Quick Start

1. **Generate protobuf stubs:**
   ```bash
   make proto
   ```

2. **Start all services:**
   ```bash
   make up
   ```
   Or:
   ```bash
   docker compose -f infra/docker-compose.yml up -d
   ```

3. **Seed initial data (devices, patients):**
   ```bash
   make seed
   ```

4. **Run device simulator:**
   ```bash
   make simulate
   ```

5. **View logs:**
   ```bash
   make logs
   ```

6. **Stop all services:**
   ```bash
   make down
   ```

### Make Commands

```bash
make up          # Start all services
make down        # Stop all services
make logs        # View logs from all services
make dev         # Start in development mode with hot reload
make seed        # Seed initial data (devices, patients)
make proto       # Generate protobuf stubs
make simulate    # Run device simulator
make clean       # Clean generated files and Docker resources
```

### End-to-End Test

Run the end-to-end test script:
```bash
bash scripts/e2e-test.sh
```

This script will:
1. Start all services via Docker Compose
2. Seed the registry with test data
3. Run the device simulator for 60 seconds
4. Assert that incidents were created via HTTP call to incident-service
5. Clean up resources

## Project Structure

```
patientMonitoring/
├── services/              # Microservices
│   ├── telemetry-gateway/     # Entry point service
│   ├── telemetry-normalizer/   # Normalization service
│   ├── telemetry-enrichment/   # Enrichment service
│   ├── rules-engine/           # Rules and anomaly detection
│   ├── anomaly-service/        # ML anomaly scoring
│   ├── incident-service/       # Incident management
│   ├── notification-service/   # Notification delivery
│   ├── analytics/              # Data aggregation
│   ├── registry/               # Device/patient registry
│   └── device-simulator/       # Test device simulator
├── proto/                 # Protocol Buffer definitions
├── infra/                 # Infrastructure
│   ├── docker-compose.yml
│   └── README.md
├── scripts/               # Utility scripts
│   ├── generate-proto-ts.sh
│   ├── generate-proto-py.sh
│   ├── seed.sh
│   └── e2e-test.sh
├── docs/                  # Documentation
│   ├── architecture.md
│   ├── events.md
│   ├── grpc.md
│   └── contracts.md
├── Makefile              # Task runner
└── README.md
```

## Development

### Local Development (without Docker)

1. Start infrastructure dependencies:
   ```bash
   docker compose -f infra/docker-compose.yml up kafka postgres redis
   ```

2. Generate protobuf stubs:
   ```bash
   make proto
   ```

3. Run services individually:
   ```bash
   # NestJS service
   cd services/telemetry-gateway
   npm install
   npm run start:dev

   # Python service
   cd services/telemetry-normalizer
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

## Protocol Buffers

Shared `.proto` files are located in `proto/`. Run `make proto` to generate:
- TypeScript stubs for NestJS services
- Python stubs for FastAPI services

See [docs/grpc.md](docs/grpc.md) for gRPC service documentation.

## Features

- **Event Correlation**: All Kafka events include `event_id` and `trace_id` for end-to-end tracing
- **Structured Logging**: JSON-formatted logs with correlation IDs across all services
- **Health Checks**: All services expose `/health` endpoints
- **Rate Limiting**: Notification service includes rate limiting to prevent spam
- **Anomaly Detection**: ML-based scoring with configurable thresholds
- **Incident Management**: Automatic incident creation from alerts
- **Analytics**: Real-time aggregation of telemetry and alert data

## Documentation

- [Architecture](docs/architecture.md) - System architecture and design
- [Events](docs/events.md) - Kafka event schemas
- [gRPC](docs/grpc.md) - gRPC service definitions
- [Contracts](docs/contracts.md) - Shared contracts documentation

## Environment Variables

Key environment variables (see `infra/docker-compose.yml` for full list):

- `KAFKA_BROKERS` - Kafka broker addresses
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Database credentials
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` - Redis configuration
- Service-specific ports and timeouts

## License

[Add your license here]
