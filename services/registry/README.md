# Registry Service

A FastAPI-based CRUD service for managing patients, devices, and threshold profiles. Provides both REST API and gRPC endpoints.

## Features

- **REST CRUD API** for patients, devices, and threshold profiles
- **gRPC Server** implementing `GetDevice`, `GetPatient`, and `GetThresholdProfile`
- **PostgreSQL** database with SQLAlchemy ORM
- **Alembic** migrations for database schema management
- **Pydantic** validation for all inputs
- **Docker** support with automatic migrations and seeding

## Data Models

### Patient
- `id` (UUID): Primary key
- `full_name` (string): Patient's full name
- `age` (integer): Patient's age (0-150)
- `sex` (string): Patient's sex (M, F, or Other)
- `created_at` (datetime): Creation timestamp

### Device
- `id` (UUID): Primary key
- `serial` (string): Unique device serial number
- `firmware` (string): Device firmware version
- `patient_id` (UUID, nullable): Associated patient ID
- `created_at` (datetime): Creation timestamp

### ThresholdProfile
- `id` (UUID): Primary key
- `patient_id` (UUID): Associated patient ID (unique)
- `hr_min` (float): Minimum heart rate threshold
- `hr_max` (float): Maximum heart rate threshold
- `spo2_min` (float): Minimum SpO2 threshold (0-100)
- `temp_min` (float): Minimum temperature threshold
- `temp_max` (float): Maximum temperature threshold

## REST API Endpoints

### Patients

- `POST /patients` - Create a new patient
- `GET /patients` - List all patients (with pagination: `skip`, `limit`)
- `GET /patients/{patient_id}` - Get a patient by ID

### Devices

- `POST /devices` - Create a new device
- `GET /devices` - List all devices (with pagination: `skip`, `limit`)
- `GET /devices/{device_id}` - Get a device by ID
- `PATCH /devices/{device_id}` - Update a device (patient_id, firmware)
- `POST /devices/link` - Link a device to a patient

### Threshold Profiles

- `POST /thresholds` - Create a new threshold profile
- `GET /thresholds` - List all threshold profiles (with pagination: `skip`, `limit`)
- `GET /thresholds/{patient_id}` - Get threshold profile by patient ID

### Health Check

- `GET /health` - Service health check

## gRPC Endpoints

The service implements the `Registry` service from `proto/registry.proto`:

- `GetDevice(GetDeviceRequest)` - Retrieve device information by device ID
- `GetPatient(GetPatientRequest)` - Retrieve patient information by patient ID
- `GetThresholdProfile(GetThresholdProfileRequest)` - Retrieve threshold profile by patient ID

gRPC server runs on port `50051` by default.

## Local Development

### Prerequisites

- Python 3.10+
- PostgreSQL 16+ (or use Docker Compose)
- `protoc` (Protocol Buffers compiler)

### Setup

1. **Install dependencies:**
   ```bash
   cd services/registry
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file or set environment variables:
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/patient_monitoring
   PORT=8000
   GRPC_PORT=50051
   ```

3. **Generate gRPC stubs:**
   ```bash
   # From project root
   make proto
   
   # Or manually:
   python -m grpc_tools.protoc \
     --proto_path=../../proto \
     --python_out=generated \
     --grpc_python_out=generated \
     ../../proto/registry.proto
   ```

4. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Seed initial data (optional):**
   ```bash
   python seed.py
   ```

6. **Start the service:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The service will be available at:
- REST API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- gRPC: localhost:50051

## Docker

### Build and Run

```bash
# From project root
docker build -t registry-service -f services/registry/Dockerfile .

# Run with Docker Compose (recommended)
docker compose -f infra/docker-compose.yml up registry-service
```

The Dockerfile automatically:
1. Runs Alembic migrations on startup
2. Seeds initial data (5 patients, 5 devices, 5 threshold profiles)
3. Starts the FastAPI service

### Docker Compose Integration

Add to `infra/docker-compose.yml`:

```yaml
registry-service:
  build:
    context: ..
    dockerfile: services/registry/Dockerfile
  container_name: registry-service
  ports:
    - "${REGISTRY_PORT:-8000}:8000"
    - "${REGISTRY_GRPC_PORT:-50051}:50051"
  environment:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/patient_monitoring
    PORT: 8000
    GRPC_PORT: 50051
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - patient-monitoring-network
  restart: unless-stopped
```

## API Examples

### Create a Patient

```bash
curl -X POST "http://localhost:8000/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "age": 45,
    "sex": "M"
  }'
```

### Create a Device

```bash
curl -X POST "http://localhost:8000/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "serial": "DEV001",
    "firmware": "v1.2.3",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Link Device to Patient

```bash
curl -X POST "http://localhost:8000/devices/link" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "660e8400-e29b-41d4-a716-446655440000",
    "patient_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Create Threshold Profile

```bash
curl -X POST "http://localhost:8000/thresholds" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "550e8400-e29b-41d4-a716-446655440000",
    "hr_min": 60,
    "hr_max": 100,
    "spo2_min": 95,
    "temp_min": 36.1,
    "temp_max": 37.2
  }'
```

### Get Patient via gRPC

Using `grpcurl`:

```bash
grpcurl -plaintext \
  -d '{"version": "1.0.0", "patient_id": "550e8400-e29b-41d4-a716-446655440000"}' \
  localhost:50051 \
  registry.Registry/GetPatient
```

## Project Structure

```
services/registry/
├── alembic/              # Alembic migration scripts
│   ├── versions/         # Migration versions
│   ├── env.py           # Alembic environment
│   └── script.py.mako   # Migration template
├── generated/            # Generated gRPC stubs (from proto/)
├── alembic.ini          # Alembic configuration
├── config.py            # Application configuration
├── crud.py              # CRUD operations
├── database.py          # Database setup
├── Dockerfile           # Docker build file
├── main.py              # FastAPI application and gRPC server
├── models.py            # SQLAlchemy models
├── requirements.txt     # Python dependencies
├── schemas.py           # Pydantic schemas
├── seed.py              # Seed script
└── README.md            # This file
```

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
alembic downgrade -1
```

## Testing

### Manual Testing

1. Use the interactive API docs at http://localhost:8000/docs
2. Test gRPC endpoints using `grpcurl` or a gRPC client
3. Verify database state using PostgreSQL client

### Example Test Flow

1. Create a patient
2. Create a device
3. Link device to patient
4. Create threshold profile for patient
5. Query via REST API
6. Query via gRPC

## Troubleshooting

### gRPC stubs not found

Ensure you've generated the gRPC stubs:
```bash
make proto
```

### Database connection errors

- Verify PostgreSQL is running
- Check `DATABASE_URL` environment variable
- Ensure database exists: `createdb patient_monitoring`

### Migration errors

- Ensure database is accessible
- Check Alembic version table exists
- Run `alembic current` to check migration state

## License

[Add your license here]

