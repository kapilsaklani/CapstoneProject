"""
Multi-Disease Risk Engine — inference layer.
Uniform interface for explainable multi-disease risk assessment.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

# Ensure sklearn compatibility for gradient boosting models
try:
    import sklearn._loss.loss
    sys.modules['_loss'] = sklearn._loss.loss
except Exception:
    pass

import joblib
import numpy as np

# Find trained_models directory
MODELS_DIR = Path(__file__).resolve().parent / "trained_models"
if not MODELS_DIR.exists():
    MODELS_DIR = Path(__file__).resolve().parent.parent / "trained_models"


class DiseaseModule:
    """Wraps one disease's model + scaler + metadata and does explainable scoring."""

    def __init__(self, name: str, model_file: str, scaler_file: str, meta_file: str):
        self.name = name
        self.model = joblib.load(MODELS_DIR / model_file)
        self.scaler = joblib.load(MODELS_DIR / scaler_file)
        with open(MODELS_DIR / meta_file, "r", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.feature_columns: List[str] = self.meta["feature_columns"]
        self.importances: Dict[str, float] = self.meta["feature_importances"]

    def _risk_level(self, prob: float) -> str:
        if prob < 0.25:
            return "low"
        if prob < 0.5:
            return "moderate"
        if prob < 0.75:
            return "high"
        return "critical"

    def assess(self, feature_values: Dict[str, float]) -> dict:
        x = np.array([[float(feature_values.get(col, 0.0)) for col in self.feature_columns]])
        x_scaled = self.scaler.transform(x)

        if hasattr(self.model, "predict_proba"):
            prob = float(self.model.predict_proba(x_scaled)[0][1])
        else:
            pred = self.model.predict(x_scaled)[0]
            prob = 1.0 if pred == 1 else 0.0

        risk_level = self._risk_level(prob)

        z_scores = x_scaled[0]
        contributions = []
        for i, col in enumerate(self.feature_columns):
            z = float(z_scores[i])
            weight = self.importances.get(col, 0.0)
            contribution_score = abs(z) * weight
            direction = "increases risk" if z > 0 else "decreases risk"
            inverse_features = {"thalach"}
            if col in inverse_features:
                direction = "decreases risk" if z > 0 else "increases risk"
            contributions.append(
                {
                    "feature": col,
                    "patient_value": float(feature_values.get(col, 0.0)),
                    "contribution_score": round(contribution_score, 4),
                    "direction": direction,
                }
            )
        contributions.sort(key=lambda c: -c["contribution_score"])
        top_factors = contributions[:5]
        requires_review = risk_level in ("high", "critical")

        return {
            "risk_score": round(prob, 4),
            "risk_level": risk_level,
            "explanation": {
                "top_factors": top_factors,
                "model_type": type(self.model).__name__,
                "disease_module": self.name,
            },
            "requires_clinician_review": requires_review,
        }


class MultiDiseaseRiskEngine:
    """Registry of all disease modules; the single entry point the API layer calls."""

    def __init__(self):
        self.modules: Dict[str, DiseaseModule] = {
            "diabetes": DiseaseModule(
                "diabetes", "diabetes_rf.joblib", "diabetes_scaler.joblib", "diabetes_meta.json"
            ),
            "heart_disease": DiseaseModule(
                "heart_disease", "heart_gb.joblib", "heart_scaler.joblib", "heart_meta.json"
            ),
            "breast_cancer_screening": DiseaseModule(
                "breast_cancer_screening",
                "breast_cancer_rf.joblib",
                "breast_cancer_scaler.joblib",
                "breast_cancer_meta.json",
            ),
        }

    def list_modules(self) -> List[str]:
        return list(self.modules.keys())

    def assess(self, disease: str, feature_values: Dict[str, float]) -> dict:
        if disease not in self.modules:
            raise ValueError(f"Unknown disease module: {disease}")
        return self.modules[disease].assess(feature_values)


risk_engine = MultiDiseaseRiskEngine()
