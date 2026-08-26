import { useEffect, useState } from "react";
import { BrainCircuit, Cpu, Database, Radar, ShieldCheck, Sparkles } from "lucide-react";
import { api } from "../api";

export default function GenAILab() {
  const [models, setModels] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.get("/models"), api.get("/red-team/history")])
      .then(([m, h]) => { setModels(m.data); setHistory(h.data.runs || []); })
      .catch((e) => setError(e.response?.data?.error || "Could not load GenAI Lab"));
  }, []);

  return (
    <div>
      <div className="page-header"><div><span className="page-label">GENAI LAB</span><h1>AI Strategy & Analysis Layer</h1><p>The LLM does not replace XGBoost. It plans safe synthetic attack scenarios and explains model behavior.</p></div></div>
      {error && <div className="error-box">{error}</div>}
      <div className="metric-grid">
        <Status icon={<ShieldCheck />} title="Blue Team" value="XGBoost V4" text="Active behavioral detector" />
        <Status icon={<Radar />} title="Red Team" value="Generator" text="Controlled stochastic simulation" />
        <Status icon={<Sparkles />} title="GenAI" value={models?.genai?.mode === "remote_llm" ? "Remote LLM" : "Fallback"} text={models?.genai?.model || "Loading..."} />
        <Status icon={<Database />} title="Missed Cases" value={history[0]?.missed ?? "—"} text="Stored from latest run" />
      </div>

      <div className="dashboard-panel genai-flow-panel">
        <h2>How the models are connected</h2>
        <div className="genai-flow">
          <Flow icon={<BrainCircuit />} title="LLM Strategist" text="Creates high-level attack parameters" />
          <span>→</span><Flow icon={<Cpu />} title="Python Generator" text="Creates reproducible synthetic transactions" />
          <span>→</span><Flow icon={<ShieldCheck />} title="XGBoost" text="Returns fraud probability" />
          <span>→</span><Flow icon={<Sparkles />} title="LLM Analyst" text="Explains misses and proposes the next safe test" />
        </div>
      </div>

      <div className="dashboard-panel">
        <h2>Recent Red Team Runs</h2>
        {history.length === 0 ? <p className="muted">No runs yet.</p> : <div className="history-table">{history.map((run) => <div className="history-row" key={run.id}><span>#{run.id}</span><strong>{run.attack_type.replaceAll("_", " ")}</strong><span>{run.detection_rate}% detected</span><span>{run.missed} missed</span><small>{run.strategy_source}</small></div>)}</div>}
      </div>

      <div className="dashboard-panel"><h2>Remote LLM configuration</h2><p className="muted">Current mode: <strong>{models?.genai?.mode || "loading"}</strong>. The project always works using its built-in fallback. To enable a remote OpenAI-compatible model, set LLM_BASE_URL, LLM_MODEL and (when required) LLM_API_KEY before starting Flask.</p></div>
    </div>
  );
}

function Status({ icon, title, value, text }) { return <div className="metric-card"><div className="metric-icon">{icon}</div><span>{title}</span><strong>{value}</strong><small>{text}</small></div>; }
function Flow({ icon, title, text }) { return <div className="pipeline-box genai-flow-box">{icon}<strong>{title}</strong><span>{text}</span></div>; }
