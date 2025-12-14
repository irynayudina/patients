# Infrastructure Setup

This directory contains the Docker Compose configuration for local development infrastructure.

## Services

The infrastructure includes the following services:

- **Kafka** (Bitnami with KRaft mode) - Message broker on port `9092` (external) and `29092` (internal)
- **PostgreSQL 16** - Relational database on port `5432`
- **Redis 7** - In-memory data store on port `6379`
- **Kafka UI** - Web interface for Kafka topic inspection on port `8080`

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Docker Compose v2.0+ (included with Docker Desktop)

## Quick Start

1. **Navigate to the infra directory:**
   ```bash
   cd infra
   ```

2. **Review and customize environment variables (optional):**
   ```bash
   # The .env file contains default values
   # Edit infra/.env if you need to change ports or credentials
   ```

3. **Start all services:**
   ```bash
   docker compose up -d
   ```

4. **Verify services are running:**
   ```bash
   docker compose ps
   ```

5. **Check service health:**
   ```bash
   docker compose ps
   # All services should show "healthy" status
   ```

6. **View logs:**
   ```bash
   # All services
   docker compose logs -f

   # Specific service
   docker compose logs -f kafka
   docker compose logs -f postgres
   docker compose logs -f redis
   docker compose logs -f kafka-ui
   ```

## Service Access

### Kafka

- **External (from host):** `localhost:9092`
- **Internal (from containers):** `kafka:29092`
- **Connection string:** `localhost:9092` (for applications running on your host machine)

### PostgreSQL

- **Host:** `localhost`
- **Port:** `5432` (default, configurable via `POSTGRES_PORT` in `.env`)
- **Database:** `patient_monitoring` (default, configurable via `POSTGRES_DB` in `.env`)
- **Username:** `postgres` (default, configurable via `POSTGRES_USER` in `.env`)
- **Password:** `postgres` (default, configurable via `POSTGRES_PASSWORD` in `.env`)

**Connection string example:**
```
postgresql://postgres:postgres@localhost:5432/patient_monitoring
```

### Redis

- **Host:** `localhost`
- **Port:** `6379` (default, configurable via `REDIS_PORT` in `.env`)
- **Password:** `redis` (default, configurable via `REDIS_PASSWORD` in `.env`)

**Connection string example:**
```
redis://:redis@localhost:6379
```

**Using redis-cli:**
```bash
docker exec -it redis redis-cli -a redis
```

### Kafka UI

- **URL:** http://localhost:8080
- Open in your browser to inspect Kafka topics, messages, and cluster information

## Network

All services are connected via the `patient-monitoring-network` bridge network. Services can communicate with each other using their container names:

- `kafka` - Kafka broker
- `postgres` - PostgreSQL database
- `redis` - Redis server
- `kafka-ui` - Kafka UI web interface

## Health Checks

All services include health checks:

- **Kafka:** Checks broker API availability
- **PostgreSQL:** Uses `pg_isready` to verify database readiness
- **Redis:** Verifies Redis server responsiveness
- **Kafka UI:** Checks web interface availability

Health check status can be viewed with:
```bash
docker compose ps
```

## Data Persistence

All data is persisted in Docker volumes:

- `kafka-data` - Kafka logs and metadata
- `postgres-data` - PostgreSQL data files
- `redis-data` - Redis AOF (Append Only File) persistence

To remove all data and start fresh:
```bash
docker compose down -v
```

## Common Commands

### Start services
```bash
docker compose up -d
```

### Stop services
```bash
docker compose down
```

### Stop and remove volumes (⚠️ deletes all data)
```bash
docker compose down -v
```

### Restart a specific service
```bash
docker compose restart kafka
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f postgres
```

### Execute commands in containers
```bash
# PostgreSQL
docker exec -it postgres psql -U postgres -d patient_monitoring

# Redis
docker exec -it redis redis-cli -a redis

# Kafka (list topics)
docker exec -it kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
```

## Environment Variables

The `.env` file in this directory contains all configuration. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_PORT` | 9092 | External Kafka port |
| `KAFKA_INTERNAL_PORT` | 29092 | Internal Kafka port for container communication |
| `POSTGRES_PORT` | 5432 | PostgreSQL port |
| `POSTGRES_USER` | postgres | PostgreSQL username |
| `POSTGRES_PASSWORD` | postgres | PostgreSQL password |
| `POSTGRES_DB` | patient_monitoring | PostgreSQL database name |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_PASSWORD` | redis | Redis password |
| `KAFKA_UI_PORT` | 8080 | Kafka UI web interface port |

## Troubleshooting

### Services not starting

1. Check if ports are already in use:
   ```bash
   # Windows
   netstat -ano | findstr :9092
   
   # Linux/Mac
   lsof -i :9092
   ```

2. Check Docker logs:
   ```bash
   docker compose logs [service-name]
   ```

### Kafka not accessible

- Ensure Kafka health check passes: `docker compose ps`
- Check Kafka logs: `docker compose logs kafka`
- Verify network connectivity: `docker network inspect patient-monitoring-network`

### PostgreSQL connection issues

- Verify credentials match `.env` file
- Check if PostgreSQL is healthy: `docker compose ps postgres`
- Test connection: `docker exec -it postgres psql -U postgres -d patient_monitoring`

### Redis connection issues

- Verify password matches `.env` file
- Test connection: `docker exec -it redis redis-cli -a redis ping`

## Development Tips

1. **Keep services running:** Use `docker compose up -d` to run in detached mode
2. **Monitor logs:** Use `docker compose logs -f` to tail logs from all services
3. **Reset data:** Use `docker compose down -v` to completely reset (⚠️ deletes all data)
4. **Network isolation:** All services are on the same network, so they can communicate by container name

## Next Steps

Once infrastructure is running:

1. Connect your application services to these infrastructure services
2. Use Kafka UI to monitor topics and messages
3. Use PostgreSQL for persistent data storage
4. Use Redis for caching and session storage

