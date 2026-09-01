import { useState, useRef } from "react";
import { Sparkles, Shield, UserCheck, Activity, Network, AlertTriangle } from "lucide-react";
import { api } from "../api";

const defaultTransaction = {
  amount: 25000,
  payment_channel: "UPI",
  merchant_category: "ELECTRONICS",
  country: "IN",
  account_age_days: 1000,
  device_age_days: 2,
  new_device: 1,
  new_location: 1,
  new_beneficiary: 1,
  transaction_velocity_5m: 8,
  failed_attempts_1h: 4,
  avg_amount_30d: 1800,
  ip_risk_score: 90,
  beneficiary_age_days: 1,
  hour_of_day: 2,
  is_weekend: 0,
};

export default function Predict() {
  const [form, setForm] = useState(defaultTransaction);
  const [triadResult, setTriadResult] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [explainLoading, setExplainLoading] = useState(false);

  // Live Keystroke Telemetry Capture
  const keyPressStartTime = useRef({});
  const dwellTimes = useRef([]);
  const flightTimes = useRef([]);
  const lastKeyUpTime = useRef(null);
  const formStartTime = useRef(Date.now());
  const submitHoverStartTime = useRef(null);
  const submitHesitationMs = useRef(800);

  const handleKeyDown = (e) => {
    const key = e.key;
    if (!keyPressStartTime.current[key]) {
      keyPressStartTime.current[key] = performance.now();
    }
  };

  const handleKeyUp = (e) => {
    const key = e.key;
    const now = performance.now();
    if (keyPressStartTime.current[key]) {
      const dwell = now - keyPressStartTime.current[key];
      dwellTimes.current.push(dwell);
      delete keyPressStartTime.current[key];
    }
    if (lastKeyUpTime.current) {
      const flight = now - lastKeyUpTime.current;
      flightTimes.current.push(flight);
    }
    lastKeyUpTime.current = now;
  };

  const update = (name, value) => setForm({ ...form, [name]: value });

  const buildTelemetry = () => ({
    keystroke_dwell_times: dwellTimes.current.slice(-15),
    keystroke_flight_times: flightTimes.current.slice(-15),
    form_dwell_time_ms: Date.now() - formStartTime.current,
    submit_hesitation_ms: submitHesitationMs.current,
    backspace_count: 1,
    on_call_detected: false,
    remote_desktop_detected: false,
  });

  const predictTriad = async (event) => {
    event.preventDefault();
    setError("");
    setExplanation(null);
    setLoading(true);

    const payload = {
      transaction: {
        ...form,
        amount_deviation: Number((Number(form.amount) / Math.max(Number(form.avg_amount_30d), 1)).toFixed(3)),
      },
      interaction_telemetry: buildTelemetry(),
    };

    try {
      const response = await api.post("/predict/triad", payload);
      setTriadResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "Defense Triad evaluation failed");
    } finally {
      setLoading(false);
    }
  };

  const explain = async () => {
    if (!triadResult) return;
    setExplainLoading(true);
    setError("");
    try {
      const response = await api.post("/genai/explain", {
        transaction: form,
        model_result: {
          fraud_probability: triadResult.composite_risk_score,
          prediction: triadResult.composite_risk_score >= 70 ? "FRAUD" : (triadResult.composite_risk_score >= 35 ? "SUSPICIOUS" : "LEGITIMATE"),
          mathematical_contributions: {
            top_positive: triadResult.triad_breakdown?.layer_2_xgboost?.mathematical_drivers || [],
          },
        },
      });
      setExplanation(response.data.explanation);
    } catch (err) {
      setError(err.response?.data?.error || "GenAI explanation failed");
    } finally {
      setExplainLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <span className="page-label">3-LAYER DEFENSE TRIAD</span>
          <h1>Multi-Dimensional Fraud Defense</h1>
          <p>Fuses Layer 1 (Biometrics), Layer 2 (XGBoost), and Layer 3 (GNN Mule Ring Analysis).</p>
        </div>
      </div>

      <div className="two-column">
        <form className="model-form" onSubmit={predictTriad}>
          <h2>Transaction & Telemetry Inputs</h2>
          <div className="form-grid">
            <NumberField label="Amount (₹)" value={form.amount} onChange={(v) => update("amount", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="Average Amount (30D)" value={form.avg_amount_30d} onChange={(v) => update("avg_amount_30d", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <SelectField label="Payment Channel" value={form.payment_channel} options={["UPI", "CARD", "WALLET", "BANK_TRANSFER"]} onChange={(v) => update("payment_channel", v)} />
            <SelectField label="Merchant Category" value={form.merchant_category} options={["ELECTRONICS", "ECOMMERCE", "FOOD", "GROCERY", "TRAVEL", "ENTERTAINMENT", "OTHER"]} onChange={(v) => update("merchant_category", v)} />
            <SelectField label="Country" value={form.country} options={["IN", "SG", "AE", "GB", "US"]} onChange={(v) => update("country", v)} />
            <NumberField label="Account Age (Days)" value={form.account_age_days} onChange={(v) => update("account_age_days", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="Device Age (Days)" value={form.device_age_days} onChange={(v) => update("device_age_days", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="Velocity (5 Min)" value={form.transaction_velocity_5m} onChange={(v) => update("transaction_velocity_5m", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="Failed Attempts (1h)" value={form.failed_attempts_1h} onChange={(v) => update("failed_attempts_1h", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="IP Risk Score (0-100)" value={form.ip_risk_score} onChange={(v) => update("ip_risk_score", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="Beneficiary Age" value={form.beneficiary_age_days} onChange={(v) => update("beneficiary_age_days", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <NumberField label="Hour of Day" value={form.hour_of_day} onChange={(v) => update("hour_of_day", v)} onKeyDown={handleKeyDown} onKeyUp={handleKeyUp} />
            <BooleanField label="New Device" value={form.new_device} onChange={(v) => update("new_device", v)} />
            <BooleanField label="New Location" value={form.new_location} onChange={(v) => update("new_location", v)} />
            <BooleanField label="New Beneficiary" value={form.new_beneficiary} onChange={(v) => update("new_beneficiary", v)} />
            <BooleanField label="Is Weekend" value={form.is_weekend} onChange={(v) => update("is_weekend", v)} />
          </div>

          {error && <div className="error-box">{error}</div>}

          <button
            className="primary-button big-button full-width"
            disabled={loading}
            onMouseEnter={() => { submitHoverStartTime.current = performance.now(); }}
            onMouseLeave={() => {
              if (submitHoverStartTime.current) {
                submitHesitationMs.current = Math.max(300, performance.now() - submitHoverStartTime.current);
              }
            }}
          >
            {loading ? "Evaluating Defense Triad..." : "Execute 3-Layer Defense Scan"}
          </button>
        </form>

        <div className="prediction-panel">
          {!triadResult ? (
            <div className="empty-result">
              <Shield size={36} style={{ margin: "0 auto 12px auto", opacity: 0.5 }} />
              <div>Submit a transaction to evaluate across all 3 Defense Layers.</div>
            </div>
          ) : (
            <div className="prediction-result" style={{ textAlign: "left" }}>
              {/* Unified Decision Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #334155", paddingBottom: "12px", marginBottom: "14px" }}>
                <div>
                  <span style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase", letterSpacing: "1px" }}>UNIFIED COMPOSITE RISK</span>
                  <div style={{ fontSize: "28px", fontWeight: "bold", color: triadResult.status_color }}>{triadResult.composite_risk_score}%</div>
                </div>
                <div style={{ padding: "6px 12px", borderRadius: "6px", fontSize: "12px", fontWeight: "bold", background: `${triadResult.status_color}22`, color: triadResult.status_color, border: `1px solid ${triadResult.status_color}` }}>
                  {triadResult.decision_tier.replace(/_/g, " ")}
                </div>
              </div>

              <div style={{ fontSize: "12px", color: "#cbd5e1", marginBottom: "16px", background: "rgba(15, 23, 42, 0.6)", padding: "10px", borderRadius: "6px" }}>
                <strong>Policy Directive:</strong> {triadResult.policy_action}
              </div>

              {/* 3-Layer Triad Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" }}>
                {/* Layer 1 */}
                <div style={{ padding: "10px", borderRadius: "6px", background: "#1e293b", borderLeft: "4px solid #10b981" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: "600", color: "#34d399", marginBottom: "4px" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "6px" }}><UserCheck size={15} /> Layer 1: Behavioral Biometrics</span>
                    <span>Risk: {triadResult.triad_breakdown?.layer_1_biometrics?.score}%</span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                    {triadResult.triad_breakdown?.layer_1_biometrics?.signals?.[0] || "Standard genuine keystroke cadence"}
                  </div>
                </div>

                {/* Layer 2 */}
                <div style={{ padding: "10px", borderRadius: "6px", background: "#1e293b", borderLeft: "4px solid #3b82f6" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: "600", color: "#60a5fa", marginBottom: "4px" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "6px" }}><Activity size={15} /> Layer 2: XGBoost Behavioral Model</span>
                    <span>Prob: {triadResult.triad_breakdown?.layer_2_xgboost?.score}% ({triadResult.triad_breakdown?.layer_2_xgboost?.prediction})</span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                    Top Driver: {triadResult.triad_breakdown?.layer_2_xgboost?.mathematical_drivers?.[0]?.feature?.replace(/_/g, " ") || "Nominal spend range"}
                  </div>
                </div>

                {/* Layer 3 */}
                <div style={{ padding: "10px", borderRadius: "6px", background: "#1e293b", borderLeft: "4px solid #a855f7" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: "600", color: "#c084fc", marginBottom: "4px" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: "6px" }}><Network size={15} /> Layer 3: GNN Mule Network Analysis</span>
                    <span>Mule Risk: {triadResult.triad_breakdown?.layer_3_gnn_network?.score}%</span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                    {triadResult.triad_breakdown?.layer_3_gnn_network?.signals?.[0] || "Clean topology without cyclic fund loops"}
                  </div>
                </div>
              </div>

              <button className="secondary-button full-width ai-explain-button" onClick={explain} disabled={explainLoading}>
                <Sparkles size={17} /> {explainLoading ? "Generating 360° Explanation..." : "Explain Triad with GenAI"}
              </button>

              {explanation && (
                <div className="ai-insight-card" style={{ marginTop: "12px" }}>
                  <div className="ai-card-label">GENAI 360° DEFENSE EXPLAINER · {explanation.source?.toUpperCase()}</div>
                  <p>{explanation.summary}</p>
                  <ul>{explanation.key_signals?.map((s) => <li key={s}>{s}</li>)}</ul>
                  <div className="ai-action"><strong>Recommended action:</strong> {explanation.recommended_action}</div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function NumberField({ label, value, onChange, onKeyDown, onKeyUp }) {
  return <label>{label}<input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} onKeyDown={onKeyDown} onKeyUp={onKeyUp} /></label>;
}

function SelectField({ label, value, options, onChange }) {
  return <label>{label}<select value={value} onChange={(e) => onChange(e.target.value)}>{options.map((o) => <option key={o} value={o}>{o}</option>)}</select></label>;
}

function BooleanField({ label, value, onChange }) {
  return <label>{label}<select value={value} onChange={(e) => onChange(Number(e.target.value))}><option value={0}>No</option><option value={1}>Yes</option></select></label>;
}
