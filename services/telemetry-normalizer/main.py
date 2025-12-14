"""
Telemetry Normalizer Service

Consumes raw telemetry from Kafka, normalizes metrics, and produces normalized events.
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

from config import settings
from logging_config import setup_logging

# Configure standardized logging
logger = setup_logging("telemetry-normalizer", os.getenv("LOG_LEVEL", "INFO"))

# Global Kafka consumer and producer
consumer: Optional[AIOKafkaConsumer] = None
producer: Optional[AIOKafkaProducer] = None


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max"""
    return max(min_val, min(max_val, value))


def parse_timestamp(timestamp: Any) -> str:
    """
    Parse and validate timestamp, return ISO 8601 format string.
    Handles various timestamp formats.
    """
    if isinstance(timestamp, str):
        try:
            # Try parsing ISO 8601 format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat().replace('+00:00', 'Z')
        except (ValueError, AttributeError):
            try:
                # Try parsing as Unix timestamp (seconds or milliseconds)
                if '.' in timestamp:
                    ts = float(timestamp)
                else:
                    ts = int(timestamp)
                
                # If timestamp is less than year 2000 in seconds, assume milliseconds
                if ts < 946684800:  # Jan 1, 2000 in seconds
                    ts = ts / 1000.0
                
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                return dt.isoformat().replace('+00:00', 'Z')
            except (ValueError, OSError):
                pass
    
    elif isinstance(timestamp, (int, float)):
        # Unix timestamp
        ts = float(timestamp)
        if ts < 946684800:  # Assume milliseconds if too small
            ts = ts / 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')
    
    # Fallback to current time
    logger.warning(f"Could not parse timestamp: {timestamp}, using current time")
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def normalize_metric_name(metric: str) -> str:
    """Normalize metric name to standard format"""
    metric_lower = metric.lower().strip()
    
    # Map common variations to standard names
    metric_map = {
        'hr': 'heart_rate',
        'heartrate': 'heart_rate',
        'heart_rate': 'heart_rate',
        'pulse': 'heart_rate',
        'spo2': 'oxygen_saturation',
        'o2sat': 'oxygen_saturation',
        'oxygen_saturation': 'oxygen_saturation',
        'o2': 'oxygen_saturation',
        'temp': 'temperature',
        'temperature': 'temperature',
        'body_temp': 'temperature',
        'bp': 'blood_pressure',
        'blood_pressure': 'blood_pressure',
        'systolic': 'systolic_pressure',
        'diastolic': 'diastolic_pressure',
        'rr': 'respiratory_rate',
        'respiratory_rate': 'respiratory_rate',
        'respiration': 'respiratory_rate',
    }
    
    return metric_map.get(metric_lower, metric_lower)


def extract_patient_id(raw_event: Dict[str, Any]) -> str:
    """
    Extract patient_id from raw event.
    Checks metadata first, then uses a placeholder if not found.
    """
    # Check metadata
    if 'metadata' in raw_event and isinstance(raw_event['metadata'], dict):
        if 'patient_id' in raw_event['metadata']:
            return str(raw_event['metadata']['patient_id'])
    
    # Check if patient_id is directly in the event
    if 'patient_id' in raw_event:
        return str(raw_event['patient_id'])
    
    # Placeholder - in production, this might query a registry service
    # For now, we'll use a pattern based on device_id or generate a placeholder
    device_id = raw_event.get('device_id', 'unknown')
    return f"patient_from_{device_id}"


def normalize_telemetry(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw telemetry event.
    
    Args:
        raw_event: Raw telemetry event from Kafka
        
    Returns:
        Normalized telemetry event
    """
    # Extract trace_id from source event, or generate new one if missing
    trace_id = raw_event.get('trace_id')
    if not trace_id:
        trace_id = f"trace_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
    
    # Parse and validate timestamp
    event_timestamp = parse_timestamp(raw_event.get('timestamp'))
    
    # Extract measurements
    measurements = raw_event.get('measurements', [])
    
    # Initialize vitals structure
    vitals: Dict[str, Any] = {}
    warnings = []
    
    # Process each measurement
    for measurement in measurements:
        metric = normalize_metric_name(measurement.get('metric', ''))
        value = measurement.get('value')
        unit = measurement.get('unit', '')
        
        if value is None:
            continue
        
        value = float(value)
        
        # Normalize based on metric type
        if metric == 'heart_rate':
            clamped_value = clamp_value(value, settings.hr_min, settings.hr_max)
            if clamped_value != value:
                warnings.append(f"Heart rate clamped from {value} to {clamped_value} bpm")
            vitals['heart_rate'] = {
                'value': clamped_value,
                'unit': unit or 'bpm',
                'timestamp': event_timestamp
            }
        
        elif metric == 'oxygen_saturation':
            clamped_value = clamp_value(value, settings.spo2_min, settings.spo2_max)
            if clamped_value != value:
                warnings.append(f"SpO2 clamped from {value} to {clamped_value}%")
            vitals['oxygen_saturation'] = {
                'value': clamped_value,
                'unit': unit or 'percent',
                'timestamp': event_timestamp
            }
        
        elif metric == 'temperature':
            clamped_value = clamp_value(value, settings.temp_min, settings.temp_max)
            if clamped_value != value:
                warnings.append(f"Temperature clamped from {value} to {clamped_value}°C")
            vitals['temperature'] = {
                'value': clamped_value,
                'unit': unit or 'celsius',
                'timestamp': event_timestamp
            }
        
        elif metric == 'systolic_pressure':
            # Blood pressure handling
            if 'blood_pressure' not in vitals:
                vitals['blood_pressure'] = {
                    'systolic': None,
                    'diastolic': None,
                    'unit': 'mmHg',
                    'timestamp': event_timestamp
                }
            vitals['blood_pressure']['systolic'] = value
        
        elif metric == 'diastolic_pressure':
            if 'blood_pressure' not in vitals:
                vitals['blood_pressure'] = {
                    'systolic': None,
                    'diastolic': None,
                    'unit': 'mmHg',
                    'timestamp': event_timestamp
                }
            vitals['blood_pressure']['diastolic'] = value
        
        elif metric == 'respiratory_rate':
            vitals['respiratory_rate'] = {
                'value': value,
                'unit': unit or 'breaths_per_minute',
                'timestamp': event_timestamp
            }
    
    # Determine validation status
    validation_status = "valid"
    if warnings:
        validation_status = "warning"
    
    # Generate normalized event
    normalized_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    new_event_id = f"evt_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
    
    normalized_event = {
        'event_id': new_event_id,
        'trace_id': trace_id,
        'event_type': 'telemetry.normalized',
        'version': raw_event.get('version', '1.0.0'),
        'timestamp': event_timestamp,
        'source_event_id': raw_event.get('event_id'),
        'device_id': raw_event.get('device_id'),
        'patient_id': extract_patient_id(raw_event),
        'vitals': vitals,
        'validation_status': validation_status,
        'normalization_metadata': {
            'normalized_at': normalized_at,
            'normalization_rules_version': '1.0.0',
            'warnings': warnings if warnings else None
        }
    }
    
    # Remove None values from normalization_metadata warnings
    if normalized_event['normalization_metadata']['warnings'] is None:
        del normalized_event['normalization_metadata']['warnings']
    
    return normalized_event


async def process_message(message) -> None:
    """Process a single Kafka message"""
    offset = message.offset
    partition = message.partition
    
    try:
        # Parse message
        raw_event = json.loads(message.value.decode('utf-8'))
        event_id = raw_event.get('event_id', 'unknown')
        
        logger.info(
            f"Consumed message from offset {offset} (partition {partition})",
            extra={"event_id": event_id, "trace_id": raw_event.get("trace_id")}
        )
        
        # Normalize telemetry
        normalized_event = normalize_telemetry(raw_event)
        
        # Produce normalized event
        if producer is None:
            logger.error("Producer is not initialized, cannot produce message")
            return
        
        await producer.send(
            settings.kafka_topic_normalized,
            key=normalized_event['device_id'].encode('utf-8'),
            value=json.dumps(normalized_event).encode('utf-8')
        )
        
        logger.info(
            "Produced normalized event",
            extra={
                "event_id": normalized_event['event_id'],
                "trace_id": normalized_event.get('trace_id'),
                "source_event_id": event_id
            }
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON message at offset {offset} (partition {partition}): {e}")
    except KeyError as e:
        logger.error(f"Missing required field in message at offset {offset} (partition {partition}): {e}")
    except Exception as e:
        logger.error(f"Error processing message at offset {offset} (partition {partition}): {e}", exc_info=True)


async def consume_messages():
    """Consume messages from Kafka"""
    global consumer
    
    try:
        consumer = AIOKafkaConsumer(
            settings.kafka_topic_raw,
            bootstrap_servers=settings.kafka_brokers,
            group_id=settings.kafka_consumer_group,
            client_id=settings.kafka_client_id,
            value_deserializer=lambda m: m,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )
        
        await consumer.start()
        logger.info(f"Started consuming from topic: {settings.kafka_topic_raw}")
        
        try:
            async for message in consumer:
                await process_message(message)
        finally:
            await consumer.stop()
            
    except KafkaError as e:
        logger.error(f"Kafka error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in consumer: {e}", exc_info=True)


async def start_kafka():
    """Start Kafka consumer and producer"""
    global producer
    
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_brokers,
            client_id=settings.kafka_client_id,
            value_serializer=lambda v: v,
        )
        
        await producer.start()
        logger.info("Kafka producer started")
        
        # Start consuming in background
        asyncio.create_task(consume_messages())
        
    except Exception as e:
        logger.error(f"Failed to start Kafka: {e}", exc_info=True)
        raise


async def stop_kafka():
    """Stop Kafka consumer and producer"""
    global consumer, producer
    
    try:
        if consumer:
            await consumer.stop()
            logger.info("Kafka consumer stopped")
        
        if producer:
            await producer.stop()
            logger.info("Kafka producer stopped")
    except Exception as e:
        logger.error(f"Error stopping Kafka: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    await start_kafka()
    yield
    # Shutdown
    await stop_kafka()


app = FastAPI(
    title="Telemetry Normalizer Service",
    description="Normalizes raw telemetry data from medical devices",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Telemetry Normalizer Service",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    kafka_status = "unknown"
    try:
        if producer is None:
            kafka_status = "disconnected"
        else:
            # Producer is initialized, assume connected
            # (aiokafka doesn't expose connection state easily)
            kafka_status = "connected"
    except Exception as e:
        logger.warning(f"Error checking Kafka status: {e}")
        kafka_status = "unknown"
    
    return JSONResponse(
        content={
            "status": "healthy" if kafka_status == "connected" else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "service": settings.service_name,
            "kafka": kafka_status
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)

