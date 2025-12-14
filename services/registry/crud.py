"""CRUD operations"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from models import Patient, Device, ThresholdProfile
from schemas import (
    PatientCreate, DeviceCreate, DeviceUpdate,
    ThresholdProfileCreate
)


# Patient CRUD
def create_patient(db: Session, patient: PatientCreate) -> Patient:
    """Create a new patient"""
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def get_patient(db: Session, patient_id: UUID) -> Optional[Patient]:
    """Get a patient by ID"""
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    """Get all patients"""
    return db.query(Patient).offset(skip).limit(limit).all()


# Device CRUD
def create_device(db: Session, device: DeviceCreate) -> Device:
    """Create a new device"""
    db_device = Device(**device.model_dump())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def get_device(db: Session, device_id: UUID) -> Optional[Device]:
    """Get a device by ID"""
    return db.query(Device).filter(Device.id == device_id).first()


def get_devices(db: Session, skip: int = 0, limit: int = 100) -> List[Device]:
    """Get all devices"""
    return db.query(Device).offset(skip).limit(limit).all()


def update_device(db: Session, device_id: UUID, device_update: DeviceUpdate) -> Optional[Device]:
    """Update a device"""
    db_device = get_device(db, device_id)
    if not db_device:
        return None
    
    update_data = device_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_device, field, value)
    
    db.commit()
    db.refresh(db_device)
    return db_device


def link_device_to_patient(db: Session, device_id: UUID, patient_id: UUID) -> Optional[Device]:
    """Link a device to a patient"""
    db_device = get_device(db, device_id)
    db_patient = get_patient(db, patient_id)
    
    if not db_device:
        return None
    if not db_patient:
        return None
    
    db_device.patient_id = patient_id
    db.commit()
    db.refresh(db_device)
    return db_device


# Threshold Profile CRUD
def create_threshold_profile(db: Session, profile: ThresholdProfileCreate) -> ThresholdProfile:
    """Create a new threshold profile"""
    db_profile = ThresholdProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile


def get_threshold_profile(db: Session, patient_id: UUID) -> Optional[ThresholdProfile]:
    """Get threshold profile by patient ID"""
    return db.query(ThresholdProfile).filter(ThresholdProfile.patient_id == patient_id).first()


def get_threshold_profiles(db: Session, skip: int = 0, limit: int = 100) -> List[ThresholdProfile]:
    """Get all threshold profiles"""
    return db.query(ThresholdProfile).offset(skip).limit(limit).all()

