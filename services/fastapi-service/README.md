# FastAPI Service

FastAPI microservice for the Med Telemetry Platform.

## Features

- REST API endpoints
- gRPC server for service-to-service communication
- Kafka consumer/producer for event streaming

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate protobuf stubs:
   ```bash
   make proto
   # or manually:
   python -m grpc_tools.protoc \
     --proto_path=../../proto \
     --python_out=generated \
     --grpc_python_out=generated \
     ../../proto/*.proto
   ```

3. Run the service:
   ```bash
   uvicorn main:app --reload
   ```

## Docker

Build and run with Docker:
```bash
docker build -f Dockerfile -t fastapi-service .
docker run -p 8000:8000 fastapi-service
```

## Environment Variables

See `infra/.env.example` for available configuration options.

