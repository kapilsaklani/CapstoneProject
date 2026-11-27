from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_patient
from app.models.clinical import Appointment, Reminder
from app.models.profile import PatientProfile
from app.models.user import User
from app.schemas.clinical import AppointmentIn, AppointmentOut, ReminderIn, ReminderOut

router = APIRouter(prefix="/api/care-plan", tags=["Appointments & Reminders"])


def _get_profile(db: Session, user: User) -> PatientProfile:
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return profile


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
def create_appointment(
    payload: AppointmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    appt = Appointment(patient_id=profile.id, **payload.model_dump())
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.get("/appointments", response_model=list[AppointmentOut])
def list_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    return (
        db.query(Appointment)
        .filter(Appointment.patient_id == profile.id)
        .order_by(Appointment.scheduled_at.asc())
        .all()
    )


@router.patch("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: str,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.patient_id == profile.id)
        .first()
    )
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = status
    db.commit()
    return {"id": appt.id, "status": appt.status}


@router.post("/reminders", response_model=ReminderOut, status_code=201)
def create_reminder(
    payload: ReminderIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    reminder = Reminder(patient_id=profile.id, **payload.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/reminders", response_model=list[ReminderOut])
def list_reminders(
    include_completed: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    query = db.query(Reminder).filter(Reminder.patient_id == profile.id)
    if not include_completed:
        query = query.filter(Reminder.is_completed == False)  # noqa: E712
    return query.order_by(Reminder.due_at.asc()).all()


@router.patch("/reminders/{reminder_id}/complete", response_model=ReminderOut)
def complete_reminder(
    reminder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient),
):
    profile = _get_profile(db, current_user)
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.patient_id == profile.id)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.is_completed = True
    reminder.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(reminder)
    return reminder
