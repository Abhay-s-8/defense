import base64
from collections import defaultdict
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from red_team.generator import generate_multiple_attacks, generate_attack
from services.biometrics_service import biometrics_engine
from services.defense_triad import defense_triad
from services.feature_store import feature_store
from services.fraud_service import (
    predict_transaction,
    predict_batch_transactions,
    get_current_metrics,
    retrain_model_with_misses,
)
from services.gnn_service import gnn_analyzer
from services.llm_service import (
    analyze_red_team_run,
    explain_prediction,
    generate_attack_plan,
    llm_status,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_defense_lab")

# ============================================================
# CONFIG
# ============================================================

JWT_SECRET = os.environ.get(
    "JWT_SECRET_KEY",
    "ai-defense-lab-local-dev-secret-key-2026-replace-in-prod",
)

TOKEN_LIFETIME_SECONDS = 8 * 60 * 60

# ============================================================
# SLIDING-WINDOW API RATE LIMITER
# ============================================================

_ip_request_windows = defaultdict(list)

def rate_limit(max_requests=60, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method == "OPTIONS":
                return "", 204
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
            now = time.time()
            cutoff = now - window_seconds
            
            _ip_request_windows[client_ip] = [t for t in _ip_request_windows[client_ip] if t > cutoff]
            if len(_ip_request_windows[client_ip]) >= max_requests:
                return jsonify({
                    "error": f"Rate limit exceeded: maximum {max_requests} requests per {window_seconds}s allowed."
                }), 429
            
            _ip_request_windows[client_ip].append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# RESILIENT DATABASE LAYER (MongoDB with Fallback Storage)
# ============================================================

class ResilientCollection:
    def __init__(self, name):
        self.name = name
        self.docs = []
        self.unique_keys = set()

    def create_index(self, key, unique=False):
        if unique:
            self.unique_keys.add(key)

    def insert_one(self, doc):
        doc_copy = dict(doc)
        if "_id" not in doc_copy:
            doc_copy["_id"] = str(uuid.uuid4())
        
        for uk in self.unique_keys:
            if uk in doc_copy:
                for existing in self.docs:
                    if existing.get(uk) == doc_copy[uk]:
                        from pymongo.errors import DuplicateKeyError
                        raise DuplicateKeyError(f"Duplicate value for {uk}: {doc_copy[uk]}")
        
        self.docs.append(doc_copy)
        
        class InsertResult:
            inserted_id = doc_copy["_id"]
        return InsertResult()

    def insert_many(self, doc_list):
        for doc in doc_list:
            self.insert_one(doc)

    def find_one(self, filter_dict=None, sort=None):
        results = self._match(filter_dict)
        if sort:
            results = self._sort(results, sort)
        return results[0] if results else None

    def find(self, filter_dict=None):
        results = self._match(filter_dict)
        return ResilientCursor(results)

    def _match(self, filter_dict):
        if not filter_dict:
            return list(self.docs)
        matched = []
        for d in self.docs:
            match = True
            for k, v in filter_dict.items():
                d_val = str(d.get(k)) if k == "_id" else d.get(k)
                v_val = str(v) if k == "_id" else v
                if d_val != v_val:
                    match = False
                    break
            if match:
                matched.append(d)
        return matched

    def _sort(self, items, sort_spec):
        for key, direction in reversed(sort_spec):
            reverse = direction == -1
            items = sorted(
                items,
                key=lambda x: x.get(key, ""),
                reverse=reverse
            )
        return items


class ResilientCursor:
    def __init__(self, items):
        self.items = list(items)

    def sort(self, key, direction=1):
        reverse = direction == -1
        self.items = sorted(
            self.items,
            key=lambda x: x.get(key, ""),
            reverse=reverse
        )
        return self

    def limit(self, n):
        self.items = self.items[:n]
        return self

    def __iter__(self):
        return iter(self.items)

    def __len__(self):
        return len(self.items)


MONGODB_URI = os.environ.get("MONGODB_URI")
db_mode = "fallback_memory"
users_collection = ResilientCollection("users")
runs_collection = ResilientCollection("red_team_runs")
missed_collection = ResilientCollection("missed_attacks")

if MONGODB_URI:
    try:
        from pymongo import MongoClient
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")
        mongo_db = mongo_client["fraudshield"]
        users_collection = mongo_db["users"]
        runs_collection = mongo_db["red_team_runs"]
        missed_collection = mongo_db["missed_attacks"]
        users_collection.create_index("email", unique=True)
        db_mode = "mongodb"
        logger.info("Connected successfully to MongoDB Atlas (database: fraudshield)")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Falling back to resilient local storage.")
        db_mode = "fallback_memory"


# ============================================================
# FLASK APP & CORS
# ============================================================

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://ai-defense-lab.vercel.app",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
            ]
        }
    },
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)


@app.after_request
def add_cors_and_security_headers(response):
    origin = request.headers.get("Origin")
    if origin and (
        origin == "https://ai-defense-lab.vercel.app"
        or origin.endswith(".vercel.app")
        or origin in [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
    ):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Vary"] = "Origin"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ============================================================
# HELPERS
# ============================================================

def mongo_health():
    if db_mode == "mongodb":
        try:
            mongo_client.admin.command("ping")
            return True
        except Exception:
            return False
    return True


def serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def serialize_run(run):
    if not run:
        return None
    return {
        "id": str(run.get("_id", "")),
        "user_id": str(run.get("user_id", "")),
        "attack_type": run.get("attack_type"),
        "total_attacks": run.get("total_attacks", 0),
        "detected": run.get("detected", 0),
        "missed": run.get("missed", 0),
        "detection_rate": run.get("detection_rate", 0),
        "strategy_source": run.get("strategy_source"),
        "strategy_json": run.get("strategy_json", {}),
        "created_at": serialize_datetime(run.get("created_at")),
    }


# ============================================================
# JWT AUTHENTICATION
# ============================================================

def _b64url_encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode("utf-8")


def _b64url_decode(value):
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def create_token(user_id):
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
    }

    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}"

    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return f"{signing_input}.{_b64url_encode(signature)}"


def verify_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        encoded_header, encoded_payload, encoded_signature = parts[0], parts[1], parts[2]
        signing_input = f"{encoded_header}.{encoded_payload}"

        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()

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


# ============================================================
# SERVER-SIDE FEATURE ENRICHMENT & VALIDATION
# ============================================================

def validate_and_enrich_transaction(data):
    """
    Checks if transaction is fully specified or requires server-side
    feature derivation via RealTimeFeatureStore.
    """
    if "amount" not in data:
        return None, "Missing required field: amount"

    required_behavioral = [
        "payment_channel", "merchant_category", "country",
        "account_age_days", "device_age_days", "new_device",
        "new_location", "new_beneficiary", "transaction_velocity_5m",
        "failed_attempts_1h", "avg_amount_30d", "amount_deviation",
        "ip_risk_score", "beneficiary_age_days", "hour_of_day", "is_weekend"
    ]

    # If any behavioral signal is missing, enrich automatically on server
    is_partial = any(k not in data or data[k] is None for k in required_behavioral)
    if is_partial:
        enriched = feature_store.enrich_transaction(data)
        return enriched, None

    return data, None


def latest_run_for_user(user_id):
    run = runs_collection.find_one(
        {"user_id": str(user_id)},
        sort=[("created_at", -1)],
    )
    if not run:
        return None
    return serialize_run(run)


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
def home():
    return jsonify({
        "message": "AI Defense Lab for Payment Security API",
        "status": "running",
        "model": "behavioral_fraud_model_v4_fortified",
        "database": db_mode,
        "database_connected": mongo_health(),
        "genai": llm_status(),
        "feature_store": "active_server_side",
    })


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": True,
        "authentication": "enabled",
        "database": db_mode,
        "database_connected": mongo_health(),
        "genai": llm_status(),
        "feature_store": "active_server_side",
    })


@app.post("/auth/register")
@rate_limit(max_requests=30, window_seconds=60)
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

    try:
        existing = users_collection.find_one({"email": email})
        if existing:
            return jsonify({"error": "An account already exists with this email."}), 409

        result = users_collection.insert_one({
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now(timezone.utc),
        })

        user_id = str(result.inserted_id)
        return jsonify({
            "message": "Account created successfully.",
            "token": create_token(user_id),
            "user": {"id": user_id, "name": name, "email": email},
        }), 201

    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            return jsonify({"error": "An account already exists with this email."}), 409
        logger.exception("Registration error")
        return jsonify({"error": f"Database error while creating account: {str(exc)}"}), 500


@app.post("/auth/login")
@rate_limit(max_requests=30, window_seconds=60)
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    try:
        user = users_collection.find_one({"email": email})
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password."}), 401

        user_id = str(user["_id"])
        return jsonify({
            "message": "Signed in successfully.",
            "token": create_token(user_id),
            "user": {"id": user_id, "name": user["name"], "email": user["email"]},
        })
    except Exception as exc:
        logger.exception("Login error")
        return jsonify({"error": f"Database error while signing in: {str(exc)}"}), 500


@app.get("/auth/me")
@auth_required
def me():
    try:
        user = users_collection.find_one({"_id": request.current_user_id})
        if not user:
            return jsonify({"error": "User not found."}), 404

        return jsonify({
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "created_at": serialize_datetime(user.get("created_at")),
            }
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/models")
@auth_required
def models():
    return jsonify({
        "active_detector": {
            "name": "Behavioral Fraud Model V4 Fortified",
            "type": "XGBoost classifier",
            "file": "behavioral_fraud_model_v4_retrained.json",
            "status": "active",
            "input": "behavioral transaction features",
            "explainability": "TreeSHAP exact mathematical marginal contributions",
        },
        "baseline_detector": {
            "name": "European credit-card baseline",
            "files": ["fraud_detector.pkl", "scaler.pkl"],
            "status": "stored_reference",
            "input": "PCA features V1-V28",
        },
        "red_team": {
            "name": "Synthetic adversarial generator with stochastic evasion",
            "status": "active",
        },
        "feature_store": {
            "name": "RealTimeFeatureStore (Server-Side Anti-Injection)",
            "status": "active",
        },
        "genai": llm_status(),
    })


@app.post("/predict")
@auth_required
@rate_limit(max_requests=120, window_seconds=60)
def predict():
    data = request.get_json(silent=True) or {}
    enriched_tx, error = validate_and_enrich_transaction(data)
    if error:
        return jsonify({"error": error}), 400

    try:
        prediction = predict_transaction(enriched_tx)
        return jsonify({
            **prediction,
            "server_enriched_signals": enriched_tx,
        })
    except Exception as exc:
        logger.exception("Prediction failed")
        return jsonify({"error": f"Model prediction failed: {str(exc)}"}), 500


@app.post("/predict/triad")
@auth_required
@rate_limit(max_requests=120, window_seconds=60)
def predict_triad():
    """
    Evaluates all 3 layers of the Defense Triad:
      Layer 1: Behavioral Biometrics (Keystroke telemetry & coercion)
      Layer 2: XGBoost Behavioral Model (Server-Enriched Features)
      Layer 3: GNN Graph Analysis (Mule rings & smurfing)
    """
    data = request.get_json(silent=True) or {}
    transaction = data.get("transaction") or data
    telemetry = data.get("interaction_telemetry")
    sender_id = data.get("sender_id") or str(request.current_user_id)
    receiver_id = data.get("receiver_id") or data.get("beneficiary_id")

    try:
        triad_eval = defense_triad.evaluate_triad(
            transaction=transaction,
            interaction_telemetry=telemetry,
            sender_id=sender_id,
            receiver_id=receiver_id,
        )
        return jsonify(triad_eval)
    except Exception as exc:
        logger.exception("Triad prediction failed")
        return jsonify({"error": f"Triad evaluation failed: {str(exc)}"}), 500


@app.get("/network/topology")
@auth_required
def network_topology():
    """
    Fetches live money-flow graph topology for GNN network visualization.
    """
    try:
        topology = gnn_analyzer.get_network_topology()
        return jsonify(topology)
    except Exception as exc:
        logger.exception("Network topology failed")
        return jsonify({"error": f"Topology retrieval failed: {str(exc)}"}), 500


@app.post("/simulate/mule-syndicate")
@auth_required
def simulate_mule_syndicate():
    """
    Simulates a coordinated multi-hop mule ring and detects the syndicate topology.
    """
    try:
        import random
        cluster_id = f"SYNDICATE_{random.randint(100, 999)}"
        nodes = [f"{cluster_id}_NODE_{i}" for i in range(1, 6)]
        now = time.time()

        for i in range(len(nodes)):
            src = nodes[i]
            dst = nodes[(i + 1) % len(nodes)]
            amt = round(random.uniform(25000, 75000), 2)
            gnn_analyzer.add_transaction(src, dst, amt, now - (i * 20), f"TX_MULE_{random.randint(1000, 9999)}")

        gnn_analyzer.flagged_mule_nodes.update(nodes)
        eval_result = gnn_analyzer.evaluate_network_risk(nodes[0], nodes[1], 50000)

        return jsonify({
            "syndicate_cluster_id": cluster_id,
            "simulated_nodes": nodes,
            "network_risk_evaluation": eval_result,
            "topology": gnn_analyzer.get_network_topology(),
        })
    except Exception as exc:
        logger.exception("Mule syndicate simulation failed")
        return jsonify({"error": f"Mule simulation failed: {str(exc)}"}), 500


@app.post("/genai/explain")
@auth_required
def genai_explain():
    data = request.get_json(silent=True) or {}
    transaction = data.get("transaction") or {}
    model_result = data.get("model_result")

    enriched_tx, error = validate_and_enrich_transaction(transaction)
    if error:
        return jsonify({"error": error}), 400

    if not model_result:
        model_result = predict_transaction(enriched_tx)

    explanation = explain_prediction(enriched_tx, model_result)
    return jsonify({
        "model_result": model_result,
        "explanation": explanation,
    })


@app.post("/genai/attack-plan")
@auth_required
def genai_attack_plan():
    data = request.get_json(silent=True) or {}
    attack_type = data.get("attack_type", "low_and_slow")
    objective = str(data.get("objective", ""))[:500]
    difficulty = data.get("difficulty", "hard")
    previous_run = latest_run_for_user(request.current_user_id)

    plan = generate_attack_plan(
        attack_type,
        objective,
        difficulty,
        previous_run,
    )

    return jsonify({
        "plan": plan,
        "llm": llm_status(),
    })


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
        return jsonify({
            "attack_type": attack_type,
            "generated": len(attacks),
            "attacks": attacks[:100],
        })
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
        # 1. Generate attacks with adversarial noise & evasions
        attacks = generate_multiple_attacks(attack_type, count, plan=plan)

        # 2. Fast Vectorized Batch Prediction
        batch_results = predict_batch_transactions(attacks)

        detected = 0
        missed_full = []
        formatted_results = []

        for i, res in enumerate(batch_results):
            attack = attacks[i]
            if res["prediction"] == "FRAUD":
                detected += 1
            else:
                missed_full.append({
                    **attack,
                    "model_probability": res["fraud_probability"],
                })

            formatted_results.append({
                "transaction_id": res["transaction_id"],
                "fraud_type": res["fraud_type"],
                "amount": res["amount"],
                "ip_risk_score": res["ip_risk_score"],
                "velocity": res["velocity"],
                "probability": res["fraud_probability"],
                "prediction": res["prediction"],
                "risk_level": res["risk_level"],
            })

        missed = count - detected
        detection_rate = round((detected / count) * 100, 2)
        strategy_source = plan.get("source", "default_generator") if isinstance(plan, dict) else "default_generator"

        # 3. Store Run in Database
        run_document = {
            "user_id": str(request.current_user_id),
            "attack_type": attack_type,
            "total_attacks": count,
            "detected": detected,
            "missed": missed,
            "detection_rate": detection_rate,
            "strategy_source": strategy_source,
            "strategy_json": plan or {},
            "created_at": datetime.now(timezone.utc),
        }

        run_result = runs_collection.insert_one(run_document)
        run_id = str(run_result.inserted_id)

        # 4. Store Missed Attacks for Closed-Loop Retraining
        if missed_full:
            missed_documents = []
            for missed_attack in missed_full[:1000]:
                prob = float(missed_attack.get("model_probability", 0))
                missed_documents.append({
                    "run_id": run_id,
                    "user_id": str(request.current_user_id),
                    "transaction_id": missed_attack.get("transaction_id"),
                    "attack": missed_attack,
                    "probability": prob,
                    "risk_level": "LOW" if prob < 30 else "MEDIUM",
                    "created_at": datetime.now(timezone.utc),
                })
            if missed_documents:
                missed_collection.insert_many(missed_documents)

        return jsonify({
            "run_id": run_id,
            "attack_type": attack_type,
            "total_attacks": count,
            "detected": detected,
            "missed": missed,
            "detection_rate": detection_rate,
            "strategy_source": strategy_source,
            "results": formatted_results[:100],
            "missed_samples": missed_full[:20],
        })

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Red Team simulation failed")
        return jsonify({"error": f"Red Team simulation failed: {str(exc)}"}), 500


@app.post("/genai/analyze-run")
@auth_required
def genai_analyze_run():
    data = request.get_json(silent=True) or {}
    run_id = data.get("run_id")

    try:
        if run_id:
            run = runs_collection.find_one({"_id": run_id, "user_id": str(request.current_user_id)})
        else:
            run = runs_collection.find_one(
                {"user_id": str(request.current_user_id)},
                sort=[("created_at", -1)],
            )

        if not run:
            return jsonify({"error": "No Red Team run found yet."}), 404

        run_id_str = str(run["_id"])
        rows = missed_collection.find({"run_id": run_id_str}).sort("created_at", 1).limit(20)
        missed_samples = [row.get("attack", {}) for row in rows]
        serialized = serialize_run(run)
        analysis = analyze_red_team_run(serialized, missed_samples)

        return jsonify({
            "run": serialized,
            "analysis": analysis,
            "missed_sample_count": len(missed_samples),
        })

    except Exception as exc:
        logger.exception("Run analysis failed")
        return jsonify({"error": f"Database error while analyzing run: {str(exc)}"}), 500


@app.get("/red-team/history")
@auth_required
def red_team_history():
    try:
        rows = runs_collection.find({"user_id": str(request.current_user_id)}).sort("created_at", -1).limit(20)
        runs = [serialize_run(row) for row in rows]
        return jsonify({"runs": runs})
    except Exception as exc:
        logger.exception("History retrieval failed")
        return jsonify({"error": f"Database error while loading history: {str(exc)}"}), 500


@app.get("/red-team/runs/<run_id>/missed")
@auth_required
def red_team_missed(run_id):
    try:
        run = runs_collection.find_one({"_id": run_id, "user_id": str(request.current_user_id)})
        if not run:
            return jsonify({"error": "Run not found."}), 404

        rows = missed_collection.find({"run_id": run_id}).sort("created_at", 1).limit(100)
        missed = [{
            "transaction_id": row.get("transaction_id"),
            "transaction": row.get("attack"),
            "probability": row.get("probability"),
            "risk_level": row.get("risk_level"),
        } for row in rows]

        return jsonify({"run_id": run_id, "missed": missed})
    except Exception as exc:
        logger.exception("Missed attacks retrieval failed")
        return jsonify({"error": f"Database error while loading missed attacks: {str(exc)}"}), 500


# ============================================================
# CLOSED-LOOP RETRAINING & PERFORMANCE METRICS
# ============================================================

@app.post("/retrain")
@auth_required
def trigger_retrain():
    """
    Executes the dynamic Attack -> Detect -> Learn -> Defend loop.
    Uses balanced replay buffer + captured missed attacks to update model weights.
    """
    try:
        rows = missed_collection.find({"user_id": str(request.current_user_id)}).limit(500)
        missed_samples = [row.get("attack", {}) for row in rows if row.get("attack")]
        
        def test_generator():
            return generate_multiple_attacks("low_and_slow", 100)

        updated_metrics = retrain_model_with_misses(missed_samples, test_attacks_generator=test_generator)
        return jsonify({
            "message": "Model fortified with balanced replay buffer and verified on held-out adversarial test suite.",
            "metrics": updated_metrics,
        })
    except Exception as exc:
        logger.exception("Retraining loop error")
        return jsonify({"error": f"Retraining failed: {str(exc)}"}), 500


@app.get("/metrics")
@auth_required
def metrics():
    return jsonify(get_current_metrics())


# ============================================================
# LOCAL RUNNER
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting AI Defense Lab API on port {port}...")
    print(f"Database storage mode: {db_mode}")
    print(f"GenAI mode: {llm_status()['mode']}")
    print(f"Server-Side Real-Time Feature Store: active")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
