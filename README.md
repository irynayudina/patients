# Med Telemetry Platform

A microservices-based telemetry platform for medical data processing, built with NestJS and FastAPI services communicating via Kafka (event pipeline) and gRPC (service-to-service).

## Architecture

- **Event Pipeline**: Kafka for asynchronous event streaming
- **Service Communication**: gRPC for synchronous service-to-service calls
- **Services**: Mix of NestJS (TypeScript) and FastAPI (Python) microservices
- **Infrastructure**: Dockerized services with Docker Compose

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Prerequisites

- Docker & Docker Compose
- Make (or use individual commands from Makefile)
- Node.js 18+ (for local NestJS development)
- Python 3.10+ (for local FastAPI development)
- Protocol Buffers compiler (`protoc`)

## Quick Start

1. **Copy environment variables:**
   ```bash
   # Copy from infra/.env.example to .env at root (or use infra/.env.example as reference)
   cp infra/.env.example .env
   ```
   Or create `.env` file manually based on `infra/.env.example`

2. **Generate protobuf stubs:**
   ```bash
   make proto
   ```

3. **Start all services:**
   ```bash
   docker compose -f infra/docker-compose.yml up
   ```
   Or from the `infra/` directory:
   ```bash
   cd infra
   docker compose up
   ```

4. **Or use Make commands:**
   ```bash
   make up          # Start all services
   make down        # Stop all services
   make logs        # View logs
   make dev         # Start in development mode with hot reload
   make seed        # Seed initial data (if applicable)
   make proto       # Generate protobuf stubs
   ```

## Project Structure

```
med-telemetry-platform/
├── services/           # Microservices
│   ├── nestjs-service/ # Example NestJS service
│   └── fastapi-service/# Example FastAPI service
├── proto/              # Shared Protocol Buffer definitions
├── infra/              # Infrastructure as Code
│   ├── docker-compose.yml
│   └── .env.example
├── scripts/            # Utility scripts
│   ├── generate-proto-ts.sh
│   └── generate-proto-py.sh
├── docs/               # Documentation
│   └── architecture.md
├── Makefile            # Task runner
├── .env.example        # Environment template
└── README.md
```

## Services

### NestJS Service
A TypeScript-based microservice using NestJS framework.

### FastAPI Service
A Python-based microservice using FastAPI framework.

## Development

### Local Development (without Docker)

1. Start infrastructure dependencies:
   ```bash
   docker compose -f infra/docker-compose.yml up kafka zookeeper
   ```

2. Generate protobuf stubs:
   ```bash
   make proto
   ```

3. Run services individually:
   ```bash
   # NestJS service
   cd services/nestjs-service
   npm install
   npm run start:dev

   # FastAPI service
   cd services/fastapi-service
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

## Protocol Buffers

Shared `.proto` files are located in `proto/`. Run `make proto` to generate:
- TypeScript stubs for NestJS services
- Python stubs for FastAPI services

## Environment Variables

Copy `.env.example` to `.env` and configure as needed. Key variables:
- Kafka brokers
- Service ports
- gRPC ports
- Database connections (if applicable)

## License

[Add your license here]

