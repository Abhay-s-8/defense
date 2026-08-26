import { useState } from "react";
import { BrainCircuit, Sparkles } from "lucide-react";
import { api } from "../api";

const attacks = [
  ["account_takeover", "Account Takeover"],
  ["card_testing", "Card Testing"],
  ["mule_activity", "Mule Activity"],
  ["low_and_slow", "Low & Slow"],
];

export default function RedTeam() {
  const [attackType, setAttackType] = useState("low_and_slow");
  const [count, setCount] = useState(100);
  const [difficulty, setDifficulty] = useState("hard");
  const [objective, setObjective] = useState("Create a stealthy synthetic scenario that challenges the current detector without relying on obvious signals.");
  const [plan, setPlan] = useState(null);
  const [result, setResult] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  const generatePlan = async () => {
    setPlanLoading(true); setError("");
    try {
      const response = await api.post("/genai/attack-plan", { attack_type: attackType, objective, difficulty });
      setPlan(response.data.plan);
    } catch (error) {
      setError(error.response?.data?.error || "Could not generate AI strategy");
    } finally { setPlanLoading(false); }
  };

  const runRedTeam = async () => {
    setLoading(true); setError(""); setAnalysis(null);
    try {
      const response = await api.post("/run-red-team", { attack_type: attackType, count: Number(count), plan });
      setResult(response.data);
    } catch (error) {
      setError(error.response?.data?.error || "Simulation failed");
    } finally { setLoading(false); }
  };

  const analyzeRun = async () => {
    if (!result?.run_id) return;
    setAnalysisLoading(true); setError("");
    try {
      const response = await api.post("/genai/analyze-run", { run_id: result.run_id });
      setAnalysis(response.data.analysis);
    } catch (error) {
      setError(error.response?.data?.error || "Run analysis failed");
    } finally { setAnalysisLoading(false); }
  };

  return (
    <div>
      <div className="page-header"><div><span className="page-label">RED TEAM</span><h1>Attack Simulator</h1><p>AI plans the scenario; the controlled Python generator creates safe synthetic transactions; XGBoost scores every attack.</p></div></div>

      <div className="two-column red-layout">
        <div className="red-team-panel">
          <h2>Attack Type</h2>
          <div className="attack-list">{attacks.map(([id, name]) => <button key={id} className={attackType === id ? "attack-card selected" : "attack-card"} onClick={() => { setAttackType(id); setPlan(null); }}>{name}</button>)}</div>

          <div className="ai-strategy-builder">
            <div className="ai-card-label"><Sparkles size={15} /> GENAI ATTACK STRATEGIST</div>
            <label>Difficulty<select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard / stealthy</option></select></label>
            <label>Defensive testing objective<textarea value={objective} onChange={(e) => setObjective(e.target.value)} rows={4} /></label>
            <button className="secondary-button full-width" onClick={generatePlan} disabled={planLoading}>{planLoading ? "Planning..." : "Generate AI Strategy"}</button>
          </div>

          {plan && <div className="plan-card"><div className="plan-top"><strong>{plan.title}</strong><span>{plan.source === "remote_llm" ? "LLM" : "Fallback"}</span></div><p>{plan.strategy}</p><small>{plan.why_it_is_hard}</small></div>}

          <label>Number of Attacks<input type="number" min="1" max="5000" value={count} onChange={(e) => setCount(e.target.value)} /></label>
          {error && <div className="error-box">{error}</div>}
          <button className="danger-button big-button full-width" onClick={runRedTeam} disabled={loading}>{loading ? "Running simulation..." : "Launch Red Team"}</button>
        </div>

        <div className="prediction-panel red-results-panel">
          {!result ? <div className="empty-result">Run an attack simulation.</div> : (
            <div className="prediction-result red-result-wrap">
              <strong className="prediction-score">{result.detection_rate}%</strong><span>Detection Rate</span>
              <div className="red-metrics"><MetricBox title="Generated" value={result.total_attacks} /><MetricBox title="Detected" value={result.detected} /><MetricBox title="Missed" value={result.missed} /></div>
              <div className="result-source">Run #{result.run_id} · strategy: {result.strategy_source}</div>
              <button className="secondary-button full-width" onClick={analyzeRun} disabled={analysisLoading}><BrainCircuit size={17} /> {analysisLoading ? "Analyzing misses..." : "Analyze Misses with GenAI"}</button>

              {analysis && <div className="ai-insight-card left-align"><div className="ai-card-label">GENAI WEAKNESS ANALYST · {analysis.source === "remote_llm" ? "REMOTE LLM" : "LOCAL FALLBACK"}</div><p>{analysis.finding}</p><ul>{analysis.likely_weaknesses?.map((x) => <li key={x}>{x}</li>)}</ul><div className="ai-action"><strong>Next test:</strong> {analysis.next_test}</div><div className="ai-action"><strong>Retraining note:</strong> {analysis.retraining_note}</div></div>}

              <h3 className="attack-results-title">Individual Attack Probabilities</h3>
              <div className="attack-results-list">{result.results?.map((item, index) => <div className="attack-result-row" key={item.transaction_id}><div><strong>#{index + 1} · ₹{Number(item.amount).toLocaleString()}</strong><small>{item.transaction_id}</small></div><div className="attack-result-score"><strong>{item.probability}%</strong><span className={item.prediction === "FRAUD" ? "fraud-text" : "legit-text"}>{item.prediction}</span></div></div>)}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricBox({ title, value }) { return <div className="mini-metric"><span>{title}</span><strong>{value}</strong></div>; }
