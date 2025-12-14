FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/device-simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install grpcio-tools for proto generation
RUN pip install --no-cache-dir grpcio-tools

# Copy proto files
COPY proto /proto

# Copy application code first
COPY services/device-simulator /app

# Create generated directory
RUN mkdir -p /app/generated

# Generate gRPC stubs
RUN python -m grpc_tools.protoc \
    --proto_path=/proto \
    --python_out=/app/generated \
    --grpc_python_out=/app/generated \
    /proto/telemetry_gateway.proto

# Create __init__.py for generated package
RUN touch /app/generated/__init__.py

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "main.py"]

