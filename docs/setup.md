# Setup Guide

## Initial Setup

1. **Environment Configuration**
   - Copy `infra/.env.example` to `.env` at the repository root
   - Adjust environment variables as needed

2. **Install Dependencies**

   For NestJS service:
   ```bash
   cd services/nestjs-service
   npm install
   cd ../..
   ```

   For FastAPI service:
   ```bash
   cd services/fastapi-service
   pip install -r requirements.txt
   cd ../..
   ```

3. **Generate Protocol Buffer Stubs**
   ```bash
   make proto
   ```

   This will generate:
   - TypeScript stubs in `services/nestjs-service/src/generated/`
   - Python stubs in `services/fastapi-service/generated/`

## Running Services

### Using Docker Compose (Recommended)

```bash
# Start all services
make up

# Or directly:
docker compose -f infra/docker-compose.yml up

# View logs
make logs

# Stop services
make down
```

### Development Mode (Hot Reload)

```bash
make dev
```

This starts all services with volume mounts for hot reloading.

### Local Development (Without Docker)

1. Start infrastructure dependencies:
   ```bash
   docker compose -f infra/docker-compose.yml up kafka zookeeper
   ```

2. Run NestJS service:
   ```bash
   cd services/nestjs-service
   npm run start:dev
   ```

3. Run FastAPI service (in another terminal):
   ```bash
   cd services/fastapi-service
   uvicorn main:app --reload
   ```

## Adding New Services

1. Create a new folder in `services/`
2. Add service configuration to `infra/docker-compose.yml`
3. Update environment variables in `infra/.env.example`
4. Add service to Makefile if needed

## Adding New Protocol Buffers

1. Add `.proto` file to `proto/` directory
2. Run `make proto` to generate stubs
3. Import generated stubs in your service code

## Troubleshooting

### Proto generation fails
- Ensure `protoc` is installed: `brew install protobuf` (macOS) or download from [protobuf releases](https://github.com/protocolbuffers/protobuf/releases)
- For TypeScript: Ensure dependencies are installed in `services/nestjs-service`
- For Python: Ensure `grpcio-tools` is installed (`pip install grpcio-tools`)

### Docker build fails
- Check that Dockerfile paths are correct relative to build context
- Ensure all required files exist in the service directories

### Kafka connection issues
- Verify Kafka and Zookeeper are healthy: `docker compose -f infra/docker-compose.yml ps`
- Check service logs: `docker compose -f infra/docker-compose.yml logs kafka`

