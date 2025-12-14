"""Configuration module"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    port: int = 8000
    grpc_port: int = 50052
    
    # Kafka configuration
    kafka_brokers: str = "localhost:29092"
    
    # gRPC configuration
    grpc_host: str = "0.0.0.0"
    
    # Logging
    log_level: str = "info"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def kafka_broker_list(self) -> List[str]:
        """Convert Kafka brokers string to list"""
        return self.kafka_brokers.split(",")


settings = Settings()

