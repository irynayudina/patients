"""Device simulator that generates and sends telemetry"""
import time
import logging
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime
import threading

from registry_client import RegistryClient
from grpc_client import TelemetryGatewayClient
from vital_generator import VitalGenerator, PatientBaseline, EpisodeType
from config import settings

logger = logging.getLogger(__name__)


class DeviceSimulator:
    """Simulates a single device sending telemetry"""
    
    def __init__(
        self,
        device: Dict,
        patient: Optional[Dict],
        threshold_profile: Optional[Dict],
        gateway_client: TelemetryGatewayClient,
        interval: float,
        episode_rate: float
    ):
        """
        Initialize device simulator
        
        Args:
            device: Device data from registry
            patient: Patient data (optional)
            threshold_profile: Threshold profile (optional)
            gateway_client: gRPC client for Telemetry Gateway
            interval: Interval between telemetry sends (seconds)
            episode_rate: Probability of episode per interval
        """
        self.device_id = str(device['id'])
        self.device_serial = device['serial']
        self.device_firmware = device.get('firmware', 'v1.0.0')
        self.patient_id = str(device.get('patient_id')) if device.get('patient_id') else None
        self.gateway_client = gateway_client
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Create baseline from threshold profile or use defaults
        if threshold_profile:
            baseline = PatientBaseline(
                hr_baseline=(threshold_profile['hr_min'] + threshold_profile['hr_max']) / 2,
                spo2_baseline=max(threshold_profile['spo2_min'] + 2, 98.0),
                temp_baseline=(threshold_profile['temp_min'] + threshold_profile['temp_max']) / 2,
                hr_min=threshold_profile['hr_min'],
                hr_max=threshold_profile['hr_max'],
                spo2_min=threshold_profile['spo2_min'],
                temp_min=threshold_profile['temp_min'],
                temp_max=threshold_profile['temp_max']
            )
        else:
            # Default baseline if no profile
            baseline = PatientBaseline(
                hr_baseline=75.0,
                spo2_baseline=98.0,
                temp_baseline=36.5,
                hr_min=60.0,
                hr_max=100.0,
                spo2_min=95.0,
                temp_min=36.0,
                temp_max=37.2
            )
        
        self.vital_generator = VitalGenerator(baseline, episode_rate)
        self.start_time = time.time()
        self.telemetry_count = 0
    
    def start(self):
        """Start the simulator in a background thread"""
        if self.running:
            logger.warning(f"Device {self.device_serial} already running")
            return
        
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(
            f"Started simulator for device {self.device_serial} "
            f"(patient: {self.patient_id or 'unassigned'})"
        )
    
    def stop(self):
        """Stop the simulator"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"Stopped simulator for device {self.device_serial}")
    
    def _run(self):
        """Main simulation loop"""
        while self.running:
            try:
                elapsed_time = time.time() - self.start_time
                
                # Generate vital signs
                hr, spo2, temp, episode_type = self.vital_generator.generate(elapsed_time)
                
                # Prepare measurements
                measurements = [
                    {
                        'metric': 'heart_rate',
                        'value': hr,
                        'unit': 'bpm'
                    },
                    {
                        'metric': 'oxygen_saturation',
                        'value': spo2,
                        'unit': '%'
                    },
                    {
                        'metric': 'temperature',
                        'value': temp,
                        'unit': 'celsius'
                    }
                ]
                
                # Device metadata
                device_metadata = {
                    'firmware': self.device_firmware,
                    'battery_level': '95'  # Simulated battery
                }
                
                # Send telemetry
                success = self.gateway_client.send_measurements(
                    device_id=self.device_id,
                    device_type='medical_device',
                    measurements=measurements,
                    device_metadata=device_metadata
                )
                
                if success:
                    self.telemetry_count += 1
                    episode_msg = f" [{episode_type.value}]" if episode_type != EpisodeType.NONE else ""
                    logger.debug(
                        f"Device {self.device_serial}: "
                        f"HR={hr:.1f} SpO2={spo2:.1f} Temp={temp:.2f}°C{episode_msg}"
                    )
                else:
                    logger.warning(f"Failed to send telemetry for device {self.device_serial}")
                
                # Wait for next interval
                time.sleep(self.interval)
            
            except Exception as e:
                logger.error(f"Error in simulator loop for device {self.device_serial}: {e}")
                time.sleep(self.interval)


class SimulatorManager:
    """Manages multiple device simulators"""
    
    def __init__(
        self,
        registry_url: str,
        gateway_grpc_url: str,
        num_devices: int,
        interval: float,
        episode_rate: float
    ):
        """
        Initialize simulator manager
        
        Args:
            registry_url: Registry service URL
            gateway_grpc_url: Telemetry Gateway gRPC URL
            num_devices: Number of devices to simulate
            interval: Interval between telemetry sends (seconds)
            episode_rate: Probability of episode per interval
        """
        self.registry_client = RegistryClient(registry_url)
        self.gateway_client = TelemetryGatewayClient(gateway_grpc_url)
        self.num_devices = num_devices
        self.interval = interval
        self.episode_rate = episode_rate
        self.simulators: list[DeviceSimulator] = []
    
    def initialize(self):
        """Initialize connections and fetch device data"""
        logger.info("Initializing simulator manager...")
        
        # Connect to gateway
        self.gateway_client.connect()
        
        # Fetch devices and patients
        devices = self.registry_client.get_devices(limit=100)
        patients = self.registry_client.get_patients(limit=100)
        
        # Create patient lookup
        patient_lookup = {str(p['id']): p for p in patients}
        
        # Select devices to simulate
        devices_to_simulate = devices[:self.num_devices]
        
        if len(devices_to_simulate) < self.num_devices:
            logger.warning(
                f"Only {len(devices_to_simulate)} devices available, "
                f"requested {self.num_devices}"
            )
        
        # Create simulators
        for device in devices_to_simulate:
            patient_id = str(device.get('patient_id')) if device.get('patient_id') else None
            patient = patient_lookup.get(patient_id) if patient_id else None
            
            threshold_profile = None
            if patient_id:
                threshold_profile = self.registry_client.get_threshold_profile(
                    UUID(patient_id)
                )
            
            simulator = DeviceSimulator(
                device=device,
                patient=patient,
                threshold_profile=threshold_profile,
                gateway_client=self.gateway_client,
                interval=self.interval,
                episode_rate=self.episode_rate
            )
            self.simulators.append(simulator)
        
        logger.info(f"Initialized {len(self.simulators)} device simulators")
    
    def start_all(self):
        """Start all simulators"""
        logger.info(f"Starting {len(self.simulators)} device simulators...")
        for simulator in self.simulators:
            simulator.start()
        logger.info("All simulators started")
    
    def stop_all(self):
        """Stop all simulators"""
        logger.info("Stopping all simulators...")
        for simulator in self.simulators:
            simulator.stop()
        self.gateway_client.close()
        logger.info("All simulators stopped")
    
    def get_stats(self) -> Dict:
        """Get statistics from all simulators"""
        total_telemetry = sum(s.telemetry_count for s in self.simulators)
        return {
            'num_devices': len(self.simulators),
            'total_telemetry_sent': total_telemetry,
            'interval': self.interval,
            'episode_rate': self.episode_rate
        }

