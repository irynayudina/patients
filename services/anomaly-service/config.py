"""
Configuration for Anomaly Detection Service
"""
import os
from typing import Optional


class Config:
    """Service configuration"""
    
    # Service ports
    PORT: int = int(os.getenv("PORT", "8003"))
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50053"))
    
    # Redis configuration
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", "redis")
    
    # Baseline configuration
    BASELINE_WINDOW_SIZE: int = int(os.getenv("BASELINE_WINDOW_SIZE", "100"))
    MIN_BASELINE_SAMPLES: int = int(os.getenv("MIN_BASELINE_SAMPLES", "10"))

