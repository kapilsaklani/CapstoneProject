import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from jose import jwt

from app.agents import patient_agent, doctor_agent
from app.database import get_database_connection
from app.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/agents", tags=["AI Clinical Agents"])


def get_optional_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"user_id": 1, "email": "patient@medassist.ai", "role": "patient"}
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "user_id": int(payload.get("sub", 1)),
            "email": payload.get("email"),
            "role": payload.get("role", "patient"),
        }
    except Exception:
        return {"user_id": 1, "email": "patient@medassist.ai", "role": "patient"}


class PatientAgentRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class DoctorAgentRequest(BaseModel):
    message: str = Field(..., min_length=1)
    patient_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


def _fetch_patient_context(user_id: int) -> dict:
    ctx = {"patient_name": "Patient", "recent_symptoms": [], "latest_risk": None, "multi_disease_risk": None}
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        # User name
        cur.execute("SELECT full_name FROM users WHERE id = %s", (user_id,))
        u = cur.fetchone()
        if u:
            ctx["patient_name"] = u[0]

        # Recent symptoms
        cur.execute(
            "SELECT symptom_name, severity, recorded_at FROM patient_symptoms WHERE user_id = %s ORDER BY recorded_at DESC LIMIT 5",
            (user_id,),
        )
        symptoms = cur.fetchall()
        ctx["recent_symptoms"] = [{"symptom_name": s[0], "severity": s[1]} for s in symptoms]

        # Latest disease prediction
        cur.execute(
            "SELECT predicted_disease, created_at FROM disease_predictions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
        pred = cur.fetchone()
        if pred:
            ctx["latest_prediction"] = {"predicted_disease": pred[0]}

        # Latest general risk assessment
        cur.execute(
            "SELECT predicted_outcome, positive_model_score, blood_pressure, cholesterol_level FROM patient_risk_assessments WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
        risk = cur.fetchone()
        if risk:
            ctx["latest_risk"] = {
                "predicted_outcome": risk[0],
                "positive_model_score": float(risk[1]) if risk[1] else 0.0,
                "blood_pressure": risk[2],
                "cholesterol_level": risk[3],
            }

        # Latest multi-disease assessment
        try:
            cur.execute(
                "SELECT disease_module, risk_score, risk_level, feature_inputs, top_factors FROM multi_disease_assessments WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            )
            m_risk = cur.fetchone()
            if m_risk:
                ctx["multi_disease_risk"] = {
                    "disease_module": m_risk[0],
                    "risk_score": float(m_risk[1]),
                    "risk_percentage": round(float(m_risk[1]) * 100, 1),
                    "risk_level": m_risk[2],
                    "explanation": {"top_factors": json.loads(m_risk[4]) if m_risk[4] else []},
                }
        except Exception:
            pass

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Notice: unable to load full patient context: {e}")

    return ctx


def _fetch_doctor_context(doctor_user_id: int, target_patient_id: Optional[int]) -> dict:
    ctx = {"doctor_name": "Clinician", "flagged_count": 0, "patient_data": {}}
    try:
        conn = get_database_connection()
        cur = conn.cursor()

        # Doctor Name
        cur.execute("SELECT full_name FROM users WHERE id = %s", (doctor_user_id,))
        doc = cur.fetchone()
        if doc:
            ctx["doctor_name"] = doc[0]

        # Flagged count
        try:
            cur.execute(
                "SELECT COUNT(*) FROM multi_disease_assessments WHERE requires_clinician_review = 1"
            )
            fc = cur.fetchone()
            if fc:
                ctx["flagged_count"] = fc[0]
        except Exception:
            ctx["flagged_count"] = 1

        # Specific patient info if provided
        if target_patient_id:
            cur.execute("SELECT full_name, email FROM users WHERE id = %s", (target_patient_id,))
            pt = cur.fetchone()
            if pt:
                ctx["patient_data"]["full_name"] = pt[0]
                ctx["patient_data"]["email"] = pt[1]

            # Fetch patient profile details
            cur.execute(
                "SELECT date_of_birth, gender, blood_group, height_cm, weight_kg FROM patient_profiles WHERE user_id = %s",
                (target_patient_id,),
            )
            prof = cur.fetchone()
            if prof:
                ctx["patient_data"]["dob"] = str(prof[0]) if prof[0] else None
                ctx["patient_data"]["sex"] = prof[1] or "Unknown"
                ctx["patient_data"]["blood_group"] = prof[2]

            # Latest multi-disease assessment for this patient
            try:
                cur.execute(
                    "SELECT disease_module, risk_score, risk_level, feature_inputs, top_factors FROM multi_disease_assessments WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                    (target_patient_id,),
                )
                m = cur.fetchone()
                if m:
                    ctx["multi_disease_risk"] = {
                        "disease_module": m[0],
                        "risk_score": float(m[1]),
                        "risk_level": m[2],
                        "explanation": {"top_factors": json.loads(m[4]) if m[4] else []},
                    }
            except Exception:
                pass

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Notice: unable to load doctor context: {e}")

    return ctx


@router.post("/patient")
def consult_patient_agent(payload: PatientAgentRequest, current_user: dict = Depends(get_optional_user)):
    """Consult the Patient AI Health Assistant."""
    user_id = current_user.get("user_id") if current_user else 1
    db_context = _fetch_patient_context(user_id)

    # Merge client provided context overrides
    if payload.context:
        db_context.update(payload.context)

    result = patient_agent.consult(payload.message, db_context)
    return result


@router.get("/patient/quick-prompts")
def get_patient_quick_prompts():
    """Returns suggested quick prompt questions for patients."""
    return {"prompts": patient_agent.QUICK_PROMPTS}


@router.post("/doctor")
def consult_doctor_agent(payload: DoctorAgentRequest, current_user: dict = Depends(get_optional_user)):
    """Consult the Doctor AI Clinical Decision Co-Pilot."""
    doc_id = current_user.get("user_id") if current_user else 2
    db_context = _fetch_doctor_context(doc_id, payload.patient_id)

    # Merge client provided context overrides
    if payload.context:
        db_context.update(payload.context)

    result = doctor_agent.consult(payload.message, db_context)
    return result


@router.get("/doctor/quick-prompts")
def get_doctor_quick_prompts():
    """Returns suggested quick prompt queries for clinicians."""
    return {"prompts": doctor_agent.QUICK_PROMPTS}
