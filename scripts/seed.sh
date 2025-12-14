#!/bin/bash

# Seed script for initial data
# Seeds the registry service with test devices and patients

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/infra/docker-compose.yml"

echo "Seeding initial data..."

# Wait for registry to be ready
echo "Waiting for registry service to be ready..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker compose -f "$COMPOSE_FILE" exec -T registry curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Registry is ready"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

# Seed registry
echo "Seeding registry with test data..."
docker compose -f "$COMPOSE_FILE" exec -T registry python seed.py

echo "Seeding complete!"

