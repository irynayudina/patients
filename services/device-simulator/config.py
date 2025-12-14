"""Configuration module for device simulator"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Registry configuration
    registry_url: str = "http://registry:8000"
    
    # Telemetry Gateway configuration
    gateway_grpc_url: str = "telemetry-gateway:50052"
    gateway_rest_url: str = "http://telemetry-gateway:3000"
    
    # Simulator defaults
    default_devices: int = 5
    default_interval: int = 5  # seconds
    default_episode_rate: float = 0.05  # 5% chance per interval
    
    # Logging
    log_level: str = "info"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

