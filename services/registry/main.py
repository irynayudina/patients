"""FastAPI application with REST and gRPC endpoints"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import grpc
from concurrent import futures
from datetime import datetime

from config import settings
from database import get_db, engine, Base
from models import Patient, Device, ThresholdProfile
from schemas import (
    PatientCreate, PatientResponse,
    DeviceCreate, DeviceResponse, DeviceUpdate,
    ThresholdProfileCreate, ThresholdProfileResponse,
    LinkDeviceRequest
)
from crud import (
    create_patient, get_patient, get_patients,
    create_device, get_device, get_devices, update_device, link_device_to_patient,
    create_threshold_profile, get_threshold_profile, get_threshold_profiles
)

# Import generated gRPC code
try:
    from generated import registry_pb2
    from generated import registry_pb2_grpc
except ImportError:
    # Fallback if generated code doesn't exist yet
    registry_pb2 = None
    registry_pb2_grpc = None

app = FastAPI(
    title="Registry Service",
    description="CRUD service for patients, devices, and threshold profiles with gRPC endpoints",
    version="1.0.0",
)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "registry-service"
    }


# Patient REST endpoints
@app.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_endpoint(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    return create_patient(db, patient)


@app.get("/patients", response_model=List[PatientResponse])
async def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all patients"""
    return get_patients(db, skip=skip, limit=limit)


@app.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient_endpoint(patient_id: UUID, db: Session = Depends(get_db)):
    """Get a patient by ID"""
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


# Device REST endpoints
@app.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device_endpoint(device: DeviceCreate, db: Session = Depends(get_db)):
    """Create a new device"""
    return create_device(db, device)


@app.get("/devices", response_model=List[DeviceResponse])
async def list_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all devices"""
    return get_devices(db, skip=skip, limit=limit)


@app.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device_endpoint(device_id: UUID, db: Session = Depends(get_db)):
    """Get a device by ID"""
    device = get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.patch("/devices/{device_id}", response_model=DeviceResponse)
async def update_device_endpoint(
    device_id: UUID,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """Update a device"""
    device = update_device(db, device_id, device_update)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.post("/devices/link", response_model=DeviceResponse)
async def link_device_endpoint(link_request: LinkDeviceRequest, db: Session = Depends(get_db)):
    """Link a device to a patient"""
    device = link_device_to_patient(db, link_request.device_id, link_request.patient_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device or patient not found")
    return device


# Threshold Profile REST endpoints
@app.post("/thresholds", response_model=ThresholdProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold_endpoint(profile: ThresholdProfileCreate, db: Session = Depends(get_db)):
    """Create a new threshold profile"""
    # Check if patient exists
    patient = get_patient(db, profile.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Check if profile already exists
    existing = get_threshold_profile(db, profile.patient_id)
    if existing:
        raise HTTPException(status_code=400, detail="Threshold profile already exists for this patient")
    
    return create_threshold_profile(db, profile)


@app.get("/thresholds", response_model=List[ThresholdProfileResponse])
async def list_thresholds(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all threshold profiles"""
    return get_threshold_profiles(db, skip=skip, limit=limit)


@app.get("/thresholds/{patient_id}", response_model=ThresholdProfileResponse)
async def get_threshold_endpoint(patient_id: UUID, db: Session = Depends(get_db)):
    """Get threshold profile by patient ID"""
    profile = get_threshold_profile(db, patient_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Threshold profile not found")
    return profile


# gRPC Service Implementation
class RegistryService(registry_pb2_grpc.RegistryServicer):
    """gRPC service implementation"""
    
    def GetDevice(self, request, context):
        """Get device by ID"""
        if not registry_pb2:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("gRPC stubs not generated")
            return registry_pb2.GetDeviceResponse()
        
        db = next(get_db())
        try:
            device_id = UUID(request.device_id)
            device = get_device(db, device_id)
            
            response = registry_pb2.GetDeviceResponse()
            response.version = "1.0.0"
            response.timestamp = datetime.utcnow().isoformat() + "Z"
            
            if not device:
                response.status = registry_pb2.STATUS_NOT_FOUND
                return response
            
            response.status = registry_pb2.STATUS_SUCCESS
            response.device.device_id = str(device.id)
            response.device.device_type = "medical_device"  # Default, can be extended
            if device.patient_id:
                response.device.patient_id = str(device.patient_id)
            response.device.status = registry_pb2.DEVICE_STATUS_ACTIVE
            response.device.metadata["serial"] = device.serial
            response.device.metadata["firmware"] = device.firmware
            response.device.registered_at = device.created_at.isoformat() + "Z"
            response.device.updated_at = device.created_at.isoformat() + "Z"
            
            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = registry_pb2.GetDeviceResponse()
            response.version = "1.0.0"
            response.status = registry_pb2.STATUS_INTERNAL_ERROR
            response.timestamp = datetime.utcnow().isoformat() + "Z"
            return response
        finally:
            db.close()
    
    def GetPatient(self, request, context):
        """Get patient by ID"""
        if not registry_pb2:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("gRPC stubs not generated")
            return registry_pb2.GetPatientResponse()
        
        db = next(get_db())
        try:
            patient_id = UUID(request.patient_id)
            patient = get_patient(db, patient_id)
            
            response = registry_pb2.GetPatientResponse()
            response.version = "1.0.0"
            response.timestamp = datetime.utcnow().isoformat() + "Z"
            
            if not patient:
                response.status = registry_pb2.STATUS_NOT_FOUND
                return response
            
            response.status = registry_pb2.STATUS_SUCCESS
            response.patient.patient_id = str(patient.id)
            response.patient.age = patient.age
            # Map sex to gender enum
            if patient.sex == "M":
                response.patient.gender = registry_pb2.GENDER_MALE
            elif patient.sex == "F":
                response.patient.gender = registry_pb2.GENDER_FEMALE
            else:
                response.patient.gender = registry_pb2.GENDER_OTHER
            response.patient.metadata["full_name"] = patient.full_name
            response.patient.registered_at = patient.created_at.isoformat() + "Z"
            response.patient.updated_at = patient.created_at.isoformat() + "Z"
            
            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = registry_pb2.GetPatientResponse()
            response.version = "1.0.0"
            response.status = registry_pb2.STATUS_INTERNAL_ERROR
            response.timestamp = datetime.utcnow().isoformat() + "Z"
            return response
        finally:
            db.close()
    
    def GetThresholdProfile(self, request, context):
        """Get threshold profile by patient ID"""
        if not registry_pb2:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("gRPC stubs not generated")
            return registry_pb2.GetThresholdProfileResponse()
        
        db = next(get_db())
        try:
            patient_id = UUID(request.patient_id)
            profile = get_threshold_profile(db, patient_id)
            
            response = registry_pb2.GetThresholdProfileResponse()
            response.version = "1.0.0"
            response.timestamp = datetime.utcnow().isoformat() + "Z"
            
            if not profile:
                response.status = registry_pb2.STATUS_NOT_FOUND
                return response
            
            response.status = registry_pb2.STATUS_SUCCESS
            response.profile.profile_id = str(profile.id)
            response.profile.patient_id = str(profile.patient_id)
            if request.device_id:
                response.profile.device_id = request.device_id
            
            # Set heart rate thresholds
            response.profile.heart_rate.lower_bound = profile.hr_min
            response.profile.heart_rate.upper_bound = profile.hr_max
            response.profile.heart_rate.unit = "bpm"
            
            # Set oxygen saturation thresholds
            response.profile.oxygen_saturation.lower_bound = profile.spo2_min
            response.profile.oxygen_saturation.upper_bound = 100.0
            response.profile.oxygen_saturation.unit = "%"
            
            # Set temperature thresholds
            response.profile.temperature.lower_bound = profile.temp_min
            response.profile.temperature.upper_bound = profile.temp_max
            response.profile.temperature.unit = "°C"
            
            return response
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            response = registry_pb2.GetThresholdProfileResponse()
            response.version = "1.0.0"
            response.status = registry_pb2.STATUS_INTERNAL_ERROR
            response.timestamp = datetime.utcnow().isoformat() + "Z"
            return response
        finally:
            db.close()


def create_grpc_server():
    """Create and configure gRPC server"""
    if not registry_pb2_grpc:
        return None
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    registry_pb2_grpc.add_RegistryServicer_to_server(RegistryService(), server)
    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    return server


def run_grpc_server():
    """Run gRPC server in background thread"""
    if not registry_pb2_grpc:
        print("Warning: gRPC stubs not generated. gRPC server will not start.")
        return
    
    server = create_grpc_server()
    if server:
        server.start()
        print(f"gRPC server started on {settings.grpc_host}:{settings.grpc_port}")
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            server.stop(0)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start gRPC server on startup"""
    # Initialize database tables (fallback if migrations haven't run)
    Base.metadata.create_all(bind=engine)
    
    # Start gRPC server
    if registry_pb2_grpc:
        import threading
        grpc_thread = threading.Thread(target=run_grpc_server, daemon=True)
        grpc_thread.start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)

