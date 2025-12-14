# Shared Contracts Documentation

This document describes the shared contracts used across the Med Telemetry Platform, including Kafka event schemas and gRPC service definitions.

## Overview

The platform uses two main communication patterns:
1. **Kafka Events**: Asynchronous event streaming for telemetry data pipeline
2. **gRPC Services**: Synchronous service-to-service communication

All contracts are versioned to support evolution over time.

## Kafka Event Schemas

Kafka events are defined as JSON schemas with examples. All events use ISO 8601 timestamps for consistency.

### Event Types

1. **telemetry.raw** - Raw telemetry data from medical devices
2. **telemetry.normalized** - Normalized and validated telemetry data
3. **telemetry.enriched** - Enriched telemetry with patient context
4. **telemetry.scored** - Telemetry with anomaly scores
5. **alerts.raised** - Alert events when anomalies are detected

### Event Schema Location

Event schemas are located in `docs/events/`:
- `telemetry.raw.json`
- `telemetry.normalized.json`
- `telemetry.enriched.json`
- `telemetry.scored.json`
- `alerts.raised.json`

Each schema file includes:
- JSON Schema definition with required/optional fields
- Example payload
- Field descriptions

### Event Schema Structure

All events follow a common structure:
```json
{
  "event_id": "unique_event_identifier",
  "event_type": "event.type.name",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source_event_id": "previous_event_id_if_applicable",
  // ... event-specific fields
}
```

### Event Versioning

- Events include a `version` field for schema versioning
- Consumers should validate version compatibility
- Breaking changes require version increments
- Multiple versions may be supported during migration periods

## gRPC Protocol Buffers

gRPC services are defined using Protocol Buffers (protobuf). All messages use ISO 8601 string timestamps for simplicity.

### Proto Files

Proto files are located in `proto/`:

1. **telemetry_gateway.proto** - Device to gateway communication
   - Service: `TelemetryGateway`
   - Method: `SendMeasurements` (device -> gateway)

2. **registry.proto** - Service to registry communication
   - Service: `Registry`
   - Methods:
     - `GetDevice` - Retrieve device information
     - `GetPatient` - Retrieve patient information
     - `GetThresholdProfile` - Retrieve threshold profiles (optional)

3. **anomaly.proto** - Rules/ML to anomaly service communication
   - Service: `AnomalyDetection`
   - Method: `ScoreVitals` (rules -> anomaly service)

### Message Versioning

All gRPC messages include a `version` field:
```protobuf
message SomeRequest {
  string version = 1;  // Schema version
  // ... other fields
}
```

- Version format: `"major.minor.patch"` (e.g., `"1.0.0"`)
- Clients should specify the version they support
- Servers should handle multiple versions during migration

### Timestamp Format

All timestamps in gRPC messages use ISO 8601 string format:
- Format: `"2024-01-15T10:30:00.000Z"`
- Timezone: UTC (Z suffix)
- Precision: Milliseconds

Example:
```protobuf
string timestamp = 4;  // ISO 8601 format: "2024-01-15T10:30:00.000Z"
```

## Code Generation

Generated code stubs are created from proto files for both TypeScript (NestJS) and Python (FastAPI) services.

### TypeScript Generation (NestJS)

**Script**: `scripts/generate-proto-ts.sh`

**Requirements**:
- `protoc` (Protocol Buffers compiler)
- `ts-proto` plugin (installed via npm in nestjs-service)
- Node.js dependencies in `services/nestjs-service/`

**Generated Output**: `services/nestjs-service/src/generated/`

**Compatibility**: Generated code is compatible with `@grpc/grpc-js`

**Usage**:
```bash
# From project root
bash scripts/generate-proto-ts.sh

# Or from nestjs-service directory
npm run proto:generate

# Or using Make
make proto
```

**Generation Options**:
- `nestJs=true` - Generates NestJS-compatible code
- `outputServices=grpc-js` - Uses @grpc/grpc-js compatible output
- `esModuleInterop=true` - Enables ES module interop
- `useExactTypes=false` - Allows type flexibility

### Python Generation (FastAPI)

**Script**: `scripts/generate-proto-py.sh`

**Requirements**:
- `protoc` (Protocol Buffers compiler)
- `grpcio-tools` Python package
- Python 3.10+

**Generated Output**: `services/fastapi-service/generated/`

**Usage**:
```bash
# From project root
bash scripts/generate-proto-py.sh

# Or using Make
make proto
```

**Installation**:
The script automatically installs `grpcio-tools` if not available:
```bash
pip install grpcio-tools
```

**Generated Files**:
- `*_pb2.py` - Message classes
- `*_pb2_grpc.py` - Service stubs and servers

### Generating All Stubs

To generate stubs for all services:

```bash
make proto
```

This runs both TypeScript and Python generation scripts.

## Service Contracts

### TelemetryGateway Service

**Package**: `telemetry.gateway`

**Service**: `TelemetryGateway`

**Method**: `SendMeasurements`
- **Request**: `SendMeasurementsRequest`
  - `version` (string) - Schema version
  - `device_id` (string) - Device identifier
  - `device_type` (string, optional) - Device type
  - `timestamp` (string) - ISO 8601 timestamp
  - `measurements` (repeated Measurement) - Array of measurements
  - `device_metadata` (map<string, string>, optional) - Device metadata
- **Response**: `SendMeasurementsResponse`
  - `version` (string) - Schema version
  - `status` (Status enum) - Operation status
  - `message` (string, optional) - Status message
  - `event_id` (string, optional) - Event ID if successful
  - `timestamp` (string) - ISO 8601 timestamp

**Use Case**: Medical devices send raw measurements to the gateway service.

### Registry Service

**Package**: `registry`

**Service**: `Registry`

**Method**: `GetDevice`
- **Request**: `GetDeviceRequest`
  - `version` (string) - Schema version
  - `device_id` (string) - Device identifier
- **Response**: `GetDeviceResponse`
  - `version` (string) - Schema version
  - `status` (Status enum) - Operation status
  - `device` (Device, optional) - Device information
  - `timestamp` (string) - ISO 8601 timestamp

**Method**: `GetPatient`
- **Request**: `GetPatientRequest`
  - `version` (string) - Schema version
  - `patient_id` (string) - Patient identifier
- **Response**: `GetPatientResponse`
  - `version` (string) - Schema version
  - `status` (Status enum) - Operation status
  - `patient` (Patient, optional) - Patient information
  - `timestamp` (string) - ISO 8601 timestamp

**Method**: `GetThresholdProfile` (Optional)
- **Request**: `GetThresholdProfileRequest`
  - `version` (string) - Schema version
  - `patient_id` (string) - Patient identifier
  - `device_id` (string, optional) - Device identifier
- **Response**: `GetThresholdProfileResponse`
  - `version` (string) - Schema version
  - `status` (Status enum) - Operation status
  - `profile` (ThresholdProfile, optional) - Threshold profile
  - `timestamp` (string) - ISO 8601 timestamp

**Use Case**: Services query the registry for device, patient, and threshold information.

### AnomalyDetection Service

**Package**: `anomaly`

**Service**: `AnomalyDetection`

**Method**: `ScoreVitals`
- **Request**: `ScoreVitalsRequest`
  - `version` (string) - Schema version
  - `patient_id` (string) - Patient identifier
  - `device_id` (string) - Device identifier
  - `timestamp` (string) - ISO 8601 timestamp
  - `vitals` (VitalSigns) - Vital signs to score
  - `patient_context` (PatientContext, optional) - Patient context
  - `historical_context` (HistoricalContext, optional) - Historical data
- **Response**: `ScoreVitalsResponse`
  - `version` (string) - Schema version
  - `status` (Status enum) - Operation status
  - `patient_id` (string) - Patient identifier
  - `timestamp` (string) - ISO 8601 timestamp
  - `anomaly_scores` (AnomalyScores) - Scores for each vital sign
  - `overall_risk_score` (RiskScore) - Combined risk score
  - `message` (string, optional) - Status message
  - `metadata` (ScoringMetadata) - Scoring process metadata

**Use Case**: Rules engine or ML service scores vital signs for anomalies.

## Development Workflow

### 1. Define or Update Contracts

**For Kafka Events**:
1. Update or create JSON schema in `docs/events/`
2. Include example payload
3. Document required vs optional fields
4. Update version if breaking changes

**For gRPC Services**:
1. Update or create `.proto` file in `proto/`
2. Define messages with version fields
3. Use ISO 8601 string timestamps
4. Document service methods and use cases

### 2. Generate Code Stubs

After updating contracts, generate stubs:

```bash
make proto
```

This generates:
- TypeScript stubs for NestJS service
- Python stubs for FastAPI service

### 3. Implement Services

Use generated stubs in service implementations:

**NestJS Example**:
```typescript
import { TelemetryGatewayService } from './generated/telemetry_gateway.pb';
// Use generated service classes
```

**FastAPI Example**:
```python
from generated import telemetry_gateway_pb2
from generated import telemetry_gateway_pb2_grpc
# Use generated message and service classes
```

### 4. Test Contracts

- Validate event schemas against JSON Schema
- Test gRPC services with generated clients
- Verify version compatibility
- Test timestamp parsing/formatting

## Versioning Strategy

### Event Versioning

- **Major version** (X.0.0): Breaking changes (removed required fields, type changes)
- **Minor version** (0.X.0): New optional fields, new event types
- **Patch version** (0.0.X): Documentation updates, bug fixes

### Proto Versioning

- **Major version** (X.0.0): Breaking changes (removed fields, changed types)
- **Minor version** (0.X.0): New optional fields, new services/methods
- **Patch version** (0.0.X): Documentation updates, bug fixes

### Migration Strategy

1. **Additive Changes**: New optional fields can be added without version bump
2. **Breaking Changes**: Require version increment and migration plan
3. **Deprecation**: Mark deprecated fields, support for 2 versions, then remove
4. **Backward Compatibility**: Support previous version for transition period

## Best Practices

1. **Always include version fields** in messages and events
2. **Use ISO 8601 timestamps** consistently
3. **Document required vs optional fields** clearly
4. **Provide example payloads** for all schemas
5. **Validate schemas** before deploying
6. **Test version compatibility** during development
7. **Update contracts.md** when adding new contracts
8. **Regenerate stubs** after proto changes
9. **Commit generated code** (or document in .gitignore if not)
10. **Use semantic versioning** for contract versions

## Troubleshooting

### Generation Issues

**TypeScript Generation Fails**:
- Ensure `protoc` is installed: `brew install protobuf` (macOS) or download from protobuf releases
- Check `ts-proto` is installed: `cd services/nestjs-service && npm install`
- Verify proto file syntax: `protoc --proto_path=proto proto/*.proto --dry-run`

**Python Generation Fails**:
- Install `grpcio-tools`: `pip install grpcio-tools`
- Ensure Python 3.10+ is used
- Check proto file syntax

### Runtime Issues

**gRPC Connection Errors**:
- Verify service ports match docker-compose.yml
- Check service names in network configuration
- Ensure generated stubs match proto definitions

**Event Schema Validation Errors**:
- Validate JSON against schema using JSON Schema validator
- Check timestamp format (ISO 8601)
- Verify required fields are present

## References

- [Protocol Buffers Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [gRPC Documentation](https://grpc.io/docs/)
- [JSON Schema Specification](https://json-schema.org/)
- [ISO 8601 Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [Kafka Event Streaming](https://kafka.apache.org/documentation/)

