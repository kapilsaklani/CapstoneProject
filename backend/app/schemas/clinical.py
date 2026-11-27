from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class DiabetesAssessmentInput(BaseModel):
    Pregnancies: float = 0
    Glucose: float = 120
    BloodPressure: float = 80
    SkinThickness: float = 20
    Insulin: float = 80
    BMI: float = 25.0
    DiabetesPedigreeFunction: float = 0.5
    Age: float = 40

class HeartAssessmentInput(BaseModel):
    age: float = 50
    sex: float = 1
    cp: float = 0
    trestbps: float = 120
    chol: float = 200
    fbs: float = 0
    restecg: float = 0
    thalach: float = 150
    exang: float = 0
    oldpeak: float = 0.0
    slope: float = 1
    ca: float = 0
    thal: float = 2

class BreastCancerAssessmentInput(BaseModel):
    mean_radius: float = 14.0
    mean_texture: float = 19.0
    mean_perimeter: float = 90.0
    mean_area: float = 600.0
    mean_smoothness: float = 0.1
    mean_compactness: float = 0.1
    mean_concavity: float = 0.08
    mean_concave_points: float = 0.05
    mean_symmetry: float = 0.18
    mean_fractal_dimension: float = 0.06

class RiskAssessmentOut(BaseModel):
    id: str
    patient_id: str
    disease_module: str
    risk_score: float
    risk_level: str
    input_snapshot: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    recommendation_text: Optional[str] = None
    requires_clinician_review: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SafetyAlertOut(BaseModel):
    id: str
    patient_id: str
    metric: str
    level: str
    message: str
    acknowledged: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PatientProfileOut(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None
    known_conditions: Optional[str] = None
    allergies: Optional[str] = None

    class Config:
        from_attributes = True

class PatientProfileUpdate(BaseModel):
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None
    known_conditions: Optional[str] = None
    allergies: Optional[str] = None

class VitalRecordIn(BaseModel):
    metric_name: str
    value: float
    unit: Optional[str] = None
    recorded_at: Optional[datetime] = None
    source: Optional[str] = "manual"

class VitalRecordOut(BaseModel):
    id: str
    patient_id: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    recorded_at: Optional[datetime] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True

class LabReportIn(BaseModel):
    report_type: str = "General"
    file_name: str = "report.txt"
    raw_text: Optional[str] = None
    extracted_values: Dict[str, float] = Field(default_factory=dict)

class LabReportOut(BaseModel):
    id: str
    patient_id: str
    report_type: str
    file_name: str
    raw_text: Optional[str] = None
    extracted_values: Optional[Dict[str, Any]] = None
    status: str
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AppointmentIn(BaseModel):
    title: str
    doctor_name: Optional[str] = None
    scheduled_at: datetime
    notes: Optional[str] = None

class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    title: str
    doctor_name: Optional[str] = None
    scheduled_at: datetime
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ReminderIn(BaseModel):
    title: str
    due_at: datetime

class ReminderOut(BaseModel):
    id: str
    patient_id: str
    title: str
    due_at: datetime
    is_completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
