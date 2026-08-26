# FraudShield AI Defense Lab — GenAI Edition

This build keeps the working XGBoost V4 fraud detector and adds a GenAI strategy/analysis layer without changing the model's role.

## What is connected

- **Blue Team / XGBoost V4**: scores behavioral transactions and returns fraud probability, prediction, and risk level.
- **Red Team generator**: creates controlled synthetic fraud transactions. It can use default distributions or a safe structured plan produced by the GenAI strategist.
- **GenAI Attack Strategist**: creates a high-level synthetic attack plan (amount ratio, IP-risk range, velocity range, probabilities of new device/location/beneficiary, and active hours). The Python generator, not the LLM, produces the final numeric transactions.
- **GenAI Prediction Analyst**: explains a Blue Team result in plain language using supplied behavioral features and the model output.
- **GenAI Weakness Analyst**: reviews a Red Team run and stored missed attacks, summarizes weaknesses, and proposes the next safe synthetic test.
- **Run history / missed storage**: every Red Team run is recorded in SQLite; missed synthetic attacks are stored for later analysis/retraining workflows.

The website does **not** automatically retrain XGBoost after every Red Team launch. Missed attacks are stored as candidate adversarial examples. Proper retraining should be a controlled offline/admin step, followed by evaluation on a fresh unseen attack set.

## Run backend

From the project root on Windows:

```bat
py -3.12 -m pip install -r requirements.txt
py -3.12 app.py
```

Check:

```text
http://127.0.0.1:5000/health
```

## Run frontend

Open a second terminal:

```bat
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## GenAI modes

The project works immediately without any LLM API key. In that case the GenAI buttons use a deterministic local fallback so the demo does not break.

To enable a remote LLM, copy `.env.example` to `.env` and configure an **OpenAI-compatible chat-completions endpoint**:

```env
LLM_PROVIDER_NAME=My Provider
LLM_BASE_URL=https://your-provider.example/v1
LLM_MODEL=your-model-name
LLM_API_KEY=your-key-if-required
```

Then restart Flask. `/health` and the GenAI Lab page show whether the project is using `remote_llm` or `local_fallback`.

## New API endpoints

```text
GET  /models
POST /genai/explain
POST /genai/attack-plan
POST /genai/analyze-run
GET  /red-team/history
GET  /red-team/runs/<run_id>/missed
```

Existing protected endpoints remain:

```text
POST /predict
POST /generate-attacks
POST /run-red-team
GET  /metrics
GET  /auth/me
```

## Model note

`behavioral_fraud_model_v4.json` is the active web detector. `fraud_detector.pkl` and `scaler.pkl` are retained as the earlier PCA-based credit-card baseline, but they are intentionally **not** used on the behavioral web form because their input schema is V1–V28 and is incompatible with the behavioral features.
