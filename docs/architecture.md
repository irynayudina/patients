# Architecture Documentation

## Med Telemetry Platform

### Overview

The Med Telemetry Platform is a microservices-based system designed for medical data telemetry processing. It uses a mix of NestJS (TypeScript) and FastAPI (Python) services that communicate via Kafka for event streaming and gRPC for synchronous service-to-service calls.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Med Telemetry Platform                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐         ┌─────────────────┐
│  NestJS Service │         │  FastAPI Service│
│  (TypeScript)   │         │  (Python)       │
│                 │         │                 │
│  - HTTP API     │         │  - HTTP API     │
│  - gRPC Server  │         │  - gRPC Server  │
│  - Kafka Client │         │  - Kafka Client │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │                           │
    ┌────┴───────────────────────────┴────┐
    │                                      │
    │         gRPC (Synchronous)          │
    │     Service-to-Service Calls        │
    │                                      │
┌───┴──────────────────────────────────────┴───┐
│                                               │
│           Kafka Event Pipeline                │
│          (Asynchronous Events)                │
│                                               │
│  ┌─────────────┐      ┌──────────────┐      │
│  │   Producer  │      │   Consumer   │      │
│  │   Services  │─────▶│   Services   │      │
│  └─────────────┘      └──────────────┘      │
│                                               │
└───────────────────────────────────────────────┘
         │                      │
         │                      │
    ┌────┴────────┐        ┌────┴────────┐
    │   Kafka     │        │  Zookeeper  │
    │   Broker    │◀───────│  (Kafka     │
    │             │        │   Metadata) │
    └─────────────┘        └─────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Shared Resources                          │
│                                                                   │
│  ┌──────────────┐                                                │
│  │ Proto Files  │  (Protocol Buffer Definitions)                 │
│  │   (proto/)   │  - Shared service contracts                    │
│  └──────────────┘  - gRPC service definitions                    │
│                                                                   │
│  ┌──────────────┐                                                │
│  │   Docker     │  (Container Orchestration)                     │
│  │   Compose    │  - Service lifecycle management                │
│  └──────────────┘  - Network configuration                       │
└─────────────────────────────────────────────────────────────────┘
```

### Communication Patterns

#### 1. Event-Driven Communication (Kafka)

**Purpose**: Asynchronous event streaming for telemetry data and system events.

**Flow**:
- Services publish events to Kafka topics
- Services subscribe to topics and consume events
- Decoupled, scalable event processing

**Use Cases**:
- Telemetry data ingestion
- Event notifications
- Data pipeline processing
- Audit logging

#### 2. Synchronous Communication (gRPC)

**Purpose**: Direct service-to-service calls requiring immediate responses.

**Flow**:
- Services define gRPC services in `.proto` files
- Generated stubs used for client/server implementation
- High-performance, type-safe communication

**Use Cases**:
- Requesting specific data
- Real-time queries
- Service orchestration
- Synchronous data retrieval

### Service Architecture

#### NestJS Service

- **Framework**: NestJS (TypeScript)
- **Communication**:
  - HTTP REST API (Express)
  - gRPC server
  - Kafka producer/consumer
- **Ports**: 
  - HTTP: 3000
  - gRPC: 50051

#### FastAPI Service

- **Framework**: FastAPI (Python)
- **Communication**:
  - HTTP REST API
  - gRPC server
  - Kafka producer/consumer
- **Ports**:
  - HTTP: 8000
  - gRPC: 50052

### Infrastructure Components

#### Kafka

- **Role**: Message broker for event streaming
- **Port**: 9092 (external), 29092 (internal)
- **Topics**: Created dynamically as needed

#### Zookeeper

- **Role**: Metadata management for Kafka
- **Port**: 2181
- **Purpose**: Cluster coordination and configuration

### Protocol Buffers

Shared `.proto` files define:
- gRPC service contracts
- Message schemas
- Service interfaces

**Location**: `proto/`

**Generation**:
- TypeScript stubs → NestJS services
- Python stubs → FastAPI services

### Development Workflow

1. **Define Contracts**: Add/update `.proto` files in `proto/`
2. **Generate Stubs**: Run `make proto` to generate language-specific stubs
3. **Implement Services**: Use generated stubs in service code
4. **Test Locally**: Use `docker compose up` or `make dev`
5. **Deploy**: Services containerized with Docker

### Network Topology

All services communicate within a Docker network (`med-telemetry-network`):
- Service discovery via service names
- Internal ports for inter-service communication
- Exposed ports for external access

### Data Flow Examples

#### Telemetry Data Ingestion

```
External Source → NestJS Service (HTTP) → Kafka Topic → FastAPI Service (Consumer)
```

#### Service-to-Service Query

```
NestJS Service → gRPC Call → FastAPI Service → Response
```

#### Event Notification

```
FastAPI Service → Kafka Event → NestJS Service (Consumer) → Action
```

### Scalability Considerations

- **Horizontal Scaling**: Services can be scaled independently
- **Kafka Partitioning**: Enables parallel processing
- **gRPC Load Balancing**: Supports multiple service instances
- **Stateless Services**: Designed for easy scaling

### Security (Future Considerations)

- Service authentication
- TLS/SSL for gRPC
- Kafka authentication (SASL/SSL)
- API authentication tokens
- Network policies

### Monitoring (Future Considerations)

- Health check endpoints (`/health`)
- Metrics collection
- Distributed tracing
- Log aggregation
- Alerting

