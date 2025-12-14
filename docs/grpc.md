# gRPC Service Definitions

This document summarizes all gRPC services defined in the Patient Monitoring System. All services use Protocol Buffers (protobuf) for message serialization and gRPC for communication.

## Proto Files

All `.proto` files are located in the `proto/` directory:

- `telemetry_gateway.proto` - Device to gateway communication
- `registry.proto` - Service to registry communication
- `anomaly.proto` - Rules/ML to anomaly service communication
- `telemetry.proto` - Additional telemetry definitions (if present)

## Services

### 1. TelemetryGateway Service

**Package**: `telemetry.gateway`  
**File**: `proto/telemetry_gateway.proto`  
**Server**: telemetry-gateway (port 50052)

#### Methods

##### SendMeasurements

Receives raw measurements from medical devices.

**Request**: `SendMeasurementsRequest`
```protobuf
message SendMeasurementsRequest {
  string version = 1;                    // Schema version
  string device_id = 2;                  // Device identifier
  string device_type = 3;                // Optional device type
  string timestamp = 4;                   // ISO 8601 timestamp
  repeated Measurement measurements = 5; // Array of measurements
  map<string, string> device_metadata = 6; // Optional device metadata
}
```

**Response**: `SendMeasurementsResponse`
```protobuf
message SendMeasurementsResponse {
  string version = 1;      // Schema version
  Status status = 2;       // Operation status
  string message = 3;      // Optional status message
  string event_id = 4;     // Event ID if successful
  string timestamp = 5;     // ISO 8601 timestamp
}
```

**Status Codes**:
- `STATUS_SUCCESS` - Measurements successfully ingested
- `STATUS_VALIDATION_ERROR` - Invalid measurement data
- `STATUS_DEVICE_NOT_FOUND` - Device not registered
- `STATUS_INTERNAL_ERROR` - Server error

**Use Case**: Medical devices send raw measurements to the gateway service via gRPC.

---

### 2. Registry Service

**Package**: `registry`  
**File**: `proto/registry.proto`  
**Server**: registry (port 50051)

#### Methods

##### GetDevice

Retrieve device information by device ID.

**Request**: `GetDeviceRequest`
```protobuf
message GetDeviceRequest {
  string version = 1;    // Schema version
  string device_id = 2; // Device identifier
}
```

**Response**: `GetDeviceResponse`
```protobuf
message GetDeviceResponse {
  string version = 1;  // Schema version
  Status status = 2;   // Operation status
  Device device = 3;    // Device information (if found)
  string timestamp = 4; // ISO 8601 timestamp
}
```

**Device Message**:
```protobuf
message Device {
  string device_id = 1;
  string device_type = 2;
  string patient_id = 3;
  DeviceStatus status = 4;
  map<string, string> metadata = 5;
  string registered_at = 6;
  string updated_at = 7;
}
```

##### GetPatient

Retrieve patient information by patient ID.

**Request**: `GetPatientRequest`
```protobuf
message GetPatientRequest {
  string version = 1;     // Schema version
  string patient_id = 2;  // Patient identifier
}
```

**Response**: `GetPatientResponse`
```protobuf
message GetPatientResponse {
  string version = 1;   // Schema version
  Status status = 2;     // Operation status
  Patient patient = 3;    // Patient information (if found)
  string timestamp = 4;   // ISO 8601 timestamp
}
```

**Patient Message**:
```protobuf
message Patient {
  string patient_id = 1;
  int32 age = 2;
  Gender gender = 3;
  repeated string medical_conditions = 4;
  repeated string medications = 5;
  repeated string allergies = 6;
  map<string, string> metadata = 7;
  string registered_at = 8;
  string updated_at = 9;
}
```

##### GetThresholdProfile

Retrieve threshold profile for a patient or device.

**Request**: `GetThresholdProfileRequest`
```protobuf
message GetThresholdProfileRequest {
  string version = 1;     // Schema version
  string patient_id = 2; // Patient identifier (required)
  string device_id = 3;  // Optional device identifier
}
```

**Response**: `GetThresholdProfileResponse`
```protobuf
message GetThresholdProfileResponse {
  string version = 1;        // Schema version
  Status status = 2;         // Operation status
  ThresholdProfile profile = 3; // Threshold profile (if found)
  string timestamp = 4;       // ISO 8601 timestamp
}
```

**ThresholdProfile Message**:
```protobuf
message ThresholdProfile {
  string profile_id = 1;
  string patient_id = 2;
  string device_id = 3;
  VitalThreshold heart_rate = 4;
  BloodPressureThreshold blood_pressure = 5;
  VitalThreshold temperature = 6;
  VitalThreshold oxygen_saturation = 7;
  VitalThreshold respiratory_rate = 8;
  string created_at = 9;
  string updated_at = 10;
}
```

**Status Codes**:
- `STATUS_SUCCESS` - Request successful
- `STATUS_NOT_FOUND` - Resource not found
- `STATUS_INVALID_REQUEST` - Invalid request parameters
- `STATUS_INTERNAL_ERROR` - Server error

**Use Case**: Services query the registry for device, patient, and threshold information during telemetry enrichment.

---

### 3. AnomalyDetection Service

**Package**: `anomaly`  
**File**: `proto/anomaly.proto`  
**Server**: anomaly-service (port 50053)

#### Methods

##### ScoreVitals

Scores vital signs measurements for anomalies using ML models or rule-based systems.

**Request**: `ScoreVitalsRequest`
```protobuf
message ScoreVitalsRequest {
  string version = 1;                    // Schema version
  string patient_id = 2;                 // Patient identifier
  string device_id = 3;                  // Device identifier
  string timestamp = 4;                  // ISO 8601 timestamp
  VitalSigns vitals = 5;                 // Vital signs to score
  PatientContext patient_context = 6;    // Optional patient context
  HistoricalContext historical_context = 7; // Optional historical context
}
```

**VitalSigns Message**:
```protobuf
message VitalSigns {
  VitalMeasurement heart_rate = 1;
  BloodPressureMeasurement blood_pressure = 2;
  VitalMeasurement temperature = 3;
  VitalMeasurement oxygen_saturation = 4;
  VitalMeasurement respiratory_rate = 5;
}
```

**Response**: `ScoreVitalsResponse`
```protobuf
message ScoreVitalsResponse {
  string version = 1;              // Schema version
  Status status = 2;               // Operation status
  string patient_id = 3;           // Patient identifier
  string timestamp = 4;             // ISO 8601 timestamp
  AnomalyScores anomaly_scores = 5; // Scores for each vital sign
  RiskScore overall_risk_score = 6; // Combined risk score
  string message = 7;               // Optional status message
  ScoringMetadata metadata = 8;     // Scoring process metadata
}
```

**AnomalyScore Message**:
```protobuf
message AnomalyScore {
  double score = 1;              // Score (0.0 = normal, 1.0 = highly anomalous)
  Severity severity = 2;         // Severity level
  string model_version = 3;       // Scoring model version
  repeated string factors = 4;    // Contributing factors
  string explanation = 5;         // Optional explanation
}
```

**Status Codes**:
- `STATUS_SUCCESS` - Scoring successful
- `STATUS_INVALID_REQUEST` - Invalid request data
- `STATUS_MODEL_ERROR` - Error in scoring model
- `STATUS_INTERNAL_ERROR` - Server error

**Use Case**: Rules engine calls this service to score enriched telemetry for anomalies before generating alerts.

## Message Versioning

All gRPC messages include a `version` field:
- Version format: `"major.minor.patch"` (e.g., `"1.0.0"`)
- Clients should specify the version they support
- Servers should handle multiple versions during migration

## Timestamp Format

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

**Generated Output**: `services/*/src/generated/` or `services/*/generated/`

**Usage**:
```bash
make proto
# or
bash scripts/generate-proto-ts.sh
```

### Python Generation (FastAPI)

**Script**: `scripts/generate-proto-py.sh`

**Generated Output**: `services/*/generated/`

**Usage**:
```bash
make proto
# or
bash scripts/generate-proto-py.sh
```

## Service Ports

| Service | gRPC Port | HTTP Port |
|---------|----------|-----------|
| telemetry-gateway | 50052 | 3000 |
| registry | 50051 | 8000 |
| anomaly-service | 50053 | 8003 |

## References

- [Protocol Buffers Language Guide](https://protobuf.dev/programming-guides/proto3/)
- [gRPC Documentation](https://grpc.io/docs/)
- [ISO 8601 Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)

