def check_safety_thresholds(metric_name: str, value: float) -> dict | None:
    m = metric_name.lower()
    if m in ("glucose", "blood_glucose"):
        if value >= 200:
            return {"metric": metric_name, "level": "critical", "message": f"Critical glucose reading: {value} mg/dL"}
        if value >= 140:
            return {"metric": metric_name, "level": "elevated", "message": f"Elevated glucose reading: {value} mg/dL"}
    elif m in ("systolic_bp", "blood_pressure", "trestbps"):
        if value >= 160:
            return {"metric": metric_name, "level": "critical", "message": f"Stage 2 Hypertensive reading: {value} mmHg"}
        if value >= 135:
            return {"metric": metric_name, "level": "elevated", "message": f"Pre-hypertensive reading: {value} mmHg"}
    elif m in ("cholesterol", "chol"):
        if value >= 240:
            return {"metric": metric_name, "level": "high", "message": f"High serum cholesterol: {value} mg/dL"}
    elif m in ("bmi",):
        if value >= 35:
            return {"metric": metric_name, "level": "obesity", "message": f"Severe obesity range: BMI {value}"}
    return None

def get_recommendation(disease_module: str, risk_level: str, inputs: dict) -> str:
    level = risk_level.lower()
    if disease_module == "diabetes":
        if level in ("high", "critical"):
            return "High risk of type 2 diabetes. Immediate fasting blood glucose & HbA1c testing recommended. Adopt low glycemic diet."
        if level == "moderate":
            return "Moderate diabetes risk detected. Monitor daily carbohydrate intake, engage in 150 min/wk aerobic exercise."
        return "Low statistical diabetes risk. Maintain balanced whole-food diet and routine annual checkups."
    elif disease_module == "heart_disease":
        if level in ("high", "critical"):
            return "High cardiovascular disease probability. Immediate 12-lead ECG and cardiology consultation advised. Limit sodium."
        if level == "moderate":
            return "Moderate cardiac risk. Schedule outpatient stress evaluation and monitor resting blood pressure daily."
        return "Low cardiovascular risk detected. Continue heart-healthy Mediterranean diet and physical activity."
    elif disease_module == "breast_cancer_screening":
        if level in ("high", "critical"):
            return "Elevated risk characteristics detected on biopsy cytology. Diagnostic imaging and surgical oncology review advised."
        return "Cytological characteristics within lower statistical risk range. Follow routine annual screening protocol."
    return "Maintain routine monitoring and follow up with a certified physician."
