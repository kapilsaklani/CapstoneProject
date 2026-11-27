from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import require_doctor_or_admin
from app.models.clinical import RiskAssessment, SafetyAlert
from app.models.profile import DoctorProfile, PatientProfile
from app.models.user import User
from app.schemas.clinical import PatientProfileOut, RiskAssessmentOut, SafetyAlertOut

router = APIRouter(prefix="/api/doctor", tags=["Clinician Dashboard"])


def _get_doctor_profile(db: Session, user: User) -> DoctorProfile:
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return profile


@router.get("/patients", response_model=list[PatientProfileOut])
def list_my_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor_or_admin),
):
    """
    Returns patients assigned to this clinician, each enriched with
    full_name/email pulled from the linked User record.
    """
    doctor = _get_doctor_profile(db, current_user)
    patients = (
        db.query(PatientProfile)
        .options(joinedload(PatientProfile.user))
        .filter(PatientProfile.assigned_doctor_id == doctor.id)
        .all()
    )
    out = []
    for p in patients:
        out.append(
            PatientProfileOut(
                id=p.id,
                full_name=p.user.full_name if p.user else None,
                email=p.user.email if p.user else None,
                date_of_birth=str(p.date_of_birth) if p.date_of_birth else None,
                sex=p.sex,
                height_cm=p.height_cm,
                weight_kg=p.weight_kg,
                blood_group=p.blood_group,
                known_conditions=p.known_conditions,
                allergies=p.allergies,
            )
        )
    return out


@router.get("/flagged-patients")
def flagged_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor_or_admin),
):
    """
    Patients with at least one risk assessment or safety alert that needs
    clinician review, sorted by most recent flag first — this is the
    triage queue on the clinician dashboard.
    """
    doctor = _get_doctor_profile(db, current_user)
    patient_ids = [
        p.id
        for p in db.query(PatientProfile).filter(PatientProfile.assigned_doctor_id == doctor.id)
    ]
    flagged_assessments = (
        db.query(RiskAssessment)
        .filter(
            RiskAssessment.patient_id.in_(patient_ids),
            RiskAssessment.requires_clinician_review == True,  # noqa: E712
        )
        .order_by(RiskAssessment.created_at.desc())
        .all()
    )
    unacknowledged_alerts = (
        db.query(SafetyAlert)
        .filter(SafetyAlert.patient_id.in_(patient_ids), SafetyAlert.acknowledged == False)  # noqa: E712
        .order_by(SafetyAlert.created_at.desc())
        .all()
    )
    return {
        "flagged_assessments": [RiskAssessmentOut.model_validate(a) for a in flagged_assessments],
        "unacknowledged_alerts": [SafetyAlertOut.model_validate(a) for a in unacknowledged_alerts],
    }


@router.patch("/assessments/{assessment_id}/review")
def mark_assessment_reviewed(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor_or_admin),
):
    doctor = _get_doctor_profile(db, current_user)
    assessment = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    assessment.requires_clinician_review = False
    assessment.reviewed_by_doctor_id = doctor.id
    db.commit()
    return {"id": assessment.id, "reviewed": True}


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor_or_admin),
):
    alert = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.commit()
    return {"id": alert.id, "acknowledged": True}


@router.post("/assign-patient/{patient_id}")
def assign_patient_to_me(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor_or_admin),
):
    doctor = _get_doctor_profile(db, current_user)
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.assigned_doctor_id = doctor.id
    db.commit()
    return {"patient_id": patient_id, "assigned_doctor_id": doctor.id}
