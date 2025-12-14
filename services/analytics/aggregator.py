"""Aggregation logic for analytics"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from redis_client import RedisClient
from config import settings

logger = logging.getLogger(__name__)


class Aggregator:
    """Handles aggregation of telemetry and alert data"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
    
    async def process_telemetry_scored(self, event: Dict[str, Any]):
        """Process a telemetry.scored event and update aggregates"""
        try:
            patient_id = event.get("patient_id")
            if not patient_id:
                logger.warning("Missing patient_id in telemetry.scored event")
                return
            
            vitals = event.get("vitals", {})
            timestamp_str = event.get("timestamp")
            
            if not timestamp_str:
                logger.warning(f"Missing timestamp in event for patient {patient_id}")
                return
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.error(f"Failed to parse timestamp {timestamp_str}: {e}")
                return
            
            # Update last vitals
            await self.redis.update_last_vitals(patient_id, vitals)
            
            # Extract and update rolling averages for hr, spo2, temp
            if "heart_rate" in vitals and vitals["heart_rate"].get("value") is not None:
                hr_value = vitals["heart_rate"]["value"]
                await self.redis.add_vital_to_rolling_window(
                    patient_id, "heart_rate", hr_value, timestamp, 
                    settings.rolling_window_15m_seconds
                )
                await self.redis.add_vital_to_rolling_window(
                    patient_id, "heart_rate", hr_value, timestamp, 
                    settings.rolling_window_1h_seconds
                )
            
            if "oxygen_saturation" in vitals and vitals["oxygen_saturation"].get("value") is not None:
                spo2_value = vitals["oxygen_saturation"]["value"]
                await self.redis.add_vital_to_rolling_window(
                    patient_id, "oxygen_saturation", spo2_value, timestamp, 
                    settings.rolling_window_15m_seconds
                )
                await self.redis.add_vital_to_rolling_window(
                    patient_id, "oxygen_saturation", spo2_value, timestamp, 
                    settings.rolling_window_1h_seconds
                )
            
            if "temperature" in vitals and vitals["temperature"].get("value") is not None:
                temp_value = vitals["temperature"]["value"]
                await self.redis.add_vital_to_rolling_window(
                    patient_id, "temperature", temp_value, timestamp, 
                    settings.rolling_window_15m_seconds
                )
                await self.redis.add_vital_to_rolling_window(
                    patient_id, "temperature", temp_value, timestamp, 
                    settings.rolling_window_1h_seconds
                )
            
            logger.debug(f"Processed telemetry.scored for patient {patient_id}")
            
        except Exception as e:
            logger.error(f"Error processing telemetry.scored event: {e}", exc_info=True)
    
    async def process_alert_raised(self, event: Dict[str, Any]):
        """Process an alerts.raised event and update aggregates"""
        try:
            severity = event.get("severity")
            if not severity:
                logger.warning("Missing severity in alerts.raised event")
                return
            
            timestamp_str = event.get("timestamp")
            if not timestamp_str:
                logger.warning("Missing timestamp in alerts.raised event")
                return
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.error(f"Failed to parse timestamp {timestamp_str}: {e}")
                return
            
            # Increment alert count for this severity
            await self.redis.increment_alert_count(severity, timestamp)
            
            logger.debug(f"Processed alert.raised with severity {severity}")
            
        except Exception as e:
            logger.error(f"Error processing alerts.raised event: {e}", exc_info=True)
    
    async def get_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get summary statistics for a patient"""
        try:
            # Get last vitals
            last_vitals = await self.redis.get_last_vitals(patient_id)
            
            # Get rolling averages for 15m and 1h windows
            hr_15m = await self.redis.get_rolling_stats(patient_id, "heart_rate", settings.rolling_window_15m_seconds)
            hr_1h = await self.redis.get_rolling_stats(patient_id, "heart_rate", settings.rolling_window_1h_seconds)
            
            spo2_15m = await self.redis.get_rolling_stats(patient_id, "oxygen_saturation", settings.rolling_window_15m_seconds)
            spo2_1h = await self.redis.get_rolling_stats(patient_id, "oxygen_saturation", settings.rolling_window_1h_seconds)
            
            temp_15m = await self.redis.get_rolling_stats(patient_id, "temperature", settings.rolling_window_15m_seconds)
            temp_1h = await self.redis.get_rolling_stats(patient_id, "temperature", settings.rolling_window_1h_seconds)
            
            return {
                "patient_id": patient_id,
                "last_vitals": last_vitals,
                "rolling_averages": {
                    "heart_rate": {
                        "15m": {
                            "average": hr_15m.get("average"),
                            "count": hr_15m.get("count"),
                            "min": hr_15m.get("min"),
                            "max": hr_15m.get("max")
                        },
                        "1h": {
                            "average": hr_1h.get("average"),
                            "count": hr_1h.get("count"),
                            "min": hr_1h.get("min"),
                            "max": hr_1h.get("max")
                        }
                    },
                    "oxygen_saturation": {
                        "15m": {
                            "average": spo2_15m.get("average"),
                            "count": spo2_15m.get("count"),
                            "min": spo2_15m.get("min"),
                            "max": spo2_15m.get("max")
                        },
                        "1h": {
                            "average": spo2_1h.get("average"),
                            "count": spo2_1h.get("count"),
                            "min": spo2_1h.get("min"),
                            "max": spo2_1h.get("max")
                        }
                    },
                    "temperature": {
                        "15m": {
                            "average": temp_15m.get("average"),
                            "count": temp_15m.get("count"),
                            "min": temp_15m.get("min"),
                            "max": temp_15m.get("max")
                        },
                        "1h": {
                            "average": temp_1h.get("average"),
                            "count": temp_1h.get("count"),
                            "min": temp_1h.get("min"),
                            "max": temp_1h.get("max")
                        }
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error getting patient summary for {patient_id}: {e}", exc_info=True)
            raise

