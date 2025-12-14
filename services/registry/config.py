"""Configuration module"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    port: int = 8000
    grpc_port: int = 50051
    
    # Database configuration
    database_url: str = "postgresql://postgres:postgres@postgres:5432/patient_monitoring"
    
    # gRPC configuration
    grpc_host: str = "0.0.0.0"
    
    # Logging
    log_level: str = "info"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

