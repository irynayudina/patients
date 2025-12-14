"""Configuration for rules-engine service"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    service_name: str = "rules-engine"
    port: int = int(os.getenv("PORT", "8004"))
    
    # Kafka configuration
    kafka_brokers: str = os.getenv("KAFKA_BROKERS", "localhost:9092")
    kafka_client_id: str = os.getenv("KAFKA_CLIENT_ID", "rules-engine")
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP", "rules-engine-group")
    kafka_topic_enriched: str = os.getenv("KAFKA_TOPIC_ENRICHED", "telemetry.enriched")
    kafka_topic_scored: str = os.getenv("KAFKA_TOPIC_SCORED", "telemetry.scored")
    kafka_topic_alerts: str = os.getenv("KAFKA_TOPIC_ALERTS", "alerts.raised")
    
    # gRPC configuration
    anomaly_service_grpc_url: str = os.getenv("ANOMALY_SERVICE_GRPC_URL", "anomaly-service:50053")
    anomaly_service_timeout: int = int(os.getenv("ANOMALY_SERVICE_TIMEOUT", "5"))
    
    # Rule thresholds
    hr_max: float = float(os.getenv("HR_MAX", "100.0"))
    spo2_min: float = float(os.getenv("SPO2_MIN", "95.0"))
    temp_max: float = float(os.getenv("TEMP_MAX", "100.4"))  # Fahrenheit
    hr_very_high: float = float(os.getenv("HR_VERY_HIGH", "120.0"))
    spo2_low: float = float(os.getenv("SPO2_LOW", "90.0"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

