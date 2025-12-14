"""
Rules Engine Service
Consumes telemetry.enriched, applies rules, calls AnomalyService, and produces telemetry.scored and alerts.raised
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
from rules_engine import RulesEngine, RuleResult
from anomaly_client import AnomalyClient
from logging_config import setup_logging

# Configure standardized logging
logger = setup_logging("rules-engine", os.getenv("LOG_LEVEL", "INFO"))

# Global Kafka consumer and producer
consumer: Optional[AIOKafkaConsumer] = None
producer: Optional[AIOKafkaProducer] = None

# Global services
rules_engine = RulesEngine()
anomaly_client = AnomalyClient()


def generate_event_id() -> str:
    """Generate a unique event ID"""
    return f"evt_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"


def generate_alert_id() -> str:
    """Generate a unique alert ID"""
    return f"alert_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"


def create_scored_event(enriched_event: Dict[str, Any], anomaly_result: Dict[str, Any]) -> Dict[str, Any]:
    """Create telemetry.scored event from enriched event and anomaly scores"""
    scored_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # Extract trace_id from source event, or generate new one if missing
    trace_id = enriched_event.get('trace_id')
    if not trace_id:
        trace_id = f"trace_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
    
    scored_event = {
        "event_id": generate_event_id(),
        "trace_id": trace_id,
        "event_type": "telemetry.scored",
        "version": enriched_event.get("version", "1.0.0"),
        "timestamp": enriched_event.get("timestamp"),
        "source_event_id": enriched_event.get("event_id"),
        "device_id": enriched_event.get("device_id"),
        "patient_id": enriched_event.get("patient_id"),
        "vitals": enriched_event.get("vitals", {}),
        "anomaly_scores": anomaly_result.get("anomaly_scores", {}),
        "overall_risk_score": anomaly_result.get("overall_risk_score", {}),
        "scoring_metadata": {
            "scored_at": scored_at,
            "scoring_engine": anomaly_result.get("metadata", {}).get("scoring_engine", "anomaly_detection"),
            "scoring_engine_version": anomaly_result.get("metadata", {}).get("scoring_engine_version", "1.0.0"),
            "processing_time_ms": anomaly_result.get("metadata", {}).get("processing_time_ms", 0)
        }
    }
    
    return scored_event


def create_alert_event(enriched_event: Dict[str, Any], scored_event: Dict[str, Any], 
                       severity: str, rules_triggered: list[RuleResult], 
                       anomaly_score: float) -> Dict[str, Any]:
    """Create alerts.raised event"""
    alert_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # Extract trace_id from scored event, or from enriched event, or generate new one
    trace_id = scored_event.get('trace_id') or enriched_event.get('trace_id')
    if not trace_id:
        trace_id = f"trace_{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:12]}"
    
    # Determine alert type
    alert_type = "vital_sign_anomaly"
    if len(rules_triggered) > 1:
        alert_type = "multi_vital_anomaly"
    elif any("combined" in rule.rule_id for rule in rules_triggered):
        alert_type = "critical_condition"
    
    # Build condition description
    condition_description = "; ".join([rule.message for rule in rules_triggered])
    
    # Extract metrics for details
    vitals = enriched_event.get("vitals", {})
    metrics = {}
    if "heart_rate" in vitals:
        metrics["heart_rate"] = vitals["heart_rate"]
    if "oxygen_saturation" in vitals:
        metrics["oxygen_saturation"] = vitals["oxygen_saturation"]
    if "temperature" in vitals:
        metrics["temperature"] = vitals["temperature"]
    
    alert_event = {
        "event_id": generate_alert_id(),
        "trace_id": trace_id,
        "event_type": "alerts.raised",
        "version": "1.0.0",
        "timestamp": alert_at,
        "source_event_id": scored_event.get("event_id"),
        "patient_id": enriched_event.get("patient_id"),
        "device_id": enriched_event.get("device_id"),
        "alert_type": alert_type,
        "severity": severity,
        "condition": {
            "description": condition_description,
            "vital_sign": "multiple" if len(rules_triggered) > 1 else (
                "heart_rate" if any("hr" in rule.rule_id for rule in rules_triggered) else
                "oxygen_saturation" if any("spo2" in rule.rule_id for rule in rules_triggered) else
                "temperature" if any("temp" in rule.rule_id for rule in rules_triggered) else
                "multiple"
            ),
            "anomaly_score": anomaly_score
        },
        "details": {
            "metrics": metrics,
            "rulesTriggered": [rule.rule_id for rule in rules_triggered],
            "anomalyScore": anomaly_score
        },
        "alert_metadata": {
            "raised_by": "rules-engine",
            "rule_version": "1.0.0",
            "acknowledged": False,
            "resolved": False
        }
    }
    
    # Add alertId, patientId, deviceId, type fields for compatibility (aliases)
    # Note: The schema uses event_id, patient_id, device_id, alert_type
    # but we keep both for compatibility with user requirements
    
    # Add patient context if available
    if "patient_context" in enriched_event:
        alert_event["patient_context"] = {
            "age": enriched_event["patient_context"].get("age"),
            "medical_conditions": enriched_event["patient_context"].get("medical_conditions", []),
            "current_medications": enriched_event["patient_context"].get("medications", [])
        }
    
    return alert_event


async def process_message(message) -> None:
    """Process a single Kafka message"""
    offset = message.offset
    partition = message.partition
    
    try:
        # Parse message
        enriched_event = json.loads(message.value.decode('utf-8'))
        event_id = enriched_event.get('event_id', 'unknown')
        patient_id = enriched_event.get('patient_id', 'unknown')
        device_id = enriched_event.get('device_id', 'unknown')
        
        logger.info(f"Processing enriched event: {event_id} for patient {patient_id}")
        
        # Extract vitals
        vitals = enriched_event.get('vitals', {})
        if not vitals:
            logger.warning(f"No vitals found in event {event_id}, skipping")
            return
        
        # Apply rules
        overall_severity, rules_triggered = rules_engine.evaluate_rules(vitals)
        logger.info(f"Rules evaluation for {event_id}: severity={overall_severity}, rules_triggered={len(rules_triggered)}")
        
        # Call AnomalyService via gRPC
        try:
            anomaly_result = anomaly_client.score_vitals(
                patient_id=patient_id,
                device_id=device_id,
                timestamp=enriched_event.get('timestamp'),
                vitals=vitals,
                patient_context=enriched_event.get('patient_context'),
                historical_context=enriched_event.get('historical_context')
            )
            logger.info(f"AnomalyService scored event {event_id}: overall_score={anomaly_result.get('overall_risk_score', {}).get('score', 0)}")
        except Exception as e:
            logger.error(f"Failed to call AnomalyService for event {event_id}: {e}", exc_info=True)
            # Continue with default scores if AnomalyService fails
            anomaly_result = {
                "anomaly_scores": {},
                "overall_risk_score": {
                    "score": 0.0,
                    "severity": "normal",
                    "aggregation_method": "default"
                },
                "metadata": {
                    "scored_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "scoring_engine": "rules-engine-fallback",
                    "scoring_engine_version": "1.0.0",
                    "processing_time_ms": 0
                }
            }
        
        # Always produce telemetry.scored event
        scored_event = create_scored_event(enriched_event, anomaly_result)
        
        if producer is None:
            logger.error("Producer is not initialized, cannot produce message")
            return
        
        await producer.send(
            settings.kafka_topic_scored,
            key=scored_event['device_id'].encode('utf-8'),
            value=json.dumps(scored_event).encode('utf-8')
        )
        logger.info(
            "Produced scored event",
            extra={
                "event_id": scored_event['event_id'],
                "trace_id": scored_event.get('trace_id')
            }
        )
        
        # Produce alerts.raised only when severity != OK
        if overall_severity != "OK":
            anomaly_score = anomaly_result.get('overall_risk_score', {}).get('score', 0.0)
            alert_event = create_alert_event(
                enriched_event,
                scored_event,
                overall_severity,
                rules_triggered,
                anomaly_score
            )
            
            await producer.send(
                settings.kafka_topic_alerts,
                key=alert_event['patient_id'].encode('utf-8'),
                value=json.dumps(alert_event).encode('utf-8')
            )
            logger.warning(
                f"Produced alert event, severity={overall_severity}",
                extra={
                    "event_id": alert_event['event_id'],
                    "trace_id": alert_event.get('trace_id'),
                    "severity": overall_severity
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
            settings.kafka_topic_enriched,
            bootstrap_servers=settings.kafka_brokers,
            group_id=settings.kafka_consumer_group,
            client_id=settings.kafka_client_id,
            value_deserializer=lambda m: m,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )
        
        await consumer.start()
        logger.info(f"Started consuming from topic: {settings.kafka_topic_enriched}", extra={})
        
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
        
        # Close gRPC client
        anomaly_client.close()
        
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
    title="Rules Engine Service",
    description="Evaluates rules on telemetry and generates alerts",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Rules Engine Service",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    kafka_status = "unknown"
    grpc_status = "unknown"
    
    try:
        if producer is None:
            kafka_status = "disconnected"
        else:
            kafka_status = "connected"
    except Exception as e:
        logger.warning(f"Error checking Kafka status: {e}")
        kafka_status = "unknown"
    
    try:
        # Try to check gRPC connection
        anomaly_client._ensure_connection()
        grpc_status = "connected"
    except Exception as e:
        logger.warning(f"Error checking gRPC status: {e}")
        grpc_status = "disconnected"
    
    overall_status = "healthy" if (kafka_status == "connected" and grpc_status == "connected") else "degraded"
    
    return JSONResponse(
        content={
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "service": settings.service_name,
            "kafka": kafka_status,
            "grpc": grpc_status
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)

