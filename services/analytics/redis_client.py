"""Redis client for analytics aggregates"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for managing analytics aggregates"""
    
    def __init__(self, host: str, port: int, password: str, db: int = 0):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = aioredis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            await self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")
    
    async def ping(self) -> bool:
        """Check Redis connection"""
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except Exception:
            return False
    
    # Patient aggregates
    
    async def update_last_vitals(self, patient_id: str, vitals: Dict[str, Any]):
        """Update last vitals for a patient"""
        key = f"patient:{patient_id}:last_vitals"
        vitals_data = {
            **vitals,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await self.client.set(key, json.dumps(vitals_data))
    
    async def get_last_vitals(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get last vitals for a patient"""
        key = f"patient:{patient_id}:last_vitals"
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def add_vital_to_rolling_window(
        self, 
        patient_id: str, 
        vital_type: str, 
        value: float, 
        timestamp: datetime,
        window_seconds: int
    ):
        """Add a vital sign value to a rolling time window using sorted set"""
        # Use sorted set with timestamp as score
        key = f"patient:{patient_id}:{vital_type}:{window_seconds}s"
        score = timestamp.timestamp()
        
        # Add value with timestamp as score
        await self.client.zadd(key, {str(value): score})
        
        # Remove old entries outside the window
        cutoff = (timestamp - timedelta(seconds=window_seconds)).timestamp()
        await self.client.zremrangebyscore(key, "-inf", cutoff)
        
        # Set expiration to window size + buffer
        await self.client.expire(key, window_seconds + 60)
    
    async def get_rolling_average(
        self, 
        patient_id: str, 
        vital_type: str, 
        window_seconds: int
    ) -> Optional[float]:
        """Get rolling average for a vital sign within a time window"""
        key = f"patient:{patient_id}:{vital_type}:{window_seconds}s"
        
        # Get all values in the window
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds
        
        values = await self.client.zrangebyscore(key, cutoff, now)
        
        if not values:
            return None
        
        # Calculate average
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue
        if numeric_values:
            return sum(numeric_values) / len(numeric_values)
        return None
    
    async def get_rolling_stats(
        self, 
        patient_id: str, 
        vital_type: str, 
        window_seconds: int
    ) -> Dict[str, Any]:
        """Get rolling statistics (count, avg, min, max) for a vital sign"""
        key = f"patient:{patient_id}:{vital_type}:{window_seconds}s"
        
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds
        
        values = await self.client.zrangebyscore(key, cutoff, now)
        
        if not values:
            return {
                "count": 0,
                "average": None,
                "min": None,
                "max": None
            }
        
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                continue
        
        if not numeric_values:
            return {
                "count": 0,
                "average": None,
                "min": None,
                "max": None
            }
        
        return {
            "count": len(numeric_values),
            "average": sum(numeric_values) / len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values)
        }
    
    # Global alert aggregates
    
    async def increment_alert_count(self, severity: str, timestamp: datetime):
        """Increment alert count for a severity level at a specific minute"""
        # Round to minute
        minute_key = timestamp.replace(second=0, microsecond=0)
        key = f"alerts:global:{severity}:{minute_key.isoformat()}"
        
        # Increment counter
        await self.client.incr(key)
        
        # Set expiration (keep for 2 minutes to allow for querying)
        await self.client.expire(key, 120)
    
    async def get_alerts_per_minute_by_severity(self) -> Dict[str, int]:
        """Get current alerts per minute by severity"""
        # Get current minute and previous minute
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        prev_minute = now - timedelta(minutes=1)
        
        severities = ["low", "medium", "high", "critical"]
        result = {}
        
        for severity in severities:
            # Try current minute first, then previous minute
            current_key = f"alerts:global:{severity}:{now.isoformat()}"
            prev_key = f"alerts:global:{severity}:{prev_minute.isoformat()}"
            
            current_count = await self.client.get(current_key)
            prev_count = await self.client.get(prev_key)
            
            # Use current minute if available, otherwise previous minute
            count = int(current_count) if current_count else (int(prev_count) if prev_count else 0)
            result[severity] = count
        
        return result
    
    async def get_recent_alerts_by_severity(self, minutes: int = 5) -> Dict[str, int]:
        """Get total alerts in the last N minutes by severity"""
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        severities = ["low", "medium", "high", "critical"]
        result = {}
        
        for severity in severities:
            total = 0
            for i in range(minutes):
                minute_key = now - timedelta(minutes=i)
                key = f"alerts:global:{severity}:{minute_key.isoformat()}"
                count = await self.client.get(key)
                if count:
                    total += int(count)
            result[severity] = total
        
        return result

