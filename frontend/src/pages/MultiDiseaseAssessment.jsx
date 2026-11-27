import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
    FaHeartbeat,
    FaChartLine,
    FaShieldAlt,
    FaRobot,
    FaExclamationCircle,
    FaCheckCircle,
    FaHistory,
    FaInfoCircle,
    FaArrowUp,
    FaArrowDown,
} from "react-icons/fa";
import {
    getAssessmentModules,
    getModuleInfo,
    evaluateRisk,
    getAssessmentHistory,
} from "../services/agentService";
import { useToast } from "../context/ToastContext";
import "../styles/MultiDisease.css";

const DEFAULT_INPUTS = {
    diabetes: {
        Pregnancies: 2,
        Glucose: 135,
        BloodPressure: 78,
        SkinThickness: 28,
        Insulin: 85,
        BMI: 29.4,
        DiabetesPedigreeFunction: 0.45,
        Age: 45,
    },
    heart_disease: {
        age: 56,
        sex: 1, // 1=Male, 0=Female
        cp: 2, // Chest pain type (0-3)
        trestbps: 140, // Resting BP mm Hg
        chol: 245, // Serum cholesterol mg/dL
        fbs: 0, // Fasting blood sugar > 120
        restecg: 1, // Resting ECG
        thalach: 142, // Max heart rate
        exang: 1, // Exercise-induced angina (1=yes)
        oldpeak: 1.8, // ST depression
        slope: 1, // Slope of peak exercise
        ca: 1, // Major vessels (0-3)
        thal: 2, // Thalassemia
    },
    breast_cancer_screening: {
        "mean radius": 14.5,
        "mean texture": 19.2,
        "mean perimeter": 95.3,
        "mean area": 650.0,
        "mean smoothness": 0.096,
        "mean compactness": 0.104,
        "mean concavity": 0.088,
        "mean concave points": 0.048,
        "mean symmetry": 0.181,
        "mean fractal dimension": 0.062,
    },
};

function MultiDiseaseAssessment() {
    const navigate = useNavigate();
    const { showToast } = useToast();

    const [activeTab, setActiveTab] = useState("diabetes");
    const [inputs, setInputs] = useState(DEFAULT_INPUTS);
    const [evaluating, setEvaluating] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            setLoadingHistory(true);
            const data = await getAssessmentHistory();
            setHistory(data.assessments || []);
        } catch (error) {
            console.error("Failed to load assessment history:", error);
        } finally {
            setLoadingHistory(false);
        }
    };

    const handleInputChange = (field, val) => {
        const numVal = parseFloat(val) || 0;
        setInputs((prev) => ({
            ...prev,
            [activeTab]: {
                ...prev[activeTab],
                [field]: numVal,
            },
        }));
    };

    const handleEvaluate = async () => {
        setEvaluating(true);
        setResult(null);
        try {
            const currentFeatures = inputs[activeTab];
            const data = await evaluateRisk(activeTab, currentFeatures);
            setResult(data);
            showToast("Multi-disease assessment calculated successfully!", "success");
            loadHistory();
        } catch (error) {
            console.error("Assessment evaluation error:", error);
            showToast("Failed to run ML model. Check input values.", "error");
        } finally {
            setEvaluating(false);
        }
    };

    const handleDiscussWithAgent = () => {
        if (!result) return;
        const msg = `Please explain my ${result.disease_module.replace("_", " ")} risk assessment (${result.risk_percentage}% - ${result.risk_level.toUpperCase()}) and suggest actionable health steps.`;
        navigate("/patient/ai-agent", {
            state: {
                role: "patient",
                prefillMessage: msg,
                context: {
                    multi_disease_risk: result,
                },
            },
        });
    };

    const getRiskColor = (level) => {
        switch (level) {
            case "low":
                return "#10b981"; // green
            case "moderate":
                return "#f59e0b"; // yellow/orange
            case "high":
                return "#f97316"; // orange
            case "critical":
                return "#ef4444"; // red
            default:
                return "#38bdf8";
        }
    };

    return (
        <div className="multi-disease-page">
            <div className="multi-disease-hero">
                <div className="hero-text-content">
                    <h2>
                        <FaHeartbeat /> Multi-Disease AI Risk Engine
                    </h2>
                    <p>
                        Screen clinical risk factors and receive explainable machine learning predictions for Type 2
                        Diabetes, Cardiovascular Heart Disease, and Oncology Biopsy screening.
                    </p>
                </div>

                <button
                    className="hero-agent-btn"
                    onClick={() => navigate("/patient/ai-agent")}
                >
                    <FaRobot />
                    <span>Consult AI Health Assistant</span>
                </button>
            </div>

            {/* Disease Navigation Tabs */}
            <div className="disease-tabs">
                <button
                    className={`disease-tab-btn ${activeTab === "diabetes" ? "active" : ""}`}
                    onClick={() => {
                        setActiveTab("diabetes");
                        setResult(null);
                    }}
                >
                    <FaChartLine />
                    <span>Type 2 Diabetes (RF)</span>
                </button>

                <button
                    className={`disease-tab-btn ${activeTab === "heart_disease" ? "active" : ""}`}
                    onClick={() => {
                        setActiveTab("heart_disease");
                        setResult(null);
                    }}
                >
                    <FaHeartbeat />
                    <span>Cardiovascular Heart Risk (GB)</span>
                </button>

                <button
                    className={`disease-tab-btn ${activeTab === "breast_cancer_screening" ? "active" : ""}`}
                    onClick={() => {
                        setActiveTab("breast_cancer_screening");
                        setResult(null);
                    }}
                >
                    <FaShieldAlt />
                    <span>Breast Cancer Biopsy (RF)</span>
                </button>
            </div>

            {/* Main Interactive Grid */}
            <div className="assessment-grid">
                {/* Inputs Form */}
                <div className="form-card-container">
                    <div className="form-card-header">
                        <h3>Clinical Parameters & Vitals</h3>
                        <span className="info-tag">
                            <FaInfoCircle /> Pre-filled with standard physiological baseline
                        </span>
                    </div>

                    <div className="fields-grid">
                        {Object.entries(inputs[activeTab]).map(([key, val]) => (
                            <div key={key} className="field-group">
                                <label>{key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</label>
                                <input
                                    type="number"
                                    step="any"
                                    value={val}
                                    onChange={(e) => handleInputChange(key, e.target.value)}
                                />
                            </div>
                        ))}
                    </div>

                    <button
                        className="evaluate-btn"
                        onClick={handleEvaluate}
                        disabled={evaluating}
                    >
                        {evaluating ? "Evaluating ML Model..." : "Calculate Risk Assessment"}
                    </button>
                </div>

                {/* Results Card */}
                <div className="results-card-container">
                    <div className="results-card-header">
                        <h3>Assessment Results & Explainability</h3>
                    </div>

                    {result ? (
                        <div className="results-body">
                            {/* Score & Gauge */}
                            <div className="score-summary-box">
                                <div
                                    className="score-circle"
                                    style={{
                                        borderColor: getRiskColor(result.risk_level),
                                    }}
                                >
                                    <span className="score-val">{result.risk_percentage}%</span>
                                    <span className="score-lbl">Risk Score</span>
                                </div>

                                <div className="score-meta">
                                    <span
                                        className="risk-badge"
                                        style={{
                                            backgroundColor: `${getRiskColor(result.risk_level)}20`,
                                            borderColor: getRiskColor(result.risk_level),
                                            color: getRiskColor(result.risk_level),
                                        }}
                                    >
                                        {result.risk_level.toUpperCase()} RISK
                                    </span>
                                    <p className="model-info-text">
                                        Model: <strong>{result.explanation.model_type}</strong>
                                    </p>
                                    {result.requires_clinician_review && (
                                        <div className="clinician-flag-alert">
                                            <FaExclamationCircle />
                                            <span>Clinician review recommended for this score.</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Safety Threshold Alerts */}
                            {result.safety_alerts && result.safety_alerts.length > 0 && (
                                <div className="safety-alerts-box">
                                    <h4>Rule-Based Vitals Alerts</h4>
                                    {result.safety_alerts.map((al, idx) => (
                                        <div key={idx} className="alert-item">
                                            <strong>{al.metric} ({al.level}):</strong> {al.message}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Top Contributing Factors */}
                            <div className="factors-box">
                                <h4>Top Contributing Factors (Explainable AI)</h4>
                                <div className="factors-list">
                                    {result.explanation.top_factors.map((f, idx) => {
                                        const isIncrease = f.direction.includes("increase");
                                        return (
                                            <div key={idx} className={`factor-row ${isIncrease ? "increase" : "decrease"}`}>
                                                <div className="factor-info">
                                                    <span className="factor-name">{f.label || f.feature}</span>
                                                    <span className="factor-val">Value: {f.patient_value}</span>
                                                </div>
                                                <div className="factor-influence">
                                                    {isIncrease ? (
                                                        <span className="influence-tag up">
                                                            <FaArrowUp /> Pushes Risk Up (+{f.contribution_score})
                                                        </span>
                                                    ) : (
                                                        <span className="influence-tag down">
                                                            <FaArrowDown /> Protective Effect
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Action to AI Agent */}
                            <button
                                className="discuss-agent-btn"
                                onClick={handleDiscussWithAgent}
                            >
                                <FaRobot />
                                <span>Discuss Result with AI Health Assistant</span>
                            </button>
                        </div>
                    ) : (
                        <div className="empty-results-state">
                            <FaShieldAlt className="empty-shield-icon" />
                            <p>Enter your clinical parameters and click "Calculate Risk Assessment" to view the explainability report.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Assessment History */}
            <div className="history-section-container">
                <div className="history-header">
                    <h3>
                        <FaHistory /> Recent Assessment History
                    </h3>
                </div>

                {loadingHistory ? (
                    <p className="loading-text">Loading history...</p>
                ) : history.length === 0 ? (
                    <p className="empty-history-text">No previous multi-disease assessments recorded yet.</p>
                ) : (
                    <div className="history-cards-scroll">
                        {history.map((item) => (
                            <div key={item.id} className="history-item-card">
                                <div className="hist-top">
                                    <span className="hist-disease">
                                        {item.disease_module.replace("_", " ").toUpperCase()}
                                    </span>
                                    <span
                                        className="hist-risk-badge"
                                        style={{
                                            color: getRiskColor(item.risk_level),
                                            borderColor: getRiskColor(item.risk_level),
                                        }}
                                    >
                                        {item.risk_level.toUpperCase()} ({item.risk_percentage}%)
                                    </span>
                                </div>
                                <div className="hist-date">{new Date(item.created_at).toLocaleDateString()}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default MultiDiseaseAssessment;
