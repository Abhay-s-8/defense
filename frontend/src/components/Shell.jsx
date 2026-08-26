import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  ShieldCheck,
  Radar,
  BrainCircuit,
  BarChart3,
  LogOut
} from "lucide-react";

const navItems = [
  ["/dashboard", "Dashboard", LayoutDashboard],
  ["/predict", "Blue Team", ShieldCheck],
  ["/red-team", "Red Team", Radar],
  ["/genai", "GenAI Lab", BrainCircuit],
  ["/metrics", "AI vs AI", BarChart3],
];

export default function Shell({ children }) {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("mastercard_user") || "{}");

  const logout = () => {
    localStorage.removeItem("mastercard_token");
    localStorage.removeItem("mastercard_user");
    navigate("/login");
  };

  return (
    <div className="mc-app-shell">
      <aside className="mc-sidebar">
        <div>
          <div className="mc-sidebar-brand">
            <div className="army-sidebar-emblem" aria-hidden="true">⚔</div>
            <div className="mc-sidebar-brand-copy">
              <strong>FraudShield</strong>
              <span>Defense Command UI</span>
            </div>
          </div>

          <nav className="mc-sidebar-nav">
            {navItems.map(([to, label, Icon]) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  isActive ? "mc-side-link active" : "mc-side-link"
                }
              >
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="mc-sidebar-bottom">
          <div className="mc-sidebar-user">
            <strong>{user.name || "User"}</strong>
            <span>{user.email || ""}</span>
          </div>

          <button className="mc-logout-button" onClick={logout}>
            <LogOut size={17} />
            Logout
          </button>
        </div>
      </aside>

      <main className="mc-app-main">
        <div className="mc-page-watermark army-page-watermark">
          <div className="army-watermark-emblem">⚔</div>
          <div className="mc-watermark-text">DEFENSE COMMAND</div>
        </div>
        {children}
      </main>
    </div>
  );
}
