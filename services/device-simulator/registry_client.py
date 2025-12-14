"""Client for interacting with Registry service"""
import requests
from typing import List, Dict, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class RegistryClient:
    """Client to fetch devices and patients from Registry service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def get_devices(self, limit: int = 100) -> List[Dict]:
        """Get all devices from registry"""
        try:
            response = requests.get(
                f"{self.base_url}/devices",
                params={"limit": limit},
                timeout=10
            )
            response.raise_for_status()
            devices = response.json()
            logger.info(f"Fetched {len(devices)} devices from registry")
            return devices
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch devices: {e}")
            raise
    
    def get_patients(self, limit: int = 100) -> List[Dict]:
        """Get all patients from registry"""
        try:
            response = requests.get(
                f"{self.base_url}/patients",
                params={"limit": limit},
                timeout=10
            )
            response.raise_for_status()
            patients = response.json()
            logger.info(f"Fetched {len(patients)} patients from registry")
            return patients
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch patients: {e}")
            raise
    
    def get_device(self, device_id: UUID) -> Optional[Dict]:
        """Get a specific device by ID"""
        try:
            response = requests.get(
                f"{self.base_url}/devices/{device_id}",
                timeout=10
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch device {device_id}: {e}")
            return None
    
    def get_threshold_profile(self, patient_id: UUID) -> Optional[Dict]:
        """Get threshold profile for a patient"""
        try:
            response = requests.get(
                f"{self.base_url}/thresholds/{patient_id}",
                timeout=10
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch threshold profile for patient {patient_id}: {e}")
            return None

