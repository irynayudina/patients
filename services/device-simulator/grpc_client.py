"""gRPC client for Telemetry Gateway"""
import grpc
from typing import List, Dict
from datetime import datetime
import logging
import sys
import os

# Add generated directory to path
generated_path = os.path.join(os.path.dirname(__file__), 'generated')
if os.path.exists(generated_path):
    sys.path.insert(0, os.path.dirname(__file__))  # Add parent directory to path

try:
    from generated import telemetry_gateway_pb2
    from generated import telemetry_gateway_pb2_grpc
except ImportError:
    # Fallback if generated code doesn't exist yet
    telemetry_gateway_pb2 = None
    telemetry_gateway_pb2_grpc = None

logger = logging.getLogger(__name__)


class TelemetryGatewayClient:
    """gRPC client for sending telemetry to Telemetry Gateway"""
    
    def __init__(self, grpc_url: str):
        """
        Initialize gRPC client
        
        Args:
            grpc_url: gRPC server URL (e.g., "telemetry-gateway:50052")
        """
        if not telemetry_gateway_pb2 or not telemetry_gateway_pb2_grpc:
            raise ImportError(
                "gRPC stubs not generated. Run: "
                "python -m grpc_tools.protoc --proto_path=../../proto "
                "--python_out=generated --grpc_python_out=generated "
                "../../proto/telemetry_gateway.proto"
            )
        
        self.grpc_url = grpc_url
        self.channel = None
        self.stub = None
    
    def connect(self):
        """Establish gRPC connection"""
        try:
            self.channel = grpc.insecure_channel(self.grpc_url)
            self.stub = telemetry_gateway_pb2_grpc.TelemetryGatewayStub(self.channel)
            logger.info(f"Connected to Telemetry Gateway at {self.grpc_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Telemetry Gateway: {e}")
            raise
    
    def close(self):
        """Close gRPC connection"""
        if self.channel:
            self.channel.close()
            logger.info("Closed gRPC connection")
    
    def send_measurements(
        self,
        device_id: str,
        device_type: str,
        measurements: List[Dict[str, float]],
        device_metadata: Dict[str, str] = None
    ) -> bool:
        """
        Send measurements to Telemetry Gateway
        
        Args:
            device_id: Device identifier
            device_type: Device type
            measurements: List of measurements, each with 'metric', 'value', 'unit'
            device_metadata: Optional device metadata
        
        Returns:
            True if successful, False otherwise
        """
        if not self.stub:
            raise RuntimeError("Not connected to Telemetry Gateway")
        
        try:
            # Create request
            request = telemetry_gateway_pb2.SendMeasurementsRequest()
            request.version = "1.0.0"
            request.device_id = device_id
            request.device_type = device_type
            request.timestamp = datetime.utcnow().isoformat() + "Z"
            
            # Add measurements
            for meas in measurements:
                measurement = request.measurements.add()
                measurement.metric = meas['metric']
                measurement.value = meas['value']
                measurement.unit = meas['unit']
                if 'timestamp' in meas:
                    measurement.measurement_timestamp = meas['timestamp']
            
            # Add metadata
            if device_metadata:
                for key, value in device_metadata.items():
                    request.device_metadata[key] = str(value)
            
            # Send request
            response = self.stub.SendMeasurements(request, timeout=10)
            
            if response.status == telemetry_gateway_pb2.STATUS_SUCCESS:
                logger.debug(
                    f"Sent measurements for device {device_id}: "
                    f"event_id={response.event_id}"
                )
                return True
            else:
                logger.warning(
                    f"Failed to send measurements for device {device_id}: "
                    f"status={response.status}, message={response.message}"
                )
                return False
        
        except grpc.RpcError as e:
            logger.error(f"gRPC error sending measurements: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"Error sending measurements: {e}")
            return False

