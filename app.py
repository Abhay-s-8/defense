import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from red_team.generator import generate_multiple_attacks
from services.fraud_service import predict_transaction
from services.llm_service import (
    analyze_red_team_run,
    explain_prediction,
    generate_attack_plan,
    llm_status,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "users.db")
JWT_SECRET = os.environ.get(
    "JWT_SECRET_KEY",
    "mastercard-ai-defense-local-dev-secret-change-before-deploy",
)
TOKEN_LIFETIME_SECONDS = 8 * 60 * 60

app = Flask(__name__)
CORS(app)


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db()
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS red_team_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            attack_type TEXT NOT NULL,
            total_attacks INTEGER NOT NULL,
            detected INTEGER NOT NULL,
            missed INTEGER NOT NULL,
            detection_rate REAL NOT NULL,
            strategy_source TEXT,
            strategy_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS missed_attacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            transaction_id TEXT,
            attack_json TEXT NOT NULL,
            probability REAL NOT NULL,
            risk_level TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.commit()
    connection.close()


initialize_database()


def _b64url_encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("utf-8")


def _b64url_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def create_token(user_id):
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + TOKEN_LIFETIME_SECONDS}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def verify_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, encoded_signature = parts
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected_signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
        provided_signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, provided_signature):
            return None
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def auth_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if request.method == "OPTIONS":
            return "", 204
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"error": "Authentication required. Please sign in."}), 401
        payload = verify_token(authorization[7:].strip())
        if not payload:
            return jsonify({"error": "Your session is invalid or expired. Please sign in again."}), 401
        request.current_user_id = payload["sub"]
        return view_function(*args, **kwargs)
    return wrapper


def validate_transaction(data):
    required = [
        "amount", "payment_channel", "merchant_category", "country", "account_age_days",
        "device_age_days", "new_device", "new_location", "new_beneficiary",
        "transaction_velocity_5m", "failed_attempts_1h", "avg_amount_30d",
        "amount_deviation", "ip_risk_score", "beneficiary_age_days", "hour_of_day", "is_weekend",
    ]
    missing = [field for field in required if field not in data or data[field] is None]
    return f"Missing transaction fields: {', '.join(missing)}" if missing else None


def latest_run_for_user(user_id):
    connection = get_db()
    row = connection.execute(
        "SELECT * FROM red_team_runs WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    connection.close()
    return dict(row) if row else None


@app.get("/")
def home():
    return jsonify({
        "message": "Mastercard AI Defense Lab API",
        "status": "running",
        "model": "behavioral_fraud_model_v4",
        "genai": llm_status(),
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": True,
        "authentication": "enabled",
        "genai": llm_status(),
    })


@app.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if len(name) < 2:
        return jsonify({"error": "Name must contain at least 2 characters."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"error": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must contain at least 8 characters."}), 400

    connection = get_db()
    existing = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        connection.close()
        return jsonify({"error": "An account already exists with this email."}), 409
    cursor = connection.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    connection.commit()
    user_id = cursor.lastrowid
    connection.close()
    return jsonify({
        "message": "Account created successfully.",
        "token": create_token(user_id),
        "user": {"id": user_id, "name": name, "email": email},
    }), 201


@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    connection = get_db()
    user = connection.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    connection.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({
        "message": "Signed in successfully.",
        "token": create_token(user["id"]),
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    })


@app.get("/auth/me")
@auth_required
def me():
    connection = get_db()
    user = connection.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?", (request.current_user_id,)
    ).fetchone()
    connection.close()
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": dict(user)})


@app.get("/models")
@auth_required
def models():
    return jsonify({
        "active_detector": {
            "name": "Behavioral Fraud Model V4",
            "type": "XGBoost classifier",
            "file": "behavioral_fraud_model_v4.json",
            "status": "active",
            "input": "behavioral transaction features",
        },
        "baseline_detector": {
            "name": "European credit-card baseline",
            "files": ["fraud_detector.pkl", "scaler.pkl"],
            "status": "stored_reference",
            "input": "PCA features V1-V28; not used for behavioral web inputs",
        },
        "red_team": {"name": "Synthetic adversarial generator", "status": "active"},
        "genai": llm_status(),
    })


@app.post("/predict")
@auth_required
def predict():
    data = request.get_json(silent=True) or {}
    validation_error = validate_transaction(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    try:
        return jsonify(predict_transaction(data))
    except Exception as exc:
        app.logger.exception("Prediction failed")
        return jsonify({"error": f"Model prediction failed: {str(exc)}"}), 500


@app.post("/genai/explain")
@auth_required
def genai_explain():
    data = request.get_json(silent=True) or {}
    transaction = data.get("transaction") or {}
    model_result = data.get("model_result")
    if not model_result:
        validation_error = validate_transaction(transaction)
        if validation_error:
            return jsonify({"error": validation_error}), 400
        model_result = predict_transaction(transaction)
    return jsonify({"model_result": model_result, "explanation": explain_prediction(transaction, model_result)})


@app.post("/genai/attack-plan")
@auth_required
def genai_attack_plan():
    data = request.get_json(silent=True) or {}
    attack_type = data.get("attack_type", "low_and_slow")
    objective = str(data.get("objective", ""))[:500]
    difficulty = data.get("difficulty", "hard")
    previous_run = latest_run_for_user(request.current_user_id)
    plan = generate_attack_plan(attack_type, objective, difficulty, previous_run)
    return jsonify({"plan": plan, "llm": llm_status()})


@app.post("/generate-attacks")
@auth_required
def generate_attacks():
    data = request.get_json(silent=True) or {}
    attack_type = data.get("attack_type")
    count = int(data.get("count", 100))
    plan = data.get("plan")
    if count < 1 or count > 5000:
        return jsonify({"error": "Count must be between 1 and 5000."}), 400
    try:
        attacks = generate_multiple_attacks(attack_type, count, plan=plan)
        return jsonify({"attack_type": attack_type, "generated": len(attacks), "attacks": attacks[:100]})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/run-red-team")
@auth_required
def run_red_team():
    data = request.get_json(silent=True) or {}
    attack_type = data.get("attack_type")
    count = int(data.get("count", 100))
    plan = data.get("plan")
    if count < 1 or count > 5000:
        return jsonify({"error": "Count must be between 1 and 5000."}), 400

    try:
        attacks = generate_multiple_attacks(attack_type, count, plan=plan)
        detected = 0
        results = []
        missed_full = []

        for attack in attacks:
            prediction = predict_transaction(attack)
            if prediction["prediction"] == "FRAUD":
                detected += 1
            else:
                missed_full.append({**attack, "model_probability": prediction["fraud_probability"]})

            results.append({
                "transaction_id": attack["transaction_id"],
                "fraud_type": attack["fraud_type"],
                "amount": attack["amount"],
                "ip_risk_score": attack["ip_risk_score"],
                "velocity": attack["transaction_velocity_5m"],
                "probability": prediction["fraud_probability"],
                "prediction": prediction["prediction"],
                "risk_level": prediction["risk_level"],
            })

        missed = count - detected
        detection_rate = round((detected / count) * 100, 2)
        strategy_source = (plan or {}).get("source", "default_generator") if isinstance(plan, dict) else "default_generator"

        connection = get_db()
        cursor = connection.execute(
            """
            INSERT INTO red_team_runs
            (user_id, attack_type, total_attacks, detected, missed, detection_rate, strategy_source, strategy_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.current_user_id, attack_type, count, detected, missed, detection_rate,
                strategy_source, json.dumps(plan or {}),
            ),
        )
        run_id = cursor.lastrowid
        for missed_attack in missed_full[:1000]:
            connection.execute(
                "INSERT INTO missed_attacks (run_id, transaction_id, attack_json, probability, risk_level) VALUES (?, ?, ?, ?, ?)",
                (
                    run_id,
                    missed_attack.get("transaction_id"),
                    json.dumps(missed_attack),
                    float(missed_attack.get("model_probability", 0)),
                    "LOW" if float(missed_attack.get("model_probability", 0)) < 30 else "MEDIUM",
                ),
            )
        connection.commit()
        connection.close()

        summary = {
            "run_id": run_id,
            "attack_type": attack_type,
            "total_attacks": count,
            "detected": detected,
            "missed": missed,
            "detection_rate": detection_rate,
            "strategy_source": strategy_source,
        }
        return jsonify({**summary, "results": results[:100], "missed_samples": missed_full[:20]})

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Red Team simulation failed")
        return jsonify({"error": f"Red Team simulation failed: {str(exc)}"}), 500


@app.post("/genai/analyze-run")
@auth_required
def genai_analyze_run():
    data = request.get_json(silent=True) or {}
    run_id = data.get("run_id")
    connection = get_db()
    if run_id:
        run = connection.execute(
            "SELECT * FROM red_team_runs WHERE id = ? AND user_id = ?", (run_id, request.current_user_id)
        ).fetchone()
    else:
        run = connection.execute(
            "SELECT * FROM red_team_runs WHERE user_id = ? ORDER BY id DESC LIMIT 1", (request.current_user_id,)
        ).fetchone()
    if not run:
        connection.close()
        return jsonify({"error": "No Red Team run found yet."}), 404
    rows = connection.execute(
        "SELECT attack_json FROM missed_attacks WHERE run_id = ? ORDER BY id LIMIT 20", (run["id"],)
    ).fetchall()
    connection.close()
    missed_samples = [json.loads(row["attack_json"]) for row in rows]
    analysis = analyze_red_team_run(dict(run), missed_samples)
    return jsonify({"run": dict(run), "analysis": analysis, "missed_sample_count": len(missed_samples)})


@app.get("/red-team/history")
@auth_required
def red_team_history():
    connection = get_db()
    rows = connection.execute(
        """
        SELECT id, attack_type, total_attacks, detected, missed, detection_rate, strategy_source, created_at
        FROM red_team_runs WHERE user_id = ? ORDER BY id DESC LIMIT 20
        """,
        (request.current_user_id,),
    ).fetchall()
    connection.close()
    return jsonify({"runs": [dict(row) for row in rows]})


@app.get("/red-team/runs/<int:run_id>/missed")
@auth_required
def red_team_missed(run_id):
    connection = get_db()
    run = connection.execute(
        "SELECT id FROM red_team_runs WHERE id = ? AND user_id = ?", (run_id, request.current_user_id)
    ).fetchone()
    if not run:
        connection.close()
        return jsonify({"error": "Run not found."}), 404
    rows = connection.execute(
        "SELECT transaction_id, attack_json, probability, risk_level FROM missed_attacks WHERE run_id = ? ORDER BY id LIMIT 100",
        (run_id,),
    ).fetchall()
    connection.close()
    return jsonify({
        "run_id": run_id,
        "missed": [
            {
                "transaction_id": row["transaction_id"],
                "transaction": json.loads(row["attack_json"]),
                "probability": row["probability"],
                "risk_level": row["risk_level"],
            }
            for row in rows
        ],
    })


@app.get("/metrics")
@auth_required
def metrics():
    return jsonify({
        "round_2": {"total_attacks": 5000, "detected": 582, "missed": 4418, "detection_rate": 11.64},
        "round_3": {"total_attacks": 5000, "detected": 4874, "missed": 126, "detection_rate": 97.48},
        "note": "These are held-out synthetic adversarial experiment results.",
    })


if __name__ == "__main__":
    print("Starting Mastercard AI Defense Lab...")
    print("Frontend expected at: http://localhost:5173")
    print("Backend API: http://127.0.0.1:5000")
    print("GenAI mode:", llm_status()["mode"])
    app.run(host="0.0.0.0", port=5000, debug=True)
