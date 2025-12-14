"""Configuration for analytics service"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    service_name: str = "analytics"
    port: int = int(os.getenv("PORT", "8005"))
    
    # Kafka configuration
    kafka_brokers: str = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_client_id: str = os.getenv("KAFKA_CLIENT_ID", "analytics")
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "analytics-group")
    kafka_topic_scored: str = os.getenv("KAFKA_TOPIC_SCORED", "telemetry.scored")
    kafka_topic_alerts: str = os.getenv("KAFKA_TOPIC_ALERTS", "alerts.raised")
    
    # Redis configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "redis")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Aggregation settings
    rolling_window_15m_seconds: int = 15 * 60  # 15 minutes
    rolling_window_1h_seconds: int = 60 * 60   # 1 hour
    alert_window_seconds: int = 60             # 1 minute for alert counting
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

