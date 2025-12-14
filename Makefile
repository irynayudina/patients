.PHONY: help up down logs proto dev seed clean simulate

# Default target
help:
	@echo "Med Telemetry Platform - Makefile Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make up      - Start all services with Docker Compose"
	@echo "  make down    - Stop all services"
	@echo "  make logs    - View logs from all services"
	@echo "  make proto   - Generate protobuf stubs for all services"
	@echo "  make dev     - Start services in development mode"
	@echo "  make seed    - Seed initial data"
	@echo "  make clean   - Clean generated files and Docker resources"
	@echo "  make simulate - Run device simulator (use DEVICES=N INTERVAL=X EPISODE_RATE=R)"

# Start all services
up:
	docker compose -f infra/docker-compose.yml up -d

# Stop all services
down:
	docker compose -f infra/docker-compose.yml down

# View logs
logs:
	docker compose -f infra/docker-compose.yml logs -f

# Generate protobuf stubs
proto:
	@echo "Generating protobuf stubs..."
	@bash scripts/generate-proto-ts.sh
	@bash scripts/generate-proto-py.sh
	@echo "Protobuf stubs generated successfully!"

# Development mode (with hot reload)
dev: proto
	@echo "Starting services in development mode..."
	docker compose -f infra/docker-compose.yml up

# Seed data
seed:
	@echo "Seeding initial data..."
	@bash scripts/seed.sh || echo "No seed script available yet"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@find services -type d -name "*_pb2*" -exec rm -rf {} + 2>/dev/null || true
	@find services -type d -name "generated" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned generated files"

# Rebuild services
rebuild:
	docker compose -f infra/docker-compose.yml build --no-cache

# Restart a specific service
restart-%:
	docker compose -f infra/docker-compose.yml restart $(subst restart-,,$@)

# Run device simulator
simulate:
	@echo "Starting device simulator..."
	@echo "Devices: ${DEVICES:-5}, Interval: ${INTERVAL:-5}s, Episode Rate: ${EPISODE_RATE:-0.05}"
	docker compose -f infra/docker-compose.yml run --rm device-simulator \
		python main.py \
		--devices ${DEVICES:-5} \
		--interval ${INTERVAL:-5} \
		--episode-rate ${EPISODE_RATE:-0.05} \
		--log-level ${LOG_LEVEL:-INFO}

