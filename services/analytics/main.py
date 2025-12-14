"""
Analytics Service
Consumes telemetry.scored and alerts.raised, maintains aggregates in Redis
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from config import settings
from redis_client import RedisClient
from aggregator import Aggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
redis_client: Optional[RedisClient] = None
aggregator: Optional[Aggregator] = None
consumer_scored: Optional[AIOKafkaConsumer] = None
consumer_alerts: Optional[AIOKafkaConsumer] = None


async def process_telemetry_message(message):
    """Process a telemetry.scored message"""
    try:
        event = json.loads(message.value.decode('utf-8'))
        if aggregator:
            await aggregator.process_telemetry_scored(event)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON message: {e}")
    except Exception as e:
        logger.error(f"Error processing telemetry message: {e}", exc_info=True)


async def process_alert_message(message):
    """Process an alerts.raised message"""
    try:
        event = json.loads(message.value.decode('utf-8'))
        if aggregator:
            await aggregator.process_alert_raised(event)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON message: {e}")
    except Exception as e:
        logger.error(f"Error processing alert message: {e}", exc_info=True)


async def consume_telemetry():
    """Consume messages from telemetry.scored topic"""
    global consumer_scored
    
    try:
        consumer_scored = AIOKafkaConsumer(
            settings.kafka_topic_scored,
            bootstrap_servers=settings.kafka_brokers,
            group_id=f"{settings.kafka_consumer_group}-scored",
            client_id=f"{settings.kafka_client_id}-scored",
            value_deserializer=lambda m: m,
            auto_offset_reset='latest',  # Start from latest to avoid processing old data
            enable_auto_commit=True,
        )
        
        await consumer_scored.start()
        logger.info(f"Started consuming from topic: {settings.kafka_topic_scored}")
        
        try:
            async for message in consumer_scored:
                await process_telemetry_message(message)
        finally:
            await consumer_scored.stop()
            
    except KafkaError as e:
        logger.error(f"Kafka error in telemetry consumer: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in telemetry consumer: {e}", exc_info=True)


async def consume_alerts():
    """Consume messages from alerts.raised topic"""
    global consumer_alerts
    
    try:
        consumer_alerts = AIOKafkaConsumer(
            settings.kafka_topic_alerts,
            bootstrap_servers=settings.kafka_brokers,
            group_id=f"{settings.kafka_consumer_group}-alerts",
            client_id=f"{settings.kafka_client_id}-alerts",
            value_deserializer=lambda m: m,
            auto_offset_reset='latest',
            enable_auto_commit=True,
        )
        
        await consumer_alerts.start()
        logger.info(f"Started consuming from topic: {settings.kafka_topic_alerts}")
        
        try:
            async for message in consumer_alerts:
                await process_alert_message(message)
        finally:
            await consumer_alerts.stop()
            
    except KafkaError as e:
        logger.error(f"Kafka error in alerts consumer: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error in alerts consumer: {e}", exc_info=True)


async def start_kafka_consumers():
    """Start Kafka consumers"""
    # Start both consumers in background
    asyncio.create_task(consume_telemetry())
    asyncio.create_task(consume_alerts())


async def stop_kafka_consumers():
    """Stop Kafka consumers"""
    global consumer_scored, consumer_alerts
    
    try:
        if consumer_scored:
            await consumer_scored.stop()
            logger.info("Telemetry consumer stopped")
        
        if consumer_alerts:
            await consumer_alerts.stop()
            logger.info("Alerts consumer stopped")
    except Exception as e:
        logger.error(f"Error stopping Kafka consumers: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global redis_client, aggregator
    
    # Startup
    try:
        # Initialize Redis client
        redis_client = RedisClient(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db
        )
        await redis_client.connect()
        
        # Initialize aggregator
        aggregator = Aggregator(redis_client)
        
        # Start Kafka consumers
        await start_kafka_consumers()
        
        logger.info("Analytics service started")
    except Exception as e:
        logger.error(f"Failed to start analytics service: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    await stop_kafka_consumers()
    if redis_client:
        await redis_client.disconnect()
    logger.info("Analytics service stopped")


app = FastAPI(
    title="Analytics Service",
    description="Real-time aggregates for patient telemetry and alerts",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Analytics Service",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    redis_status = "unknown"
    kafka_status = "unknown"
    
    try:
        if redis_client:
            redis_status = "connected" if await redis_client.ping() else "disconnected"
        else:
            redis_status = "disconnected"
    except Exception as e:
        logger.warning(f"Error checking Redis status: {e}")
        redis_status = "disconnected"
    
    try:
        if consumer_scored and consumer_alerts:
            kafka_status = "connected"
        else:
            kafka_status = "disconnected"
    except Exception as e:
        logger.warning(f"Error checking Kafka status: {e}")
        kafka_status = "disconnected"
    
    overall_status = "healthy" if (redis_status == "connected" and kafka_status == "connected") else "degraded"
    
    return JSONResponse(
        content={
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "service": settings.service_name,
            "redis": redis_status,
            "kafka": kafka_status
        }
    )


@app.get("/stats/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    """Get summary statistics for a patient"""
    if not aggregator:
        raise HTTPException(status_code=503, detail="Aggregator not initialized")
    
    try:
        summary = await aggregator.get_patient_summary(patient_id)
        return summary
    except Exception as e:
        logger.error(f"Error getting patient summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats/global/alerts")
async def get_global_alerts():
    """Get global alert statistics per minute by severity"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis client not initialized")
    
    try:
        alerts_per_minute = await redis_client.get_alerts_per_minute_by_severity()
        return {
            "alerts_per_minute": alerts_per_minute,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    except Exception as e:
        logger.error(f"Error getting global alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)

