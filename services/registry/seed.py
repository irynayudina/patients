"""Seed script to create initial data"""
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Patient, Device, ThresholdProfile

# Create database session
db: Session = SessionLocal()


def seed_data():
    """Seed the database with 5 patients and 5 devices with thresholds"""
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    db.query(ThresholdProfile).delete()
    db.query(Device).delete()
    db.query(Patient).delete()
    db.commit()
    
    # Create 5 patients
    patients_data = [
        {"full_name": "John Doe", "age": 45, "sex": "M"},
        {"full_name": "Jane Smith", "age": 32, "sex": "F"},
        {"full_name": "Robert Johnson", "age": 58, "sex": "M"},
        {"full_name": "Emily Davis", "age": 28, "sex": "F"},
        {"full_name": "Michael Brown", "age": 67, "sex": "M"},
    ]
    
    patients = []
    for patient_data in patients_data:
        patient = Patient(**patient_data)
        db.add(patient)
        patients.append(patient)
    
    db.commit()
    
    # Refresh to get IDs
    for patient in patients:
        db.refresh(patient)
    
    # Create 5 devices
    devices_data = [
        {"serial": "DEV001", "firmware": "v1.2.3", "patient_id": patients[0].id},
        {"serial": "DEV002", "firmware": "v1.3.0", "patient_id": patients[1].id},
        {"serial": "DEV003", "firmware": "v1.2.1", "patient_id": patients[2].id},
        {"serial": "DEV004", "firmware": "v1.4.0", "patient_id": patients[3].id},
        {"serial": "DEV005", "firmware": "v1.2.5", "patient_id": patients[4].id},
    ]
    
    devices = []
    for device_data in devices_data:
        device = Device(**device_data)
        db.add(device)
        devices.append(device)
    
    db.commit()
    
    # Create threshold profiles for each patient
    threshold_profiles_data = [
        {"patient_id": patients[0].id, "hr_min": 60, "hr_max": 100, "spo2_min": 95, "temp_min": 36.1, "temp_max": 37.2},
        {"patient_id": patients[1].id, "hr_min": 65, "hr_max": 105, "spo2_min": 96, "temp_min": 36.0, "temp_max": 37.0},
        {"patient_id": patients[2].id, "hr_min": 55, "hr_max": 95, "spo2_min": 94, "temp_min": 35.8, "temp_max": 37.5},
        {"patient_id": patients[3].id, "hr_min": 70, "hr_max": 110, "spo2_min": 97, "temp_min": 36.2, "temp_max": 37.1},
        {"patient_id": patients[4].id, "hr_min": 50, "hr_max": 90, "spo2_min": 93, "temp_min": 35.5, "temp_max": 37.8},
    ]
    
    for profile_data in threshold_profiles_data:
        profile = ThresholdProfile(**profile_data)
        db.add(profile)
    
    db.commit()
    
    print("✓ Seeded 5 patients")
    print("✓ Seeded 5 devices")
    print("✓ Seeded 5 threshold profiles")
    print("\nPatient IDs:")
    for patient in patients:
        print(f"  - {patient.full_name}: {patient.id}")
    print("\nDevice IDs:")
    for device in devices:
        print(f"  - {device.serial}: {device.id}")


if __name__ == "__main__":
    try:
        seed_data()
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

