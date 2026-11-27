import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_patient
from app.models.clinical import LabReport, ReportStatus, VitalRecord
from app.models.profile import PatientProfile
from app.models.user import User
from app.schemas.clinical import LabReportIn, LabReportOut

router = APIRouter(prefix="/api/lab-reports", tags=["Lab Reports & Extraction"])

# Lightweight regex-based structured-value extractor simulating the OCR /
# information-extraction step called for in the proposal's workflow. A
# production system would swap this for a real OCR + NLP pipeline (e.g.
# Tesseract + a medical NER model) operating on the uploaded document image,
# but the extraction *contract* (raw text in, structured key/value out) is
# the same, so this module is a drop-in replacement point.
EXTRACTION_PATTERNS = {
    "Glucose": r"glucose[:\s]+(\d+\.?\d*)",
    "BloodPressure": r"(?:blood pressure|bp)[:\s]+(\d+)\s*/?\s*\d*",
    "BMI": r"bmi[:\s]+(\d+\.?\d*)",
    "Cholesterol": r"cholesterol[:\s]+(\d+\.?\d*)",
    "Hemoglobin": r"h(?:a)?emoglobin[:\s]+(\d+\.?\d*)",
    "HeartRate": r"(?:heart rate|pulse)[:\s]+(\d+)",
}


def extract_values_from_text(text: str) -> dict:
    values = {}
    lower = text.lower()
    for key, pattern in EXTRACTION_PATTERNS.items():
        match = re.search(pattern, lower)
        if match:
            values[key] = float(match.group(1))
    return values


def _get_profile(db: Session, user: User) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return profile


@router.post("", response_model=LabReportOut, status_code=201)
def upload_lab_report(
    payload: LabReportIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)

    extracted = dict(payload.extracted_values)
    status = ReportStatus.EXTRACTED if extracted else ReportStatus.UPLOADED

    if payload.raw_text:
        auto_extracted = extract_values_from_text(payload.raw_text)
        # manual values take precedence over auto-extracted ones
        extracted = {**auto_extracted, **extracted}
        status = ReportStatus.EXTRACTED

    report = LabReport(
        patient_id=profile.id,
        report_type=payload.report_type,
        file_name=payload.file_name,
        raw_text=payload.raw_text,
        extracted_values=extracted,
        status=status,
    )
    db.add(report)

    # Feed extracted values into the longitudinal vitals timeline automatically
    metric_map = {
        "Glucose": ("glucose", "mg/dL"),
        "BMI": ("bmi", "kg/m^2"),
        "Cholesterol": ("cholesterol", "mg/dL"),
        "Hemoglobin": ("hemoglobin", "g/dL"),
        "HeartRate": ("heart_rate", "bpm"),
    }
    for key, val in extracted.items():
        if key in metric_map:
            metric_name, unit = metric_map[key]
            db.add(VitalRecord(patient_id=profile.id, metric_name=metric_name, value=val, unit=unit, source="lab_report"))

    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=list[LabReportOut])
def list_lab_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    return (
        db.query(LabReport)
        .filter(LabReport.patient_id == profile.id)
        .order_by(LabReport.uploaded_at.desc())
        .all()
    )
