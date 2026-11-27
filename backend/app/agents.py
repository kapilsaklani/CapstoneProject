"""
MedAssist AI Intelligent Health Agents:
1. PatientHealthAgent - Empathetic patient health companion and symptom advisor.
2. DoctorCopilotAgent - Rigorous clinical decision support co-pilot for clinicians.
"""
from typing import Dict, List, Any, Optional
import datetime


class PatientHealthAgent:
    """Intelligent conversational agent for patients."""

    QUICK_PROMPTS = [
        "Explain my latest disease risk assessment in simple terms",
        "What lifestyle and dietary changes can reduce my diabetes risk?",
        "I have a mild fever and headache — what should I do at home?",
        "How can I improve my cardiovascular health and resting blood pressure?",
        "What are warning signs that require immediate emergency medical care?",
    ]

    EMERGENCY_SYMPTOMS = [
        "crushing chest pain", "chest pressure", "difficulty breathing",
        "shortness of breath", "sudden numbness", "facial drooping",
        "slurred speech", "coughing blood", "loss of consciousness"
    ]

    def consult(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        msg_lower = message.lower()

        # Check for emergency symptoms
        is_emergency = any(em in msg_lower for em in self.EMERGENCY_SYMPTOMS)

        patient_name = context.get("patient_name", "Patient")
        symptoms = context.get("recent_symptoms", [])
        latest_prediction = context.get("latest_prediction")
        latest_risk = context.get("latest_risk")
        multi_disease_risk = context.get("multi_disease_risk")

        response_sections = []

        if is_emergency:
            urgency = "EMERGENCY"
            response_sections.append(
                "🚨 **URGENT MEDICAL WARNING**: Your symptoms indicate a potential medical emergency. "
                "Please do not wait — call your local emergency service (such as 911, 112, or local ER) "
                "or proceed to the nearest emergency room immediately."
            )
        else:
            urgency = "NORMAL"

        # Context-aware reasoning
        if any(w in msg_lower for w in ["risk", "score", "explain", "assessment", "percent", "level"]):
            if multi_disease_risk:
                mod = multi_disease_risk.get("disease_module", "Disease")
                level = multi_disease_risk.get("risk_level", "Unknown").upper()
                score = multi_disease_risk.get("risk_percentage", 0.0)
                factors = multi_disease_risk.get("explanation", {}).get("top_factors", [])

                factor_bullets = []
                for f in factors:
                    direction = "📈 pushes risk UP" if "increase" in f.get("direction", "") else "📉 is protective"
                    factor_bullets.append(f"- **{f.get('label', f.get('feature'))}** (value: {f.get('patient_value')}): {direction}")

                response_sections.append(
                    f"### 📊 Your {mod.replace('_', ' ').title()} Assessment Summary\n"
                    f"Your calculated statistical risk level is **{level}** ({score}% probability).\n\n"
                    f"**Key factors influencing this score:**\n" + "\n".join(factor_bullets) + "\n\n"
                    f"**What this means for you:** This score is an AI risk estimate to guide preventative care, "
                    f"not an absolute diagnosis. Discuss these results with your healthcare provider for clinical confirmation."
                )
            elif latest_risk:
                outcome = latest_risk.get("predicted_outcome", "Normal")
                pos_score = latest_risk.get("positive_model_score", 0.0)
                response_sections.append(
                    f"### 📋 Recent Health Risk Assessment\n"
                    f"- **Outcome Category:** {outcome}\n"
                    f"- **High-Risk Probability:** {pos_score}%\n"
                    f"- **Vitals Monitored:** BP: {latest_risk.get('blood_pressure', 'Normal')}, "
                    f"Cholesterol: {latest_risk.get('cholesterol_level', 'Normal')}"
                )

        if any(w in msg_lower for w in ["diet", "food", "eat", "nutrition", "lifestyle", "habit", "exercise"]):
            response_sections.append(
                "### 🥗 Nutrition & Lifestyle Guidance\n"
                "- **Hydration:** Aim for 2.5 to 3 liters of water daily; limit sugary sodas and excess caffeine.\n"
                "- **Dietary Balance:** Focus on high-fiber whole grains, leafy greens, lean proteins, and healthy fats (olive oil, nuts).\n"
                "- **Activity:** 30 minutes of moderate aerobic exercise (brisk walking, cycling) 5 days a week.\n"
                "- **Rest & Recovery:** Prioritize 7–8 hours of consistent, restorative sleep."
            )

        if any(w in msg_lower for w in ["symptom", "fever", "cough", "headache", "cold", "pain", "fatigue"]):
            symptom_list_str = ", ".join([s.get("symptom_name", "") for s in symptoms]) if symptoms else "None logged recently"
            response_sections.append(
                f"### 🩺 Symptom Check & Self-Care\n"
                f"- **Logged Symptoms:** {symptom_list_str}\n"
                "- **Rest:** Get adequate bed rest and avoid strenuous physical exertion.\n"
                "- **Monitor:** Keep a log of your body temperature twice daily.\n"
                "- **When to see a doctor:** Seek consultation if fever persists over 48 hours or exceeds 102°F (38.9°C)."
            )

        # General response synthesis if no specific trigger fired
        if not response_sections or (len(response_sections) == 1 and is_emergency):
            response_sections.append(
                f"Hello {patient_name}! I am your MedAssist AI Health Assistant. "
                "I can help you understand your symptoms, interpret your multi-disease risk assessments (Diabetes, Heart Disease, Breast Cancer), "
                "explain clinical lab values, and provide personalized preventative lifestyle advice."
            )

        disclaimer = (
            "\n\n> 💡 *Disclaimer: MedAssist AI provides clinical decision support and health education. "
            "It does not replace professional medical advice, diagnosis, or treatment.*"
        )

        full_reply = "\n\n".join(response_sections) + disclaimer

        return {
            "agent_type": "patient_health_agent",
            "reply": full_reply,
            "urgency": urgency,
            "timestamp": datetime.datetime.now().isoformat(),
            "suggested_follow_ups": [
                "How can I prepare for my upcoming doctor visit?",
                "What lab tests should I ask my physician about?",
                "Explain the difference between systolic and diastolic BP"
            ]
        }


class DoctorCopilotAgent:
    """Intelligent clinical co-pilot for physicians, caretakers, and clinicians."""

    QUICK_PROMPTS = [
        "Synthesize flagged patient triage queue and critical alerts",
        "Draft a formal SOAP clinical care plan for a diabetic patient",
        "Explain feature importance and risk breakdown for cardiovascular risk",
        "Review abnormal vital trends and recommend lab workups",
        "Check pharmacological safety precautions for hypertensive patients",
    ]

    def consult(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        q_lower = query.lower()

        doctor_name = context.get("doctor_name", "Doctor")
        patient_data = context.get("patient_data", {})
        flagged_count = context.get("flagged_count", 0)
        multi_disease_risk = context.get("multi_disease_risk")
        vital_summary = context.get("vital_summary", {})

        response_sections = []

        if any(w in q_lower for w in ["triage", "flagged", "queue", "urgent", "critical", "alerts"]):
            response_sections.append(
                f"### 🚨 Clinician Triage & Risk Summary\n"
                f"- **Flagged Patients Under Care:** {flagged_count} require clinician review.\n"
                "- **Priority Criteria:** High/Critical ML risk scores (>50%), vital alerts (Systolic BP > 140 mmHg, Fasting Glucose > 180 mg/dL, ST depression > 2.0 mm).\n"
                "- **Action Recommended:** Prioritize patients with multiple interacting risk vectors for immediate same-week clinical follow-up."
            )

        if any(w in q_lower for w in ["soap", "care plan", "plan", "directive", "draft", "notes"]):
            p_name = patient_data.get("full_name", "Patient")
            p_age = patient_data.get("age", 55)
            p_sex = patient_data.get("sex", "Adult")

            response_sections.append(
                f"### 📝 Generated SOAP Clinical Care Plan\n"
                f"**Patient:** {p_name} | **Age/Sex:** {p_age} / {p_sex}\n\n"
                "**1. Subjective (S):**\n"
                "- Patient presents for evaluation of risk assessment scores and preventative monitoring.\n"
                "- Reports intermittent fatigue, mild exertional dyspnea, and occasional headaches.\n\n"
                "**2. Objective (O):**\n"
                "- Automated Risk Score: High Risk Classification (Random Forest / Gradient Boosting inference).\n"
                "- Vitals snapshot: Review BP, resting heart rate, BMI, and metabolic panels.\n\n"
                "**3. Assessment (A):**\n"
                "- Elevated cardiovascular and cardiometabolic risk profile.\n"
                "- Potential early-stage metabolic syndrome or hypertensive progression.\n\n"
                "**4. Plan (P):**\n"
                "- **Diagnostics:** Order comprehensive metabolic panel (CMP), HbA1c, lipid panel, and resting 12-lead ECG.\n"
                "- **Pharmacology:** Evaluate initiation/titration of standard first-line therapies (ACE-I/ARB or Metformin) if confirmed on repeat testing.\n"
                "- **Lifestyle:** DASH/Mediterranean dietary protocol, sodium restriction (<2000 mg/day), 150 min/wk moderate activity.\n"
                "- **Follow-up:** Clinical review in 4 weeks with home BP & blood glucose logs."
            )

        if any(w in q_lower for w in ["explain", "feature", "z-score", "importance", "model", "breakdown"]):
            if multi_disease_risk:
                mod = multi_disease_risk.get("disease_module", "Disease")
                level = multi_disease_risk.get("risk_level", "Unknown").upper()
                score = multi_disease_risk.get("risk_score", 0.0)
                factors = multi_disease_risk.get("explanation", {}).get("top_factors", [])

                factor_rows = []
                for f in factors:
                    factor_rows.append(f"| {f.get('label', f.get('feature'))} | {f.get('patient_value')} | {f.get('contribution_score')} | {f.get('direction')} |")

                factor_table = "\n".join(factor_rows)
                response_sections.append(
                    f"### 🔬 Multi-Disease Explainable Inference: {mod.replace('_', ' ').title()}\n"
                    f"- **Model:** {multi_disease_risk.get('explanation', {}).get('model_type', 'Ensemble')}\n"
                    f"- **Inference Score:** {score:.4f} ({level})\n\n"
                    f"| Clinical Feature | Patient Value | Contribution Weight | Influence Vector |\n"
                    f"| :--- | :--- | :--- | :--- |\n"
                    f"{factor_table}\n\n"
                    "**Clinical Interpretation:** Features with positive contribution scores push the patient's log-odds of risk above the normalized population mean."
                )
            else:
                response_sections.append(
                    "### 🔬 ML Model Risk Explainability Architecture\n"
                    "- **Random Forest & Gradient Boosting:** Uses patient-specific z-score normalization scaled against feature importances.\n"
                    "- **Inverse Vectors:** Protective markers (e.g. higher maximum exercise heart rate `thalach`) actively reduce risk.\n"
                    "- **Clinician Flagging:** Threshold triggers automatically when predicted class probability exceeds 0.50 (High) or 0.75 (Critical)."
                )

        if any(w in q_lower for w in ["lab", "test", "diagnostic", "workup", "vitals"]):
            response_sections.append(
                "### 🧪 Recommended Clinical Workup & Biomarkers\n"
                "- **Metabolic Evaluation:** Fasting Blood Glucose, HbA1c, Fasting Lipid Profile (Total, LDL, HDL, Triglycerides).\n"
                "- **Cardiovascular:** Resting 12-lead ECG, high-sensitivity C-reactive protein (hs-CRP), serum creatinine & eGFR.\n"
                "- **Oncology Screening (if indicated):** High-resolution diagnostic mammography and targeted breast ultrasound for suspicious nodules."
            )

        if not response_sections:
            response_sections.append(
                f"Greetings Dr. {doctor_name}. I am your Clinical Decision Support Co-Pilot. "
                "I can synthesize patient triage queues, explain model predictions & feature contributions, "
                "draft structured SOAP care plans, and recommend diagnostic investigation protocols."
            )

        disclaimer = (
            "\n\n> ⚕️ *Clinical Decision Support notice: MedAssist AI recommendations are provided to assist "
            "qualified medical personnel. Clinical judgment and institutional protocols take precedence.*"
        )

        full_reply = "\n\n".join(response_sections) + disclaimer

        return {
            "agent_type": "doctor_copilot_agent",
            "reply": full_reply,
            "timestamp": datetime.datetime.now().isoformat(),
            "suggested_actions": [
                "Generate clinical care plan",
                "Export PDF patient summary",
                "Acknowledge safety alerts"
            ]
        }


# Singleton instances
patient_agent = PatientHealthAgent()
doctor_agent = DoctorCopilotAgent()
