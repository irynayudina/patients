"""
gRPC client for AnomalyService
"""
import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import grpc

# Add generated directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generated'))

from generated import anomaly_pb2, anomaly_pb2_grpc
from config import settings

logger = logging.getLogger(__name__)


class AnomalyClient:
    """gRPC client for calling AnomalyService"""
    
    def __init__(self):
        self.grpc_url = settings.anomaly_service_grpc_url
        self.timeout = settings.anomaly_service_timeout
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[anomaly_pb2_grpc.AnomalyDetectionStub] = None
    
    def _ensure_connection(self):
        """Ensure gRPC channel and stub are initialized"""
        if self._channel is None or self._stub is None:
            try:
                self._channel = grpc.insecure_channel(self.grpc_url)
                self._stub = anomaly_pb2_grpc.AnomalyDetectionStub(self._channel)
                logger.info(f"Connected to AnomalyService at {self.grpc_url}")
            except Exception as e:
                logger.error(f"Failed to connect to AnomalyService: {e}")
                raise
    
    def score_vitals(self, patient_id: str, device_id: str, timestamp: str, 
                    vitals: Dict[str, Any], patient_context: Optional[Dict[str, Any]] = None,
                    historical_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call AnomalyService to score vital signs.
        
        Returns:
            Dictionary with anomaly scores and overall risk score
        """
        self._ensure_connection()
        
        try:
            # Build request
            request = anomaly_pb2.ScoreVitalsRequest(
                version="1.0.0",
                patient_id=patient_id,
                device_id=device_id,
                timestamp=timestamp
            )
            
            # Set vital signs
            if "heart_rate" in vitals and vitals["heart_rate"]:
                hr = vitals["heart_rate"]
                request.vitals.heart_rate.value = float(hr.get("value", 0))
                request.vitals.heart_rate.unit = hr.get("unit", "bpm")
                request.vitals.heart_rate.timestamp = hr.get("timestamp", timestamp)
            
            if "oxygen_saturation" in vitals and vitals["oxygen_saturation"]:
                spo2 = vitals["oxygen_saturation"]
                request.vitals.oxygen_saturation.value = float(spo2.get("value", 0))
                request.vitals.oxygen_saturation.unit = spo2.get("unit", "percent")
                request.vitals.oxygen_saturation.timestamp = spo2.get("timestamp", timestamp)
            
            if "temperature" in vitals and vitals["temperature"]:
                temp = vitals["temperature"]
                request.vitals.temperature.value = float(temp.get("value", 0))
                request.vitals.temperature.unit = temp.get("unit", "fahrenheit")
                request.vitals.temperature.timestamp = temp.get("timestamp", timestamp)
            
            if "blood_pressure" in vitals and vitals["blood_pressure"]:
                bp = vitals["blood_pressure"]
                request.vitals.blood_pressure.systolic = float(bp.get("systolic", 0))
                request.vitals.blood_pressure.diastolic = float(bp.get("diastolic", 0))
                request.vitals.blood_pressure.unit = bp.get("unit", "mmHg")
                request.vitals.blood_pressure.timestamp = bp.get("timestamp", timestamp)
            
            if "respiratory_rate" in vitals and vitals["respiratory_rate"]:
                rr = vitals["respiratory_rate"]
                request.vitals.respiratory_rate.value = float(rr.get("value", 0))
                request.vitals.respiratory_rate.unit = rr.get("unit", "breaths_per_minute")
                request.vitals.respiratory_rate.timestamp = rr.get("timestamp", timestamp)
            
            # Set patient context if provided
            if patient_context:
                if "age" in patient_context:
                    request.patient_context.age = int(patient_context["age"])
                if "gender" in patient_context:
                    gender_map = {
                        "male": anomaly_pb2.GENDER_MALE,
                        "female": anomaly_pb2.GENDER_FEMALE,
                        "other": anomaly_pb2.GENDER_OTHER
                    }
                    request.patient_context.gender = gender_map.get(
                        patient_context["gender"].lower(),
                        anomaly_pb2.GENDER_UNSPECIFIED
                    )
                if "medical_conditions" in patient_context:
                    request.patient_context.medical_conditions.extend(
                        patient_context["medical_conditions"]
                    )
                if "medications" in patient_context:
                    request.patient_context.medications.extend(
                        patient_context["medications"]
                    )
            
            # Call gRPC service
            logger.info(f"Calling AnomalyService for patient {patient_id}")
            response = self._stub.ScoreVitals(request, timeout=self.timeout)
            
            if response.status != anomaly_pb2.STATUS_SUCCESS:
                logger.error(f"AnomalyService returned error: {response.message}")
                raise Exception(f"AnomalyService error: {response.message}")
            
            # Convert response to dictionary
            result = {
                "anomaly_scores": {},
                "overall_risk_score": {
                    "score": response.overall_risk_score.score,
                    "severity": self._severity_to_string(response.overall_risk_score.severity),
                    "aggregation_method": response.overall_risk_score.aggregation_method
                },
                "metadata": {
                    "scored_at": response.metadata.scored_at,
                    "scoring_engine": response.metadata.scoring_engine,
                    "scoring_engine_version": response.metadata.scoring_engine_version,
                    "processing_time_ms": response.metadata.processing_time_ms
                }
            }
            
            # Extract individual anomaly scores
            scores = response.anomaly_scores
            if scores.heart_rate:
                result["anomaly_scores"]["heart_rate"] = {
                    "score": scores.heart_rate.score,
                    "severity": self._severity_to_string(scores.heart_rate.severity),
                    "model_version": scores.heart_rate.model_version,
                    "factors": list(scores.heart_rate.factors)
                }
            
            if scores.oxygen_saturation:
                result["anomaly_scores"]["oxygen_saturation"] = {
                    "score": scores.oxygen_saturation.score,
                    "severity": self._severity_to_string(scores.oxygen_saturation.severity),
                    "model_version": scores.oxygen_saturation.model_version,
                    "factors": list(scores.oxygen_saturation.factors)
                }
            
            if scores.temperature:
                result["anomaly_scores"]["temperature"] = {
                    "score": scores.temperature.score,
                    "severity": self._severity_to_string(scores.temperature.severity),
                    "model_version": scores.temperature.model_version,
                    "factors": list(scores.temperature.factors)
                }
            
            if scores.blood_pressure:
                result["anomaly_scores"]["blood_pressure"] = {
                    "score": scores.blood_pressure.score,
                    "severity": self._severity_to_string(scores.blood_pressure.severity),
                    "model_version": scores.blood_pressure.model_version,
                    "factors": list(scores.blood_pressure.factors)
                }
            
            if scores.respiratory_rate:
                result["anomaly_scores"]["respiratory_rate"] = {
                    "score": scores.respiratory_rate.score,
                    "severity": self._severity_to_string(scores.respiratory_rate.severity),
                    "model_version": scores.respiratory_rate.model_version,
                    "factors": list(scores.respiratory_rate.factors)
                }
            
            logger.info(f"AnomalyService returned score: {result['overall_risk_score']['score']}")
            return result
            
        except grpc.RpcError as e:
            logger.error(f"gRPC error calling AnomalyService: {e.code()} - {e.details()}")
            raise
        except Exception as e:
            logger.error(f"Error calling AnomalyService: {e}", exc_info=True)
            raise
    
    def _severity_to_string(self, severity: int) -> str:
        """Convert severity enum to string"""
        severity_map = {
            anomaly_pb2.SEVERITY_UNSPECIFIED: "normal",
            anomaly_pb2.SEVERITY_NORMAL: "normal",
            anomaly_pb2.SEVERITY_LOW: "low",
            anomaly_pb2.SEVERITY_MEDIUM: "medium",
            anomaly_pb2.SEVERITY_HIGH: "high",
            anomaly_pb2.SEVERITY_CRITICAL: "critical"
        }
        return severity_map.get(severity, "normal")
    
    def close(self):
        """Close gRPC channel"""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("Closed AnomalyService connection")

