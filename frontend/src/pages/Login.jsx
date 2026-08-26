import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", form);
      localStorage.setItem("mastercard_token", data.token);
      localStorage.setItem("mastercard_user", JSON.stringify(data.user));
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mc-auth-page">
      <div className="mc-auth-visual">
        <div className="mc-auth-arc one"></div>
        <div className="mc-auth-arc two"></div>

        <div className="mc-auth-logo-block army-auth-logo-block">
          <div className="army-auth-emblem">⚔</div>
          <div className="mc-auth-wordmark">FraudShield</div>
          <div className="mc-auth-subtitle">AI DEFENSE LAB · TEAM AITIANS</div>
        </div>

        <div className="mc-auth-copy">
          <div className="mc-eyebrow">SECURE COMMAND ACCESS</div>
          <h1>Enter the intelligent defense command center.</h1>
          <p>
            Sign in to access the protected Blue Team, Red Team, GenAI analysis, and adversarial experiment workspace.
          </p>
        </div>
      </div>

      <div className="mc-auth-form-pane">
        <form className="mc-auth-card" onSubmit={submit}>
          <div className="mc-eyebrow">WELCOME BACK</div>
          <h2>Sign in</h2>

          {error && <div className="mc-auth-error">{error}</div>}

          <label>
            Email
            <input name="email" type="email" value={form.email} onChange={change} required />
          </label>

          <label>
            Password
            <input name="password" type="password" value={form.password} onChange={change} required />
          </label>

          <button className="mc-auth-primary" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="mc-auth-switch">
            New here? <Link to="/register">Create account</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
