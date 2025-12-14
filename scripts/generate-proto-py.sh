#!/bin/bash

# Generate Python stubs from proto files for FastAPI services
# Run from repository root: bash scripts/generate-proto-py.sh

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

PROTO_DIR="proto"
SERVICE_DIR="services/fastapi-service"
OUT_DIR="$SERVICE_DIR/generated"

# Create output directory
mkdir -p "$OUT_DIR"

echo "Generating Python stubs from proto files..."

# Check if grpcio-tools is installed
if ! python -m grpc_tools.protoc --help &>/dev/null; then
  echo "Installing grpcio-tools..."
  cd "$SERVICE_DIR"
  pip install grpcio-tools
  cd "$PROJECT_ROOT"
fi

# Generate Python stubs for each proto file
for proto_file in "$PROTO_DIR"/*.proto; do
  if [ -f "$proto_file" ]; then
    filename=$(basename "$proto_file" .proto)
    echo "Processing $filename.proto..."
    
    # Generate Python code
    python -m grpc_tools.protoc \
      --proto_path="$PROTO_DIR" \
      --python_out="$OUT_DIR" \
      --grpc_python_out="$OUT_DIR" \
      "$proto_file"
  fi
done

echo "Python stubs generated in $OUT_DIR"

