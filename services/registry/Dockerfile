FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/registry/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files
COPY proto /app/proto

# Copy source code
COPY services/registry /app

# Generate protobuf stubs
RUN python -m grpc_tools.protoc \
    --proto_path=/app/proto \
    --python_out=/app/generated \
    --grpc_python_out=/app/generated \
    /app/proto/registry.proto || echo "Proto generation skipped in build"

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Copy only requirements and install production dependencies
COPY services/registry/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and generated stubs
COPY --from=base /app /app

# Expose ports
EXPOSE 8000 50051

# Start command: run migrations then start the service
CMD ["sh", "-c", "alembic upgrade head && python seed.py && uvicorn main:app --host 0.0.0.0 --port 8000"]

