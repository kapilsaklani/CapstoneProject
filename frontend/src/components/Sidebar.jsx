import { NavLink, useLocation } from "react-router-dom";
import {
    FaHome,
    FaUser,
    FaHeartbeat,
    FaRobot,
    FaHistory,
    FaLightbulb,
    FaFileMedical,
    FaUserNurse,
    FaSignOutAlt,
    FaChartBar,
    FaUserMd,
    FaShieldAlt,
    FaClipboardList,
} from "react-icons/fa";

import "../styles/Sidebar.css";

function Sidebar({ logout }) {
    const location = useLocation();
    const isCaretaker = location.pathname.startsWith("/caretaker");

    return (
        <aside className="sidebar">
            <h2 className="sidebar-logo">
                🏥 MedAssist
            </h2>

            <nav>
                {isCaretaker ? (
                    <>
                        <NavLink to="/caretaker/dashboard" className="sidebar-link">
                            <FaHome />
                            Dashboard
                        </NavLink>

                        <NavLink to="/caretaker/ai-copilot" className="sidebar-link">
                            <FaUserMd />
                            Doctor AI Co-Pilot
                        </NavLink>

                        <NavLink to="/caretaker/patients" className="sidebar-link">
                            <FaUserNurse />
                            Assigned Patients
                        </NavLink>

                        <NavLink to="/caretaker/care-plans" className="sidebar-link">
                            <FaClipboardList />
                            Care Plans
                        </NavLink>

                        <NavLink to="/caretaker/analytics" className="sidebar-link">
                            <FaChartBar />
                            Analytics
                        </NavLink>

                        <NavLink to="/caretaker/profile" className="sidebar-link">
                            <FaUser />
                            Profile
                        </NavLink>
                    </>
                ) : (
                    <>
                        <NavLink to="/patient/dashboard" className="sidebar-link">
                            <FaHome />
                            Dashboard
                        </NavLink>

                        <NavLink to="/patient/ai-agent" className="sidebar-link">
                            <FaRobot />
                            AI Health Assistant
                        </NavLink>

                        <NavLink to="/patient/multi-disease-assessment" className="sidebar-link">
                            <FaShieldAlt />
                            Multi-Disease AI
                        </NavLink>

                        <NavLink to="/patient/symptoms" className="sidebar-link">
                            <FaHeartbeat />
                            Symptoms
                        </NavLink>

                        <NavLink to="/patient/disease-prediction" className="sidebar-link">
                            <FaRobot />
                            Prediction
                        </NavLink>

                        <NavLink to="/patient/medical-history" className="sidebar-link">
                            <FaHistory />
                            History
                        </NavLink>

                        <NavLink to="/patient/recommendations" className="sidebar-link">
                            <FaLightbulb />
                            Recommendations
                        </NavLink>

                        <NavLink to="/patient/health-reports" className="sidebar-link">
                            <FaFileMedical />
                            Reports
                        </NavLink>

                        <NavLink to="/patient/analytics" className="sidebar-link">
                            <FaChartBar />
                            Analytics
                        </NavLink>

                        <NavLink to="/patient/select-caretaker" className="sidebar-link">
                            <FaUserNurse />
                            Caretaker
                        </NavLink>
                    </>
                )}
            </nav>

            <button className="logout-btn" onClick={logout}>
                <FaSignOutAlt />
                Logout
            </button>
        </aside>
    );
}

export default Sidebar;
