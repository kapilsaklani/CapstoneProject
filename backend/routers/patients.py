from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_patient
from app.models.clinical import SafetyAlert
from app.models.profile import PatientProfile
from app.models.user import User
from app.schemas.clinical import PatientProfileOut, PatientProfileUpdate, SafetyAlertOut

router = APIRouter(prefix="/api/patients", tags=["Patient Profile"])


def _get_profile(db: Session, user: User) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return profile


@router.get("/me", response_model=PatientProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    return PatientProfileOut(
        id=profile.id,
        full_name=current_user.full_name,
        email=current_user.email,
        date_of_birth=str(profile.date_of_birth) if profile.date_of_birth else None,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        blood_group=profile.blood_group,
        known_conditions=profile.known_conditions,
        allergies=profile.allergies,
    )


@router.patch("/me", response_model=PatientProfileOut)
def update_my_profile(
    payload: PatientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return PatientProfileOut(
        id=profile.id,
        full_name=current_user.full_name,
        email=current_user.email,
        date_of_birth=str(profile.date_of_birth) if profile.date_of_birth else None,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        blood_group=profile.blood_group,
        known_conditions=profile.known_conditions,
        allergies=profile.allergies,
    )


@router.get("/me/alerts", response_model=list[SafetyAlertOut])
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    return (
        db.query(SafetyAlert)
        .filter(SafetyAlert.patient_id == profile.id)
        .order_by(SafetyAlert.created_at.desc())
        .all()
    )
