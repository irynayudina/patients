"""SQLAlchemy models"""
from sqlalchemy import Column, String, Integer, ForeignKey, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base


class Patient(Base):
    """Patient model"""
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String(10), nullable=False)  # M, F, Other
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    devices = relationship("Device", back_populates="patient", cascade="all, delete-orphan")
    threshold_profile = relationship("ThresholdProfile", back_populates="patient", uselist=False, cascade="all, delete-orphan")


class Device(Base):
    """Device model"""
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    serial = Column(String(100), unique=True, nullable=False)
    firmware = Column(String(50), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="devices")


class ThresholdProfile(Base):
    """Threshold profile model"""
    __tablename__ = "threshold_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, unique=True)
    hr_min = Column(Float, nullable=False)
    hr_max = Column(Float, nullable=False)
    spo2_min = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="threshold_profile")

