"""
Scoring Service - Z-score based anomaly detection with rolling baselines
"""
import json
import math
import statistics
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import redis
from config import Config


class BaselineStore:
    """Store for patient baselines (in-memory or Redis)"""
    
    def __init__(self):
        self.use_redis = Config.REDIS_ENABLED
        if self.use_redis:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
        else:
            # In-memory storage: {patient_id: {vital_type: deque of values}}
            self.baselines: Dict[str, Dict[str, deque]] = {}
    
    def add_measurement(self, patient_id: str, vital_type: str, value: float):
        """Add a measurement to the baseline"""
        if self.use_redis:
            key = f"baseline:{patient_id}:{vital_type}"
            # Use Redis list to store recent values
            self.redis_client.lpush(key, json.dumps({"value": value, "timestamp": datetime.utcnow().isoformat()}))
            # Keep only last N measurements
            self.redis_client.ltrim(key, 0, Config.BASELINE_WINDOW_SIZE - 1)
            # Set expiration (e.g., 7 days)
            self.redis_client.expire(key, 7 * 24 * 60 * 60)
        else:
            if patient_id not in self.baselines:
                self.baselines[patient_id] = {}
            if vital_type not in self.baselines[patient_id]:
                self.baselines[patient_id][vital_type] = deque(maxlen=Config.BASELINE_WINDOW_SIZE)
            self.baselines[patient_id][vital_type].append(value)
    
    def get_baseline_stats(self, patient_id: str, vital_type: str) -> Optional[Tuple[float, float]]:
        """Get mean and std dev for a patient's vital type. Returns (mean, std_dev) or None if insufficient data."""
        if self.use_redis:
            key = f"baseline:{patient_id}:{vital_type}"
            values_json = self.redis_client.lrange(key, 0, Config.BASELINE_WINDOW_SIZE - 1)
            if not values_json:
                return None
            values = [json.loads(v)["value"] for v in values_json]
        else:
            if patient_id not in self.baselines or vital_type not in self.baselines[patient_id]:
                return None
            values = list(self.baselines[patient_id][vital_type])
        
        if len(values) < Config.MIN_BASELINE_SAMPLES:
            return None
        
        mean = statistics.mean(values)
        if len(values) < 2:
            std_dev = 0.0
        else:
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # Avoid division by zero
        if std_dev == 0:
            std_dev = 0.1  # Small default std dev
        
        return (mean, std_dev)
    
    def get_sample_count(self, patient_id: str, vital_type: str) -> int:
        """Get number of samples for a patient's vital type"""
        if self.use_redis:
            key = f"baseline:{patient_id}:{vital_type}"
            return self.redis_client.llen(key)
        else:
            if patient_id not in self.baselines or vital_type not in self.baselines[patient_id]:
                return 0
            return len(self.baselines[patient_id][vital_type])


class ScoringService:
    """Service for scoring vital signs using z-score based anomaly detection"""
    
    # Normal ranges for vitals (fallback when no baseline)
    NORMAL_RANGES = {
        "hr": (60, 100),      # Heart rate: 60-100 bpm
        "spo2": (95, 100),    # SpO2: 95-100%
        "temp": (36.1, 37.2), # Temperature: 36.1-37.2°C (97-99°F)
    }
    
    # Z-score thresholds
    Z_SCORE_NORMAL = 1.0      # Within 1 std dev = normal
    Z_SCORE_LOW = 2.0         # Within 2 std dev = low severity
    Z_SCORE_MEDIUM = 3.0      # Within 3 std dev = medium severity
    Z_SCORE_HIGH = 4.0        # > 3 std dev = high severity
    
    def __init__(self):
        self.baseline_store = BaselineStore()
    
    def score_single_vital(
        self,
        patient_id: str,
        vital_type: str,
        value: float
    ) -> Dict[str, any]:
        """Score a single vital sign measurement"""
        # Get baseline stats
        baseline = self.baseline_store.get_baseline_stats(patient_id, vital_type)
        sample_count = self.baseline_store.get_sample_count(patient_id, vital_type)
        
        # If insufficient history, return low score with explanation
        if baseline is None:
            # Add this measurement to baseline
            self.baseline_store.add_measurement(patient_id, vital_type, value)
            
            # Check against normal ranges as fallback
            if vital_type in self.NORMAL_RANGES:
                min_val, max_val = self.NORMAL_RANGES[vital_type]
                if value < min_val or value > max_val:
                    score = 0.5  # Moderate score for out-of-range but no baseline
                    explanation = f"{vital_type.upper()} value {value:.2f} is outside normal range ({min_val}-{max_val}), but insufficient baseline data ({sample_count} samples)"
                else:
                    score = 0.2  # Low score for normal range but no baseline
                    explanation = f"{vital_type.upper()} value {value:.2f} is within normal range, but insufficient baseline data ({sample_count} samples)"
            else:
                score = 0.3
                explanation = f"Insufficient baseline data for {vital_type.upper()} ({sample_count} samples)"
            
            return {
                "score": score,
                "is_anomaly": score > 0.5,
                "explanation": explanation
            }
        
        mean, std_dev = baseline
        
        # Calculate z-score
        z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
        
        # Convert z-score to anomaly score (0-1)
        # Use sigmoid-like function to map z-score to 0-1 range
        if z_score <= self.Z_SCORE_NORMAL:
            score = 0.0 + (z_score / self.Z_SCORE_NORMAL) * 0.2  # 0.0 to 0.2
        elif z_score <= self.Z_SCORE_LOW:
            score = 0.2 + ((z_score - self.Z_SCORE_NORMAL) / (self.Z_SCORE_LOW - self.Z_SCORE_NORMAL)) * 0.2  # 0.2 to 0.4
        elif z_score <= self.Z_SCORE_MEDIUM:
            score = 0.4 + ((z_score - self.Z_SCORE_LOW) / (self.Z_SCORE_MEDIUM - self.Z_SCORE_LOW)) * 0.2  # 0.4 to 0.6
        elif z_score <= self.Z_SCORE_HIGH:
            score = 0.6 + ((z_score - self.Z_SCORE_MEDIUM) / (self.Z_SCORE_HIGH - self.Z_SCORE_MEDIUM)) * 0.2  # 0.6 to 0.8
        else:
            score = 0.8 + min((z_score - self.Z_SCORE_HIGH) / self.Z_SCORE_HIGH * 0.2, 0.2)  # 0.8 to 1.0
        
        score = min(1.0, max(0.0, score))
        
        # Determine if anomaly (score > 0.5)
        is_anomaly = score > 0.5
        
        # Build explanation
        direction = "above" if value > mean else "below"
        explanation = (
            f"{vital_type.upper()} value {value:.2f} is {direction} baseline "
            f"(mean={mean:.2f}, std={std_dev:.2f}, z-score={z_score:.2f}). "
            f"Anomaly score: {score:.2f}"
        )
        
        # Add this measurement to baseline for future calculations
        self.baseline_store.add_measurement(patient_id, vital_type, value)
        
        return {
            "score": score,
            "is_anomaly": is_anomaly,
            "explanation": explanation
        }
    
    def score_vitals(
        self,
        patient_id: str,
        hr: float,
        spo2: float,
        temp: float
    ) -> Dict[str, any]:
        """Score multiple vital signs and return overall score"""
        # Score each vital
        hr_result = self.score_single_vital(patient_id, "hr", hr)
        spo2_result = self.score_single_vital(patient_id, "spo2", spo2)
        temp_result = self.score_single_vital(patient_id, "temp", temp)
        
        # Calculate overall score (weighted average, with SpO2 and HR weighted more)
        overall_score = (
            hr_result["score"] * 0.35 +
            spo2_result["score"] * 0.35 +
            temp_result["score"] * 0.30
        )
        
        # Determine if any is an anomaly
        is_anomaly = hr_result["is_anomaly"] or spo2_result["is_anomaly"] or temp_result["is_anomaly"]
        
        # Build explanation
        explanations = [
            hr_result["explanation"],
            spo2_result["explanation"],
            temp_result["explanation"]
        ]
        explanation = " | ".join(explanations)
        
        return {
            "score": overall_score,
            "is_anomaly": is_anomaly,
            "explanation": explanation,
            "vitals": {
                "hr": hr_result,
                "spo2": spo2_result,
                "temp": temp_result
            }
        }

