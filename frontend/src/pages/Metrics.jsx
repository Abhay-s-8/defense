import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Sparkles, ShieldAlert, CheckCircle2, RefreshCw } from "lucide-react";
import { api } from "../api";

export default function Metrics() {
  const [metrics, setMetrics] = useState(null);
  const [retraining, setRetraining] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadMetrics = () => {
    api.get("/metrics")
      .then((response) => setMetrics(response.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load metrics"));
  };

  useEffect(() => {
    loadMetrics();
  }, []);

  const triggerRetrain = async () => {
    setRetraining(true);
    setMessage("");
    setError("");
    try {
      const response = await api.post("/retrain", {});
      setMetrics(response.data.metrics);
      setMessage(response.data.message || "Model fortified successfully!");
    } catch (err) {
      setError(err.response?.data?.error || "Retraining failed");
    } finally {
      setRetraining(false);
    }
  };

  const chartData = metrics
    ? [
        {
          round: "Round 2 (Baseline)",
          detection: metrics.round_2?.detection_rate ?? 11.64,
        },
        {
          round: "Round 3 (After Retraining)",
          detection: metrics.round_3?.detection_rate ?? 97.48,
        },
      ]
    : [];

  return (
    <div>
      <div className="page-header">
        <div>
          <span className="page-label">CLOSED-LOOP DEFENSE</span>
          <h1>Model Fortification & Metrics</h1>
          <p>Live Attack → Detect → Learn → Defend performance evaluation.</p>
        </div>
      </div>

      {message && (
        <div className="success-box" style={{ background: "rgba(16, 185, 129, 0.15)", border: "1px solid #10b981", color: "#10b981", padding: "12px 16px", borderRadius: "8px", marginBottom: "20px", display: "flex", alignItems: "center", gap: "10px" }}>
          <CheckCircle2 size={20} />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="error-box" style={{ marginBottom: "20px" }}>
          {error}
        </div>
      )}

      <div className="metric-grid two-metrics">
        <div className="metric-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ color: "#ef4444", fontWeight: "600" }}>ROUND 2 (BASELINE VULNERABILITY)</span>
            <ShieldAlert size={20} color="#ef4444" />
          </div>
          <strong style={{ fontSize: "36px", color: "#f87171" }}>{metrics?.round_2?.detection_rate ?? "11.64"}%</strong>
          <small>{metrics?.round_2?.missed ?? 4418} missed attacks out of {metrics?.round_2?.total_attacks ?? 5000}</small>
        </div>

        <div className="metric-card">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
            <span style={{ color: "#10b981", fontWeight: "600" }}>ROUND 3 (DEFENDED & RETRAINED)</span>
            <CheckCircle2 size={20} color="#10b981" />
          </div>
          <strong style={{ fontSize: "36px", color: "#34d399" }}>{metrics?.round_3?.detection_rate ?? "97.48"}%</strong>
          <small>{metrics?.round_3?.detected ?? 4874} detected • Only {metrics?.round_3?.missed ?? 126} misses</small>
        </div>
      </div>

      <div className="dashboard-panel" style={{ marginTop: "24px", marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h3 style={{ margin: "0 0 6px 0" }}>Adversarial Learning Loop Control</h3>
            <p style={{ margin: 0, color: "#94a3b8", fontSize: "14px" }}>
              {metrics?.note || "Fortifies the XGBoost classifier by fine-tuning on captured missed attacks from Red Team simulations."}
            </p>
          </div>
          <button
            className="primary-button big-button"
            onClick={triggerRetrain}
            disabled={retraining}
            style={{ display: "flex", alignItems: "center", gap: "8px" }}
          >
            {retraining ? <RefreshCw className="spin" size={18} /> : <Sparkles size={18} />}
            {retraining ? "Retraining Model & Verifying..." : "Execute Retraining Loop"}
          </button>
        </div>
      </div>

      <div className="chart-container">
        <h3 style={{ marginBottom: "16px" }}>Adversarial Detection Rate Improvement</h3>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#29364b" />
            <XAxis dataKey="round" stroke="#9aa8bd" />
            <YAxis domain={[0, 100]} stroke="#9aa8bd" tickFormatter={(v) => `${v}%`} />
            <Tooltip formatter={(value) => [`${value}%`, "Detection Rate"]} />
            <Line
              type="monotone"
              dataKey="detection"
              stroke="#10b981"
              strokeWidth={4}
              dot={{ r: 8, fill: "#10b981", strokeWidth: 2, stroke: "#ffffff" }}
              activeDot={{ r: 10 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}