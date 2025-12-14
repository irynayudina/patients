# Kafka Event Schemas

This document describes all Kafka events used in the Patient Monitoring System. All events include correlation IDs (`event_id` and `trace_id`) for end-to-end tracing.

## Event Types

1. **telemetry.raw** - Raw telemetry data from medical devices
2. **telemetry.normalized** - Normalized and validated telemetry data
3. **telemetry.enriched** - Enriched telemetry with patient context
4. **telemetry.scored** - Telemetry with anomaly scores
5. **alerts.raised** - Alert events when anomalies are detected

## Common Event Structure

All events follow a common structure:

```json
{
  "event_id": "unique_event_identifier",
  "trace_id": "correlation_id_for_tracing",
  "event_type": "event.type.name",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source_event_id": "previous_event_id_if_applicable",
  // ... event-specific fields
}
```

### Common Fields

- **event_id** (string, required): Unique identifier for this event
- **trace_id** (string, required): Correlation ID for tracing this event through the system
- **event_type** (string, required): Event type identifier (e.g., "telemetry.raw")
- **version** (string, optional): Schema version (default: "1.0.0")
- **timestamp** (string, required): ISO 8601 timestamp when the event was created
- **source_event_id** (string, optional): Event ID of the source event that triggered this event

## Event Schemas

### 1. telemetry.raw

**Topic**: `telemetry.raw`  
**Producer**: telemetry-gateway  
**Consumer**: telemetry-normalizer

Raw telemetry data from medical devices.

**Schema**: See [docs/events/telemetry.raw.json](events/telemetry.raw.json)

**Example**:
```json
{
  "event_id": "evt_550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "trace_550e8400-e29b-41d4-a716-446655440000",
  "event_type": "telemetry.raw",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "device_id": "device_12345",
  "device_type": "blood_pressure_monitor",
  "measurements": [
    {
      "metric": "systolic_pressure",
      "value": 120.5,
      "unit": "mmHg"
    }
  ],
  "metadata": {
    "firmware_version": "v2.1.3",
    "battery_level": 85
  }
}
```

### 2. telemetry.normalized

**Topic**: `telemetry.normalized`  
**Producer**: telemetry-normalizer  
**Consumer**: telemetry-enrichment

Normalized and validated telemetry data.

**Schema**: See [docs/events/telemetry.normalized.json](events/telemetry.normalized.json)

**Example**:
```json
{
  "event_id": "evt_660e8400-e29b-41d4-a716-446655440001",
  "trace_id": "trace_550e8400-e29b-41d4-a716-446655440000",
  "event_type": "telemetry.normalized",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source_event_id": "evt_550e8400-e29b-41d4-a716-446655440000",
  "device_id": "device_12345",
  "patient_id": "patient_78901",
  "vitals": {
    "heart_rate": {
      "value": 72,
      "unit": "bpm",
      "timestamp": "2024-01-15T10:30:00.000Z"
    }
  },
  "validation_status": "valid"
}
```

### 3. telemetry.enriched

**Topic**: `telemetry.enriched`  
**Producer**: telemetry-enrichment  
**Consumer**: rules-engine

Enriched telemetry with patient context and thresholds.

**Schema**: See [docs/events/telemetry.enriched.json](events/telemetry.enriched.json)

**Example**:
```json
{
  "event_id": "evt_770e8400-e29b-41d4-a716-446655440002",
  "trace_id": "trace_550e8400-e29b-41d4-a716-446655440000",
  "event_type": "telemetry.enriched",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source_event_id": "evt_660e8400-e29b-41d4-a716-446655440001",
  "device_id": "device_12345",
  "patient_id": "patient_78901",
  "patientProfile": {
    "age": 45,
    "sex": "male"
  },
  "thresholds": {
    "heart_rate": { "max": 100, "min": 60 }
  },
  "vitals": {
    "heart_rate": {
      "value": 72,
      "unit": "bpm"
    }
  }
}
```

### 4. telemetry.scored

**Topic**: `telemetry.scored`  
**Producer**: rules-engine  
**Consumer**: analytics

Telemetry with anomaly scores from ML/rules engine.

**Schema**: See [docs/events/telemetry.scored.json](events/telemetry.scored.json)

**Example**:
```json
{
  "event_id": "evt_880e8400-e29b-41d4-a716-446655440003",
  "trace_id": "trace_550e8400-e29b-41d4-a716-446655440000",
  "event_type": "telemetry.scored",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "source_event_id": "evt_770e8400-e29b-41d4-a716-446655440002",
  "device_id": "device_12345",
  "patient_id": "patient_78901",
  "vitals": {
    "heart_rate": {
      "value": 72,
      "unit": "bpm"
    }
  },
  "anomaly_scores": {
    "heart_rate": {
      "score": 0.15,
      "severity": "normal"
    }
  },
  "overall_risk_score": {
    "score": 0.18,
    "severity": "low"
  }
}
```

### 5. alerts.raised

**Topic**: `alerts.raised`  
**Producer**: rules-engine  
**Consumers**: incident-service, notification-service, analytics

Alert events when anomalies are detected or thresholds exceeded.

**Schema**: See [docs/events/alerts.raised.json](events/alerts.raised.json)

**Example**:
```json
{
  "event_id": "alert_990e8400-e29b-41d4-a716-446655440004",
  "trace_id": "trace_550e8400-e29b-41d4-a716-446655440000",
  "event_type": "alerts.raised",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:05.000Z",
  "source_event_id": "evt_880e8400-e29b-41d4-a716-446655440003",
  "patient_id": "patient_78901",
  "device_id": "device_12345",
  "alert_type": "vital_sign_anomaly",
  "severity": "medium",
  "condition": {
    "description": "Heart rate elevated above baseline",
    "vital_sign": "heart_rate",
    "anomaly_score": 0.75
  }
}
```

## Event Versioning

- Events include a `version` field for schema versioning
- Consumers should validate version compatibility
- Breaking changes require version increments
- Multiple versions may be supported during migration periods

## Correlation IDs

All events include:
- **event_id**: Unique identifier for the specific event
- **trace_id**: Correlation ID that persists across the event pipeline

The `trace_id` is generated at the entry point (telemetry-gateway) and propagated through all downstream events, enabling end-to-end tracing of a single device reading through the entire system.

## References

- [JSON Schema Specification](https://json-schema.org/)
- [ISO 8601 Date/Time Format](https://en.wikipedia.org/wiki/ISO_8601)
- [Kafka Event Streaming](https://kafka.apache.org/documentation/)

