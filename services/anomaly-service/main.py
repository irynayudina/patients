"""
Anomaly Detection Service - Med Telemetry Platform
FastAPI service hosting a gRPC server for vital signs anomaly detection
"""
import asyncio
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

import grpc
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add generated directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generated'))

from generated import anomaly_pb2, anomaly_pb2_grpc
from scoring_service import ScoringService
from config import Config

# FastAPI app for health checks
app = FastAPI(
    title="Anomaly Detection Service",
    description="gRPC service for vital signs anomaly detection",
    version="1.0.0",
)

# Global gRPC server instance
grpc_server: Optional[grpc.Server] = None


@app.get("/health")
async def health():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "anomaly-service",
            "grpc_port": Config.GRPC_PORT
        }
    )


class AnomalyDetectionServicer(anomaly_pb2_grpc.AnomalyDetectionServicer):
    """gRPC servicer for anomaly detection"""
    
    def __init__(self, scoring_service: ScoringService):
        self.scoring_service = scoring_service
    
    def ScoreVitals(self, request, context):
        """Score vital signs for anomalies"""
        try:
            # Extract vital signs from request
            vitals = request.vitals
            
            # Get heart rate, SpO2, and temperature
            hr = vitals.heart_rate.value if vitals.heart_rate else None
            spo2 = vitals.oxygen_saturation.value if vitals.oxygen_saturation else None
            temp = vitals.temperature.value if vitals.temperature else None
            
            # Validate required fields
            if hr is None or spo2 is None or temp is None:
                return anomaly_pb2.ScoreVitalsResponse(
                    version="1.0.0",
                    status=anomaly_pb2.STATUS_INVALID_REQUEST,
                    patient_id=request.patient_id,
                    timestamp=datetime.utcnow().isoformat(),
                    message="Missing required vital signs: hr, spo2, or temp"
                )
            
            # Score the vitals
            result = self.scoring_service.score_vitals(
                patient_id=request.patient_id,
                hr=hr,
                spo2=spo2,
                temp=temp
            )
            
            # Build response
            response = anomaly_pb2.ScoreVitalsResponse(
                version="1.0.0",
                status=anomaly_pb2.STATUS_SUCCESS,
                patient_id=request.patient_id,
                timestamp=datetime.utcnow().isoformat(),
                message=result.get("explanation", "")
            )
            
            # Set overall risk score
            response.overall_risk_score.score = result["score"]
            response.overall_risk_score.severity = self._score_to_severity(result["score"])
            response.overall_risk_score.aggregation_method = "z_score_based"
            
            # Set individual vital scores from the result
            vitals_results = result.get("vitals", {})
            
            if "hr" in vitals_results:
                hr_result = vitals_results["hr"]
                response.anomaly_scores.heart_rate.score = hr_result["score"]
                response.anomaly_scores.heart_rate.severity = self._score_to_severity(hr_result["score"])
                response.anomaly_scores.heart_rate.explanation = hr_result.get("explanation", "")
            
            if "spo2" in vitals_results:
                spo2_result = vitals_results["spo2"]
                response.anomaly_scores.oxygen_saturation.score = spo2_result["score"]
                response.anomaly_scores.oxygen_saturation.severity = self._score_to_severity(spo2_result["score"])
                response.anomaly_scores.oxygen_saturation.explanation = spo2_result.get("explanation", "")
            
            if "temp" in vitals_results:
                temp_result = vitals_results["temp"]
                response.anomaly_scores.temperature.score = temp_result["score"]
                response.anomaly_scores.temperature.severity = self._score_to_severity(temp_result["score"])
                response.anomaly_scores.temperature.explanation = temp_result.get("explanation", "")
            
            # Set metadata
            response.metadata.scored_at = datetime.utcnow().isoformat()
            response.metadata.scoring_engine = "z_score_baseline"
            response.metadata.scoring_engine_version = "1.0.0"
            
            return response
            
        except Exception as e:
            return anomaly_pb2.ScoreVitalsResponse(
                version="1.0.0",
                status=anomaly_pb2.STATUS_INTERNAL_ERROR,
                patient_id=request.patient_id if hasattr(request, 'patient_id') else "",
                timestamp=datetime.utcnow().isoformat(),
                message=f"Internal error: {str(e)}"
            )
    
    def _score_to_severity(self, score: float) -> int:
        """Convert score (0-1) to severity enum"""
        if score < 0.2:
            return anomaly_pb2.SEVERITY_NORMAL
        elif score < 0.4:
            return anomaly_pb2.SEVERITY_LOW
        elif score < 0.6:
            return anomaly_pb2.SEVERITY_MEDIUM
        elif score < 0.8:
            return anomaly_pb2.SEVERITY_HIGH
        else:
            return anomaly_pb2.SEVERITY_CRITICAL


def serve_grpc():
    """Start the gRPC server in a separate thread"""
    global grpc_server
    
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    scoring_service = ScoringService()
    anomaly_pb2_grpc.add_AnomalyDetectionServicer_to_server(
        AnomalyDetectionServicer(scoring_service),
        server
    )
    
    grpc_port = f'[::]:{Config.GRPC_PORT}'
    server.add_insecure_port(grpc_port)
    server.start()
    grpc_server = server
    
    print(f"gRPC server started on port {Config.GRPC_PORT}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=5)


@app.on_event("startup")
async def startup_event():
    """Start gRPC server on startup in a separate thread"""
    grpc_thread = threading.Thread(target=serve_grpc, daemon=True)
    grpc_thread.start()
    print("gRPC server thread started")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop gRPC server on shutdown"""
    global grpc_server
    if grpc_server:
        grpc_server.stop(grace=5)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

