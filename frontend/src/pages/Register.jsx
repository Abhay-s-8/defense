import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const change = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/auth/register", form);
      localStorage.setItem("mastercard_token", data.token);
      localStorage.setItem("mastercard_user", JSON.stringify(data.user));
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.error || "Unable to create account.");
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
          <div className="mc-eyebrow">ENLIST ACCESS</div>
          <h1>Strengthen the digital payment perimeter.</h1>
          <p>
            Create access to the secure command workspace for transaction scoring, synthetic attack simulation, GenAI analysis, and model evaluation.
          </p>
        </div>
      </div>

      <div className="mc-auth-form-pane">
        <form className="mc-auth-card" onSubmit={submit}>
          <div className="mc-eyebrow">CREATE ACCOUNT</div>
          <h2>Get started</h2>

          {error && <div className="mc-auth-error">{error}</div>}

          <label>
            Full name
            <input name="name" value={form.name} onChange={change} required />
          </label>

          <label>
            Email
            <input name="email" type="email" value={form.email} onChange={change} required />
          </label>

          <label>
            Password
            <input name="password" type="password" minLength="8" value={form.password} onChange={change} required />
          </label>

          <button className="mc-auth-primary" disabled={loading}>
            {loading ? "Creating..." : "Create account"}
          </button>

          <p className="mc-auth-switch">
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
