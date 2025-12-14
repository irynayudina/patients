FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/fastapi-service/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto files
COPY proto /app/proto

# Copy source code
COPY services/fastapi-service /app

# Generate protobuf stubs
RUN python -m grpc_tools.protoc \
    --proto_path=/app/proto \
    --python_out=/app/generated \
    --grpc_python_out=/app/generated \
    /app/proto/*.proto || echo "Proto generation skipped in build"

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Copy only requirements and install production dependencies
COPY services/fastapi-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and generated stubs
COPY --from=base /app /app

# Expose ports
EXPOSE 8000 50052

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

