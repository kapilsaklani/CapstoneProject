from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_patient
from app.ml.inference import risk_engine
from app.models.clinical import RiskAssessment, SafetyAlert
from app.models.profile import PatientProfile
from app.models.user import User
from app.schemas.clinical import (
    BreastCancerAssessmentInput,
    DiabetesAssessmentInput,
    HeartAssessmentInput,
    RiskAssessmentOut,
)
from app.services.rules_engine import check_safety_thresholds, get_recommendation

router = APIRouter(prefix="/api/assessments", tags=["AI Risk Assessments"])


def _get_patient_profile(db: Session, user: User) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return profile


def _persist_assessment(
    db: Session, patient_id: str, disease_module: str, inputs: dict, result: dict
) -> RiskAssessment:
    recommendation = get_recommendation(disease_module, result["risk_level"], inputs)
    assessment = RiskAssessment(
        patient_id=patient_id,
        disease_module=disease_module,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        input_snapshot=inputs,
        explanation=result["explanation"],
        recommendation_text=recommendation,
        requires_clinician_review=result["requires_clinician_review"],
    )
    db.add(assessment)

    # Independent rule-based safety check on key raw values (glucose, BP, BMI)
    # regardless of what the ML model concluded.
    safety_map = {
        "Glucose": "glucose",
        "glucose": "glucose",
        "trestbps": "systolic_bp",
        "BMI": "bmi",
        "chol": "cholesterol",
    }
    for input_key, metric_name in safety_map.items():
        if input_key in inputs:
            alert = check_safety_thresholds(metric_name, float(inputs[input_key]))
            if alert:
                db.add(SafetyAlert(patient_id=patient_id, **alert))

    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/modules")
def list_disease_modules():
    """Lists the disease-specific assessment modules currently registered in the engine."""
    return {"modules": risk_engine.list_modules()}


@router.post("/diabetes", response_model=RiskAssessmentOut)
def assess_diabetes(
    payload: DiabetesAssessmentInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_patient_profile(db, current_user)
    inputs = payload.model_dump()
    result = risk_engine.assess("diabetes", inputs)
    return _persist_assessment(db, profile.id, "diabetes", inputs, result)


@router.post("/heart-disease", response_model=RiskAssessmentOut)
def assess_heart_disease(
    payload: HeartAssessmentInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_patient_profile(db, current_user)
    inputs = payload.model_dump()
    result = risk_engine.assess("heart_disease", inputs)
    return _persist_assessment(db, profile.id, "heart_disease", inputs, result)


@router.post("/breast-cancer-screening", response_model=RiskAssessmentOut)
def assess_breast_cancer(
    payload: BreastCancerAssessmentInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_patient_profile(db, current_user)
    # map underscored API field names back to the model's trained column names
    inputs = {
        "mean radius": payload.mean_radius,
        "mean texture": payload.mean_texture,
        "mean perimeter": payload.mean_perimeter,
        "mean area": payload.mean_area,
        "mean smoothness": payload.mean_smoothness,
        "mean compactness": payload.mean_compactness,
        "mean concavity": payload.mean_concavity,
        "mean concave points": payload.mean_concave_points,
        "mean symmetry": payload.mean_symmetry,
        "mean fractal dimension": payload.mean_fractal_dimension,
    }
    result = risk_engine.assess("breast_cancer_screening", inputs)
    return _persist_assessment(db, profile.id, "breast_cancer_screening", inputs, result)


@router.get("/history", response_model=list[RiskAssessmentOut])
def get_my_assessment_history(
    disease_module: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_patient_profile(db, current_user)
    query = db.query(RiskAssessment).filter(RiskAssessment.patient_id == profile.id)
    if disease_module:
        query = query.filter(RiskAssessment.disease_module == disease_module)
    return query.order_by(RiskAssessment.created_at.desc()).all()


@router.get("/patient/{patient_id}/history", response_model=list[RiskAssessmentOut])
def get_patient_assessment_history(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clinician view of a specific patient's assessment history (role-checked in service layer)."""
    from app.models.user import UserRole

    if current_user.role not in (UserRole.DOCTOR, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Doctor or admin access required")
    return (
        db.query(RiskAssessment)
        .filter(RiskAssessment.patient_id == patient_id)
        .order_by(RiskAssessment.created_at.desc())
        .all()
    )
