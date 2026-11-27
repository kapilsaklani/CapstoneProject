from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_patient
from app.models.clinical import SafetyAlert, VitalRecord
from app.models.profile import PatientProfile
from app.models.user import User
from app.schemas.clinical import VitalRecordIn, VitalRecordOut
from app.services.rules_engine import check_safety_thresholds

router = APIRouter(prefix="/api/vitals", tags=["Vitals & Trends"])


def _get_profile(db: Session, user: User) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return profile


@router.post("", response_model=VitalRecordOut, status_code=201)
def record_vital(
    payload: VitalRecordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    record = VitalRecord(
        patient_id=profile.id,
        metric_name=payload.metric_name,
        value=payload.value,
        unit=payload.unit,
        recorded_at=payload.recorded_at or datetime.utcnow(),
        source=payload.source,
    )
    db.add(record)

    alert = check_safety_thresholds(payload.metric_name, payload.value)
    if alert:
        db.add(SafetyAlert(patient_id=profile.id, **alert))

    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[VitalRecordOut])
def list_vitals(
    metric_name: str | None = None,
    days: int = 180,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.query(VitalRecord).filter(
        VitalRecord.patient_id == profile.id, VitalRecord.recorded_at >= cutoff
    )
    if metric_name:
        query = query.filter(VitalRecord.metric_name == metric_name)
    return query.order_by(VitalRecord.recorded_at.asc()).all()


@router.get("/trends/summary")
def trend_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    """
    Longitudinal trend summary per metric: first vs latest value, simple
    delta, and direction — powers the patient dashboard's trend cards.
    """
    profile = _get_profile(db, current_user)
    records = (
        db.query(VitalRecord)
        .filter(VitalRecord.patient_id == profile.id)
        .order_by(VitalRecord.recorded_at.asc())
        .all()
    )
    by_metric: dict[str, list[VitalRecord]] = {}
    for r in records:
        by_metric.setdefault(r.metric_name, []).append(r)

    summary = {}
    for metric, series in by_metric.items():
        first, latest = series[0], series[-1]
        delta = latest.value - first.value
        summary[metric] = {
            "first_value": first.value,
            "latest_value": latest.value,
            "delta": round(delta, 2),
            "direction": "up" if delta > 0 else ("down" if delta < 0 else "flat"),
            "data_points": len(series),
            "unit": latest.unit,
            "series": [
                {"date": r.recorded_at.isoformat(), "value": r.value} for r in series
            ],
        }
    return summary
