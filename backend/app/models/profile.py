import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base

class PatientProfile(Base):
    __tablename__ = "core_patient_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("core_users.id"), unique=True, nullable=False)
    assigned_doctor_id = Column(String(36), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    sex = Column(String(20), nullable=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    blood_group = Column(String(10), nullable=True)
    known_conditions = Column(String(255), nullable=True)
    allergies = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="patient_profile")


class DoctorProfile(Base):
    __tablename__ = "core_doctor_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("core_users.id"), unique=True, nullable=False)
    specialization = Column(String(100), nullable=True)
    license_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="doctor_profile")
