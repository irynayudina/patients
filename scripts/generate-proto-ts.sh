#!/bin/bash

# Generate TypeScript stubs from proto files for NestJS services
# Run from repository root: bash scripts/generate-proto-ts.sh

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

PROTO_DIR="proto"
SERVICE_DIR="services/nestjs-service"
OUT_DIR="$SERVICE_DIR/src/generated"

# Create output directory
mkdir -p "$OUT_DIR"

# Install dependencies if needed
if [ ! -f "$SERVICE_DIR/node_modules/.bin/protoc-gen-ts_proto" ] && [ ! -f "$SERVICE_DIR/node_modules/ts-proto/build/bin/protoc-gen-ts_proto.js" ]; then
  echo "Installing protoc dependencies..."
  cd "$SERVICE_DIR"
  npm install --save-dev @grpc/proto-loader @grpc/grpc-js ts-proto @types/node
  cd "$PROJECT_ROOT"
fi

# Find ts-proto plugin
TS_PROTO_PLUGIN=""
if [ -f "$SERVICE_DIR/node_modules/.bin/protoc-gen-ts_proto" ]; then
  TS_PROTO_PLUGIN="$SERVICE_DIR/node_modules/.bin/protoc-gen-ts_proto"
elif [ -f "$SERVICE_DIR/node_modules/ts-proto/build/bin/protoc-gen-ts_proto.js" ]; then
  TS_PROTO_PLUGIN="$SERVICE_DIR/node_modules/ts-proto/build/bin/protoc-gen-ts_proto.js"
else
  echo "Error: ts-proto plugin not found. Please install dependencies in $SERVICE_DIR"
  exit 1
fi

echo "Generating TypeScript stubs from proto files..."

# Generate TypeScript stubs for each proto file
for proto_file in "$PROTO_DIR"/*.proto; do
  if [ -f "$proto_file" ]; then
    filename=$(basename "$proto_file" .proto)
    echo "Processing $filename.proto..."
    
    # Generate TypeScript definitions using ts-proto
    # Options configured for @grpc/grpc-js compatibility
    protoc \
      --plugin=protoc-gen-ts_proto="$TS_PROTO_PLUGIN" \
      --ts_proto_out="$OUT_DIR" \
      --ts_proto_opt=nestJs=true \
      --ts_proto_opt=useExactTypes=false \
      --ts_proto_opt=esModuleInterop=true \
      --ts_proto_opt=outputServices=grpc-js \
      --ts_proto_opt=fileSuffix=.pb \
      --proto_path="$PROTO_DIR" \
      "$proto_file"
  fi
done

echo "TypeScript stubs generated in $OUT_DIR"

