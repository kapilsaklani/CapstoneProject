import json
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from jose import jwt

from app.ml_engine import risk_engine
from app.database import get_database_connection
from app.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/assessments", tags=["Multi-Disease Risk Assessments"])


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


class AssessmentRequest(BaseModel):
    disease_module: str = Field(..., description="diabetes, heart_disease, or breast_cancer_screening")
    features: Dict[str, float]


def _check_safety_rules(disease: str, features: Dict[str, float]) -> list:
    alerts = []
    # Blood Glucose checks
    glucose = features.get("Glucose") or features.get("glucose")
    if glucose is not None:
        if glucose >= 200:
            alerts.append({"metric": "Glucose", "level": "Critical", "message": f"Critical Hyperglycemia detected ({glucose} mg/dL). Immediate medical evaluation advised."})
        elif glucose >= 140:
            alerts.append({"metric": "Glucose", "level": "Elevated", "message": f"Elevated blood glucose detected ({glucose} mg/dL). Fasting verification recommended."})

    # Blood Pressure checks
    bp = features.get("BloodPressure") or features.get("trestbps")
    if bp is not None:
        if bp >= 160:
            alerts.append({"metric": "Blood Pressure", "level": "Stage 2 Hypertension", "message": f"Resting systolic/diastolic blood pressure significantly elevated ({bp} mmHg)."})
        elif bp >= 135:
            alerts.append({"metric": "Blood Pressure", "level": "Pre-Hypertension", "message": f"Elevated blood pressure observed ({bp} mmHg). Routine monitoring recommended."})

    # Cholesterol checks
    chol = features.get("chol") or features.get("cholesterol")
    if chol is not None:
        if chol >= 240:
            alerts.append({"metric": "Cholesterol", "level": "High", "message": f"Serum cholesterol is high ({chol} mg/dL). Full lipid panel indicated."})

    # ST depression / ECG
    oldpeak = features.get("oldpeak")
    if oldpeak is not None and oldpeak >= 2.0:
        alerts.append({"metric": "ST Depression", "level": "High Warning", "message": f"Exertional ST depression ({oldpeak} mm) suggests significant myocardial ischemia."})

    return alerts


def _save_assessment_record(user_id: Optional[int], disease: str, result: dict, features: dict):
    try:
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS multi_disease_assessments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                disease_module VARCHAR(50) NOT NULL,
                risk_score NUMERIC(6, 4) NOT NULL,
                risk_level VARCHAR(30) NOT NULL,
                feature_inputs TEXT,
                top_factors TEXT,
                requires_clinician_review BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            """
            INSERT INTO multi_disease_assessments
            (user_id, disease_module, risk_score, risk_level, feature_inputs, top_factors, requires_clinician_review)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id or 1,
                disease,
                result["risk_score"],
                result["risk_level"],
                json.dumps(features),
                json.dumps(result["explanation"]["top_factors"]),
                result["requires_clinician_review"],
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: could not persist assessment: {e}")


@router.get("/modules")
def list_modules():
    """Lists registered disease prediction modules."""
    return {
        "modules": risk_engine.list_modules(),
        "details": [
            {
                "id": "diabetes",
                "name": "Type 2 Diabetes Risk Assessment",
                "icon": "FaChartLine",
                "description": "Evaluates insulin resistance, fasting glucose, BMI, and genetic risk factors using Random Forest.",
            },
            {
                "id": "heart_disease",
                "name": "Coronary Heart Disease Risk Assessment",
                "icon": "FaHeartbeat",
                "description": "Analyzes clinical cardiovascular vitals, exercise-induced ST depression, and fluoroscopy using Gradient Boosting.",
            },
            {
                "id": "breast_cancer_screening",
                "name": "Breast Cancer Biopsy Screening Risk",
                "icon": "FaShieldAlt",
                "description": "Predicts cell nucleus malignancy probabilities from fine-needle aspirate (FNA) morphological features.",
            },
        ],
    }


@router.get("/info/{disease_module}")
def get_module_info(disease_module: str):
    """Returns feature specifications and normal clinical reference ranges for a module."""
    try:
        return risk_engine.get_module_info(disease_module)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/evaluate")
def evaluate_risk(payload: AssessmentRequest, current_user: dict = Depends(get_optional_user)):
    """Runs explainable ML inference on the selected disease module."""
    try:
        result = risk_engine.assess(payload.disease_module, payload.features)
        safety_alerts = _check_safety_rules(payload.disease_module, payload.features)
        result["safety_alerts"] = safety_alerts

        user_id = current_user.get("user_id") if current_user else 1
        _save_assessment_record(user_id, payload.disease_module, result, payload.features)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@router.post("/diabetes")
def assess_diabetes_endpoint(features: Dict[str, float], current_user: dict = Depends(get_optional_user)):
    return evaluate_risk(AssessmentRequest(disease_module="diabetes", features=features), current_user)


@router.post("/heart-disease")
def assess_heart_endpoint(features: Dict[str, float], current_user: dict = Depends(get_optional_user)):
    return evaluate_risk(AssessmentRequest(disease_module="heart_disease", features=features), current_user)


@router.post("/breast-cancer-screening")
def assess_breast_cancer_endpoint(features: Dict[str, float], current_user: dict = Depends(get_optional_user)):
    return evaluate_risk(AssessmentRequest(disease_module="breast_cancer_screening", features=features), current_user)


@router.get("/history")
def get_assessment_history(current_user: dict = Depends(get_optional_user)):
    """Fetches past multi-disease assessments."""
    user_id = current_user.get("user_id") if current_user else 1
    try:
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, disease_module, risk_score, risk_level, feature_inputs, top_factors, requires_clinician_review, created_at
            FROM multi_disease_assessments
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        history = []
        for r in rows:
            history.append(
                {
                    "id": r[0],
                    "disease_module": r[1],
                    "risk_score": float(r[2]),
                    "risk_percentage": round(float(r[2]) * 100, 1),
                    "risk_level": r[3],
                    "features": json.loads(r[4]) if r[4] else {},
                    "top_factors": json.loads(r[5]) if r[5] else [],
                    "requires_clinician_review": bool(r[6]),
                    "created_at": str(r[7]),
                }
            )
        return {"assessments": history}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"assessments": []}
