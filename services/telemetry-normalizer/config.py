"""Configuration for telemetry-normalizer service"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    service_name: str = "telemetry-normalizer"
    port: int = int(os.getenv("PORT", "8001"))
    
    # Kafka configuration
    kafka_brokers: str = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_client_id: str = os.getenv("KAFKA_CLIENT_ID", "telemetry-normalizer")
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "telemetry-normalizer-group")
    kafka_topic_raw: str = os.getenv("KAFKA_TOPIC_RAW", "telemetry.raw")
    kafka_topic_normalized: str = os.getenv("KAFKA_TOPIC_NORMALIZED", "telemetry.normalized")
    
    # Normalization rules
    hr_min: float = 20.0
    hr_max: float = 240.0
    spo2_min: float = 50.0
    spo2_max: float = 100.0
    temp_min: float = 30.0
    temp_max: float = 45.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

