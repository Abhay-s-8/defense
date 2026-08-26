import { useState } from "react";
import { Sparkles } from "lucide-react";
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
  const [result, setResult] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [explainLoading, setExplainLoading] = useState(false);

  const update = (name, value) => setForm({ ...form, [name]: value });

  const buildPayload = () => ({
    ...form,
    amount_deviation: Number((Number(form.amount) / Math.max(Number(form.avg_amount_30d), 1)).toFixed(3)),
  });

  const predict = async (event) => {
    event.preventDefault();
    setError("");
    setExplanation(null);
    setLoading(true);
    try {
      const response = await api.post("/predict", buildPayload());
      setResult(response.data);
    } catch (error) {
      setError(error.response?.data?.error || (error.code === "ERR_NETWORK" ? "Cannot reach Flask API. Start py -3.12 app.py." : "Prediction failed"));
    } finally {
      setLoading(false);
    }
  };

  const explain = async () => {
    if (!result) return;
    setExplainLoading(true);
    setError("");
    try {
      const response = await api.post("/genai/explain", {
        transaction: buildPayload(),
        model_result: result,
      });
      setExplanation(response.data.explanation);
    } catch (error) {
      setError(error.response?.data?.error || "GenAI explanation failed");
    } finally {
      setExplainLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <span className="page-label">BLUE TEAM</span>
          <h1>Fraud Prediction</h1>
          <p>Manually test one transaction against the trained behavioral XGBoost model.</p>
        </div>
      </div>

      <div className="two-column">
        <form className="model-form" onSubmit={predict}>
          <h2>Transaction Features</h2>
          <div className="form-grid">
            <NumberField label="Amount" value={form.amount} onChange={(v) => update("amount", v)} />
            <NumberField label="Average Amount" value={form.avg_amount_30d} onChange={(v) => update("avg_amount_30d", v)} />
            <SelectField label="Payment Channel" value={form.payment_channel} options={["CARD", "UPI", "WALLET", "BANK_TRANSFER"]} onChange={(v) => update("payment_channel", v)} />
            <SelectField label="Merchant" value={form.merchant_category} options={["GROCERY", "FOOD", "FUEL", "ECOMMERCE", "TRAVEL", "ELECTRONICS", "ENTERTAINMENT", "UTILITIES", "HEALTHCARE", "OTHER"]} onChange={(v) => update("merchant_category", v)} />
            <SelectField label="Country" value={form.country} options={["IN", "SG", "AE", "GB", "US"]} onChange={(v) => update("country", v)} />
            <NumberField label="Account Age" value={form.account_age_days} onChange={(v) => update("account_age_days", v)} />
            <NumberField label="Device Age" value={form.device_age_days} onChange={(v) => update("device_age_days", v)} />
            <NumberField label="Velocity" value={form.transaction_velocity_5m} onChange={(v) => update("transaction_velocity_5m", v)} />
            <NumberField label="Failed Attempts" value={form.failed_attempts_1h} onChange={(v) => update("failed_attempts_1h", v)} />
            <NumberField label="IP Risk" value={form.ip_risk_score} onChange={(v) => update("ip_risk_score", v)} />
            <NumberField label="Beneficiary Age" value={form.beneficiary_age_days} onChange={(v) => update("beneficiary_age_days", v)} />
            <NumberField label="Hour" value={form.hour_of_day} onChange={(v) => update("hour_of_day", v)} />
            <BooleanField label="New Device" value={form.new_device} onChange={(v) => update("new_device", v)} />
            <BooleanField label="New Location" value={form.new_location} onChange={(v) => update("new_location", v)} />
            <BooleanField label="New Beneficiary" value={form.new_beneficiary} onChange={(v) => update("new_beneficiary", v)} />
            <BooleanField label="Weekend" value={form.is_weekend} onChange={(v) => update("is_weekend", v)} />
          </div>
          {error && <div className="error-box">{error}</div>}
          <button className="primary-button big-button full-width" disabled={loading}>{loading ? "Analyzing..." : "Analyze Transaction"}</button>
        </form>

        <div className="prediction-panel">
          {!result ? (
            <div className="empty-result">Waiting for transaction...</div>
          ) : (
            <div className="prediction-result">
              <div className={`risk-label ${result.risk_level.toLowerCase()}`}>{result.risk_level}</div>
              <strong className="prediction-score">{result.fraud_probability}%</strong>
              <span>Fraud Probability</span>
              <div className="prediction-bar"><div style={{ width: `${result.fraud_probability}%` }} /></div>
              <div className="prediction-row"><span>Prediction</span><strong>{result.prediction}</strong></div>

              <button className="secondary-button full-width ai-explain-button" onClick={explain} disabled={explainLoading}>
                <Sparkles size={17} /> {explainLoading ? "Explaining..." : "Explain with GenAI"}
              </button>

              {explanation && (
                <div className="ai-insight-card">
                  <div className="ai-card-label">GENAI ANALYST · {explanation.source === "remote_llm" ? "REMOTE LLM" : "LOCAL FALLBACK"}</div>
                  <p>{explanation.summary}</p>
                  <ul>{explanation.key_signals?.map((signal) => <li key={signal}>{signal}</li>)}</ul>
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

function NumberField({ label, value, onChange }) {
  return <label>{label}<input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} /></label>;
}

function SelectField({ label, value, options, onChange }) {
  return <label>{label}<select value={value} onChange={(e) => onChange(e.target.value)}>{options.map((o) => <option key={o} value={o}>{o}</option>)}</select></label>;
}

function BooleanField({ label, value, onChange }) {
  return <label>{label}<select value={value} onChange={(e) => onChange(Number(e.target.value))}><option value={0}>No</option><option value={1}>Yes</option></select></label>;
}
