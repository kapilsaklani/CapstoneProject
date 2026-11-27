import api from "./api";

export const getAssessmentModules = async () => {
    const response = await api.get("/api/assessments/modules");
    return response.data;
};

export const getModuleInfo = async (moduleName) => {
    const response = await api.get(`/api/assessments/info/${moduleName}`);
    return response.data;
};

export const evaluateRisk = async (diseaseModule, features) => {
    const response = await api.post("/api/assessments/evaluate", {
        disease_module: diseaseModule,
        features: features,
    });
    return response.data;
};

export const getAssessmentHistory = async () => {
    const response = await api.get("/api/assessments/history");
    return response.data;
};

export const consultPatientAgent = async (message, context = null) => {
    const response = await api.post("/api/agents/patient", {
        message,
        context,
    });
    return response.data;
};

export const getPatientQuickPrompts = async () => {
    const response = await api.get("/api/agents/patient/quick-prompts");
    return response.data;
};

export const consultDoctorAgent = async (message, patientId = null, context = null) => {
    const response = await api.post("/api/agents/doctor", {
        message,
        patient_id: patientId,
        context,
    });
    return response.data;
};

export const getDoctorQuickPrompts = async () => {
    const response = await api.get("/api/agents/doctor/quick-prompts");
    return response.data;
};
