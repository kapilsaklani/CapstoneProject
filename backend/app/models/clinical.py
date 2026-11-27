import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Enum
from app.core.database import Base

class ReportStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    REVIEWED = "reviewed"

class RiskAssessment(Base):
    __tablename__ = "core_risk_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    disease_module = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(30), nullable=False)
    input_snapshot = Column(JSON, nullable=True)
    explanation = Column(JSON, nullable=True)
    recommendation_text = Column(String(500), nullable=True)
    requires_clinician_review = Column(Boolean, default=False)
    reviewed_by_doctor_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SafetyAlert(Base):
    __tablename__ = "core_safety_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    metric = Column(String(50), nullable=False)
    level = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VitalRecord(Base):
    __tablename__ = "core_vital_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    metric_name = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50), default="manual")

class LabReport(Base):
    __tablename__ = "core_lab_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    report_type = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    raw_text = Column(String, nullable=True)
    extracted_values = Column(JSON, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.UPLOADED)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class Appointment(Base):
    __tablename__ = "core_appointments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    title = Column(String(150), nullable=False)
    doctor_name = Column(String(100), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(30), default="scheduled")
    notes = Column(String(255), nullable=True)

class Reminder(Base):
    __tablename__ = "core_reminders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False)
    title = Column(String(150), nullable=False)
    due_at = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
