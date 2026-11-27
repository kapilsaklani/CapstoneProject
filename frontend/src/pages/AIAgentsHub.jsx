import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import {
    FaRobot,
    FaUserMd,
    FaUser,
    FaPaperPlane,
    FaMagic,
    FaExclamationTriangle,
    FaHeartbeat,
    FaShieldAlt,
    FaTrashAlt,
    FaFileMedicalAlt,
    FaCheckCircle,
} from "react-icons/fa";
import {
    consultPatientAgent,
    consultDoctorAgent,
    getPatientQuickPrompts,
    getDoctorQuickPrompts,
} from "../services/agentService";
import { useToast } from "../context/ToastContext";
import "../styles/AIAgents.css";

function AIAgentsHub({ initialRole = "patient" }) {
    const location = useLocation();
    const { showToast } = useToast();

    // Determine role from route or state
    const isCaretakerRoute = location.pathname.includes("caretaker");
    const [activeRole, setActiveRole] = useState(
        isCaretakerRoute ? "doctor" : location.state?.role || initialRole
    );

    const [messages, setMessages] = useState([]);
    const [inputPrompt, setInputPrompt] = useState("");
    const [quickPrompts, setQuickPrompts] = useState([]);
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // Initial greeting based on role
    useEffect(() => {
        const greeting =
            activeRole === "patient"
                ? {
                      sender: "agent",
                      text: "👋 **Hello! I am your MedAssist Patient AI Health Assistant.**\n\nI can help you understand your symptoms, explain your multi-disease risk assessment scores (Diabetes, Heart Disease, and Breast Cancer), provide dietary and lifestyle recommendations, and alert you if symptoms require emergency medical care. How can I support your health journey today?",
                      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                      urgency: "NORMAL",
                  }
                : {
                      sender: "agent",
                      text: "⚕️ **Greetings Doctor. I am your Clinical Decision Support Co-Pilot.**\n\nI can synthesize patient triage queues, explain model predictions & feature z-score importances, draft structured SOAP clinical care plans, and review abnormal vital parameters. What clinical inquiry would you like to review?",
                      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                      urgency: "CLINICAL",
                  };

        // If pre-filled query was passed via location.state (e.g. from MultiDiseaseAssessment)
        if (location.state?.prefillMessage) {
            setMessages([
                greeting,
                {
                    sender: "user",
                    text: location.state.prefillMessage,
                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                },
            ]);
            // Automatically trigger consultation
            handleSend(location.state.prefillMessage, location.state.context);
        } else {
            setMessages([greeting]);
        }

        loadQuickPrompts(activeRole);
    }, [activeRole]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const loadQuickPrompts = async (role) => {
        try {
            if (role === "patient") {
                const data = await getPatientQuickPrompts();
                setQuickPrompts(data.prompts || []);
            } else {
                const data = await getDoctorQuickPrompts();
                setQuickPrompts(data.prompts || []);
            }
        } catch (error) {
            console.error("Failed to load quick prompts:", error);
        }
    };

    const handleSend = async (textToSend, customContext = null) => {
        const msgText = textToSend || inputPrompt.trim();
        if (!msgText) return;

        const userMsg = {
            sender: "user",
            text: msgText,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInputPrompt("");
        setLoading(true);

        try {
            let res;
            if (activeRole === "patient") {
                res = await consultPatientAgent(msgText, customContext);
            } else {
                res = await consultDoctorAgent(msgText, null, customContext);
            }

            const agentMsg = {
                sender: "agent",
                text: res.reply,
                urgency: res.urgency || "NORMAL",
                timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                suggested_follow_ups: res.suggested_follow_ups || res.suggested_actions || [],
            };

            setMessages((prev) => [...prev, agentMsg]);
        } catch (error) {
            console.error("Agent consultation failed:", error);
            showToast("Failed to connect with the AI agent. Please try again.", "error");
            setMessages((prev) => [
                ...prev,
                {
                    sender: "agent",
                    text: "⚠️ **Connection Error**: Unable to reach the AI engine right now. Please ensure the backend server is running and try again.",
                    timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    urgency: "ERROR",
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleClearChat = () => {
        setMessages([]);
        setActiveRole((prev) => prev); // re-trigger greeting
    };

    return (
        <div className="ai-agents-container">
            {/* Header & Role Switcher */}
            <div className="ai-agents-header">
                <div className="ai-agents-title-group">
                    <div className="agent-badge-icon">
                        {activeRole === "patient" ? <FaRobot /> : <FaUserMd />}
                    </div>
                    <div>
                        <h2>
                            {activeRole === "patient"
                                ? "Patient AI Health Assistant"
                                : "Doctor Clinical Co-Pilot AI"}
                        </h2>
                        <p className="agent-subtitle">
                            {activeRole === "patient"
                                ? "Empathetic, 24/7 symptom guidance, risk explanations, and personalized wellness advice"
                                : "Evidence-based decision support, triage synthesis, and clinical SOAP care plan generator"}
                        </p>
                    </div>
                </div>

                {/* Role Toggle Switcher */}
                <div className="role-switch-container">
                    <button
                        className={`role-btn ${activeRole === "patient" ? "active patient" : ""}`}
                        onClick={() => setActiveRole("patient")}
                    >
                        <FaUser />
                        <span>Patient Assistant</span>
                    </button>
                    <button
                        className={`role-btn ${activeRole === "doctor" ? "active doctor" : ""}`}
                        onClick={() => setActiveRole("doctor")}
                    >
                        <FaUserMd />
                        <span>Doctor Co-Pilot</span>
                    </button>
                </div>
            </div>

            {/* Main Interactive Layout */}
            <div className="ai-agents-body">
                {/* Chat Section */}
                <div className="ai-chat-card">
                    {/* Top Action Bar */}
                    <div className="chat-action-bar">
                        <span className="live-pill">
                            <span className="pulse-dot"></span>
                            AI Agent Active ({activeRole === "patient" ? "Patient Mode" : "Clinician Mode"})
                        </span>

                        <button className="clear-btn" onClick={handleClearChat} title="Clear conversation">
                            <FaTrashAlt />
                            <span>Reset Chat</span>
                        </button>
                    </div>

                    {/* Messages Thread */}
                    <div className="chat-messages-scroll">
                        {messages.map((m, idx) => (
                            <div key={idx} className={`chat-bubble-row ${m.sender}`}>
                                <div className="avatar-col">
                                    {m.sender === "user" ? (
                                        <div className="user-avatar">
                                            <FaUser />
                                        </div>
                                    ) : (
                                        <div className={`agent-avatar ${activeRole}`}>
                                            {activeRole === "patient" ? <FaRobot /> : <FaUserMd />}
                                        </div>
                                    )}
                                </div>
                                <div className="bubble-content-col">
                                    <div className="bubble-meta">
                                        <span className="sender-name">
                                            {m.sender === "user"
                                                ? "You"
                                                : activeRole === "patient"
                                                ? "MedAssist Health AI"
                                                : "Clinical Decision Co-Pilot"}
                                        </span>
                                        <span className="msg-time">{m.timestamp}</span>
                                        {m.urgency === "EMERGENCY" && (
                                            <span className="urgency-badge emergency">
                                                <FaExclamationTriangle /> Urgent Emergency
                                            </span>
                                        )}
                                        {m.urgency === "CLINICAL" && (
                                            <span className="urgency-badge clinical">
                                                <FaShieldAlt /> Decision Support
                                            </span>
                                        )}
                                    </div>
                                    <div className="bubble-text">
                                        {/* Simple markdown formatting */}
                                        {m.text.split("\n\n").map((paragraph, pIdx) => {
                                            if (paragraph.startsWith("### ")) {
                                                return <h4 key={pIdx}>{paragraph.replace("### ", "")}</h4>;
                                            }
                                            if (paragraph.startsWith("> ")) {
                                                return (
                                                    <blockquote key={pIdx}>
                                                        {paragraph.replace("> ", "")}
                                                    </blockquote>
                                                );
                                            }
                                            if (paragraph.startsWith("- ")) {
                                                const items = paragraph.split("\n- ");
                                                return (
                                                    <ul key={pIdx}>
                                                        {items.map((it, iIdx) => (
                                                            <li key={iIdx}>
                                                                {it.replace("- ", "").split("**").map((chunk, cIdx) =>
                                                                    cIdx % 2 === 1 ? <strong key={cIdx}>{chunk}</strong> : chunk
                                                                )}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                );
                                            }
                                            return (
                                                <p key={pIdx}>
                                                    {paragraph.split("**").map((chunk, cIdx) =>
                                                        cIdx % 2 === 1 ? <strong key={cIdx}>{chunk}</strong> : chunk
                                                    )}
                                                </p>
                                            );
                                        })}
                                    </div>

                                    {/* Follow up suggestions if any */}
                                    {m.suggested_follow_ups && m.suggested_follow_ups.length > 0 && (
                                        <div className="suggested-chips-container">
                                            <span className="chips-label">Suggested follow-ups:</span>
                                            {m.suggested_follow_ups.map((sug, sIdx) => (
                                                <button
                                                    key={sIdx}
                                                    className="suggestion-chip"
                                                    onClick={() => handleSend(sug)}
                                                >
                                                    {sug}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div className="chat-bubble-row agent">
                                <div className="avatar-col">
                                    <div className={`agent-avatar ${activeRole}`}>
                                        {activeRole === "patient" ? <FaRobot /> : <FaUserMd />}
                                    </div>
                                </div>
                                <div className="bubble-content-col">
                                    <div className="typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Quick Prompts Bar */}
                    <div className="quick-prompts-section">
                        <span className="quick-prompts-label">
                            <FaMagic /> Quick Prompts:
                        </span>
                        <div className="quick-prompts-scroll">
                            {quickPrompts.map((p, idx) => (
                                <button
                                    key={idx}
                                    className="quick-prompt-pill"
                                    onClick={() => handleSend(p)}
                                    disabled={loading}
                                >
                                    {p}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Chat Input Bar */}
                    <form
                        className="chat-input-bar"
                        onSubmit={(e) => {
                            e.preventDefault();
                            handleSend();
                        }}
                    >
                        <input
                            type="text"
                            placeholder={
                                activeRole === "patient"
                                    ? "Ask about your symptoms, disease risks, nutrition, or medications..."
                                    : "Ask for patient triage summary, SOAP notes draft, or feature risk explanations..."
                            }
                            value={inputPrompt}
                            onChange={(e) => setInputPrompt(e.target.value)}
                            disabled={loading}
                        />
                        <button type="submit" className="send-btn" disabled={loading || !inputPrompt.trim()}>
                            <FaPaperPlane />
                            <span>Send</span>
                        </button>
                    </form>
                </div>

                {/* Sidebar Info & Integrated Models Card */}
                <div className="ai-agent-sidebar-card">
                    <div className="sidebar-section">
                        <h3>
                            <FaHeartbeat /> Active ML Engines
                        </h3>
                        <p className="sidebar-desc">
                            The agents are powered by four production machine learning architectures:
                        </p>
                        <div className="engine-item">
                            <div className="engine-name">Type 2 Diabetes Risk</div>
                            <div className="engine-type">RandomForestClassifier • 8 Features</div>
                        </div>
                        <div className="engine-item">
                            <div className="engine-name">Cardiovascular Heart Risk</div>
                            <div className="engine-type">GradientBoosting • 13 Vitals</div>
                        </div>
                        <div className="engine-item">
                            <div className="engine-name">Breast Cancer Biopsy</div>
                            <div className="engine-type">RandomForest • 10 FNA Nuclei</div>
                        </div>
                        <div className="engine-item">
                            <div className="engine-name">General Disease Classifier</div>
                            <div className="engine-type">RandomForest • 131 Symptoms</div>
                        </div>
                    </div>

                    <div className="sidebar-section">
                        <h3>
                            <FaShieldAlt /> Clinical Safeguards
                        </h3>
                        <ul className="safety-bullets">
                            <li>
                                <FaCheckCircle /> Automated Emergency Triage Detection
                            </li>
                            <li>
                                <FaCheckCircle /> Critical Threshold Rule Checks (BP & Glucose)
                            </li>
                            <li>
                                <FaCheckCircle /> Transparent Z-Score Explainability
                            </li>
                            <li>
                                <FaCheckCircle /> HIPAA-Compliant Data Isolation
                            </li>
                        </ul>
                    </div>

                    <div className="sidebar-section help-box">
                        <h4>Need a Full Multi-Disease Scan?</h4>
                        <p>Evaluate your vitals across Diabetes, Heart Disease, and Oncology.</p>
                        <a href="/patient/multi-disease-assessment" className="side-action-link">
                            <FaFileMedicalAlt /> Open Multi-Disease Engine
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AIAgentsHub;
