"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


# Patient schemas
class PatientBase(BaseModel):
    """Base patient schema"""
    full_name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(..., ge=0, le=150)
    sex: str = Field(..., pattern="^(M|F|Other)$")


class PatientCreate(PatientBase):
    """Schema for creating a patient"""
    pass


class PatientResponse(PatientBase):
    """Schema for patient response"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# Device schemas
class DeviceBase(BaseModel):
    """Base device schema"""
    serial: str = Field(..., min_length=1, max_length=100)
    firmware: str = Field(..., min_length=1, max_length=50)


class DeviceCreate(DeviceBase):
    """Schema for creating a device"""
    patient_id: Optional[UUID] = None


class DeviceUpdate(BaseModel):
    """Schema for updating a device"""
    patient_id: Optional[UUID] = None
    firmware: Optional[str] = Field(None, min_length=1, max_length=50)


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: UUID
    patient_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Threshold profile schemas
class ThresholdProfileBase(BaseModel):
    """Base threshold profile schema"""
    hr_min: float = Field(..., ge=0)
    hr_max: float = Field(..., ge=0)
    spo2_min: float = Field(..., ge=0, le=100)
    temp_min: float = Field(..., ge=0)
    temp_max: float = Field(..., ge=0)
    
    @validator('hr_max')
    def hr_max_greater_than_min(cls, v, values):
        if 'hr_min' in values and v <= values['hr_min']:
            raise ValueError('hr_max must be greater than hr_min')
        return v
    
    @validator('temp_max')
    def temp_max_greater_than_min(cls, v, values):
        if 'temp_min' in values and v <= values['temp_min']:
            raise ValueError('temp_max must be greater than temp_min')
        return v


class ThresholdProfileCreate(ThresholdProfileBase):
    """Schema for creating a threshold profile"""
    patient_id: UUID


class ThresholdProfileResponse(ThresholdProfileBase):
    """Schema for threshold profile response"""
    id: UUID
    patient_id: UUID
    
    class Config:
        from_attributes = True


# Link device to patient
class LinkDeviceRequest(BaseModel):
    """Schema for linking device to patient"""
    device_id: UUID
    patient_id: UUID

