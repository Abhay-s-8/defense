import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from functools import wraps

from bson import ObjectId
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash

from red_team.generator import generate_multiple_attacks
from services.fraud_service import predict_transaction
from services.llm_service import (
    analyze_red_team_run,
    explain_prediction,
    generate_attack_plan,
    llm_status,
)


# ============================================================
# CONFIG
# ============================================================

JWT_SECRET = os.environ.get(
    "JWT_SECRET_KEY",
    "mastercard-ai-defense-local-dev-secret-change-before-deploy",
)

TOKEN_LIFETIME_SECONDS = 8 * 60 * 60

MONGODB_URI = os.environ.get("MONGODB_URI")
client = MongoClient(MONGODB_URI)

db = client["Aidefense"]

users_collection = db["users"]
runs_collection = db["red_team_runs"]
missed_collection = db["missed_attacks"]
if not MONGODB_URI:
    raise RuntimeError(
        "MONGODB_URI environment variable is not configured."
    )


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# CORS
# ============================================================

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://ai-defense-lab.vercel.app",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    },
    supports_credentials=False,
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
    methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
)


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    if origin and (
        origin == "https://ai-defense-lab.vercel.app"
        or origin.endswith(".vercel.app")
        or origin
        in [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    ):
        response.headers["Access-Control-Allow-Origin"] = origin

        response.headers[
            "Access-Control-Allow-Headers"
        ] = "Content-Type, Authorization"

        response.headers[
            "Access-Control-Allow-Methods"
        ] = "GET, POST, OPTIONS"

        response.headers["Vary"] = "Origin"

    return response


# ============================================================
# MONGODB CONNECTION
# ============================================================

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=10000,
)

db = client["fraudshield"]

users_collection = db["users"]
runs_collection = db["red_team_runs"]
missed_collection = db["missed_attacks"]


# Prevent duplicate accounts
users_collection.create_index(
    "email",
    unique=True,
)


# ============================================================
# HELPERS
# ============================================================

def mongo_health():
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False


def serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def serialize_run(run):
    if not run:
        return None

    return {
        "id": str(run["_id"]),
        "user_id": str(run.get("user_id", "")),
        "attack_type": run.get("attack_type"),
        "total_attacks": run.get(
            "total_attacks",
            0,
        ),
        "detected": run.get(
            "detected",
            0,
        ),
        "missed": run.get(
            "missed",
            0,
        ),
        "detection_rate": run.get(
            "detection_rate",
            0,
        ),
        "strategy_source": run.get(
            "strategy_source",
        ),
        "strategy_json": run.get(
            "strategy_json",
            {},
        ),
        "created_at": serialize_datetime(
            run.get("created_at")
        ),
    }


# ============================================================
# JWT
# ============================================================

def _b64url_encode(raw_bytes):
    return (
        base64.urlsafe_b64encode(raw_bytes)
        .rstrip(b"=")
        .decode("utf-8")
    )


def _b64url_decode(value):
    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(
        (value + padding).encode("utf-8")
    )


def create_token(user_id):
    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    now = int(time.time())

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
    }

    encoded_header = _b64url_encode(
        json.dumps(
            header,
            separators=(",", ":"),
        ).encode("utf-8")
    )

    encoded_payload = _b64url_encode(
        json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")
    )

    signing_input = (
        f"{encoded_header}.{encoded_payload}"
    )

    signature = hmac.new(
        JWT_SECRET.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return (
        f"{signing_input}."
        f"{_b64url_encode(signature)}"
    )


def verify_token(token):
    try:
        parts = token.split(".")

        if len(parts) != 3:
            return None

        encoded_header = parts[0]
        encoded_payload = parts[1]
        encoded_signature = parts[2]

        signing_input = (
            f"{encoded_header}.{encoded_payload}"
        )

        expected_signature = hmac.new(
            JWT_SECRET.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        provided_signature = _b64url_decode(
            encoded_signature
        )

        if not hmac.compare_digest(
            expected_signature,
            provided_signature,
        ):
            return None

        payload = json.loads(
            _b64url_decode(
                encoded_payload
            ).decode("utf-8")
        )

        if int(payload.get("exp", 0)) < int(
            time.time()
        ):
            return None

        return payload

    except Exception:
        return None


# ============================================================
# AUTH DECORATOR
# ============================================================

def auth_required(view_function):

    @wraps(view_function)
    def wrapper(*args, **kwargs):

        if request.method == "OPTIONS":
            return "", 204

        authorization = request.headers.get(
            "Authorization",
            "",
        )

        if not authorization.startswith(
            "Bearer "
        ):
            return jsonify({
                "error":
                "Authentication required. Please sign in."
            }), 401

        payload = verify_token(
            authorization[7:].strip()
        )

        if not payload:
            return jsonify({
                "error":
                "Your session is invalid or expired. Please sign in again."
            }), 401

        request.current_user_id = payload["sub"]

        return view_function(
            *args,
            **kwargs,
        )

    return wrapper


# ============================================================
# TRANSACTION VALIDATION
# ============================================================

def validate_transaction(data):

    required = [
        "amount",
        "payment_channel",
        "merchant_category",
        "country",
        "account_age_days",
        "device_age_days",
        "new_device",
        "new_location",
        "new_beneficiary",
        "transaction_velocity_5m",
        "failed_attempts_1h",
        "avg_amount_30d",
        "amount_deviation",
        "ip_risk_score",
        "beneficiary_age_days",
        "hour_of_day",
        "is_weekend",
    ]

    missing = [
        field
        for field in required
        if field not in data
        or data[field] is None
    ]

    if missing:
        return (
            "Missing transaction fields: "
            + ", ".join(missing)
        )

    return None


# ============================================================
# LATEST RED TEAM RUN
# ============================================================

def latest_run_for_user(user_id):

    run = runs_collection.find_one(
        {
            "user_id":
            str(user_id)
        },
        sort=[
            (
                "created_at",
                -1,
            )
        ],
    )

    if not run:
        return None

    return serialize_run(run)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return jsonify({
        "message":
        "Mastercard AI Defense Lab API",
        "status":
        "running",
        "model":
        "behavioral_fraud_model_v4",
        "database":
        "mongodb",
        "mongodb_connected":
        mongo_health(),
        "genai":
        llm_status(),
    })


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return jsonify({
        "status":
        "ok",
        "model_loaded":
        True,
        "authentication":
        "enabled",
        "database":
        "mongodb",
        "mongodb_connected":
        mongo_health(),
        "genai":
        llm_status(),
    })


# ============================================================
# REGISTER
# ============================================================

@app.post("/auth/register")
def register():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    name = str(
        data.get(
            "name",
            "",
        )
    ).strip()

    email = str(
        data.get(
            "email",
            "",
        )
    ).strip().lower()

    password = str(
        data.get(
            "password",
            "",
        )
    )

    if len(name) < 2:
        return jsonify({
            "error":
            "Name must contain at least 2 characters."
        }), 400

    if (
        "@" not in email
        or "." not in email
    ):
        return jsonify({
            "error":
            "Enter a valid email address."
        }), 400

    if len(password) < 8:
        return jsonify({
            "error":
            "Password must contain at least 8 characters."
        }), 400

    try:

        existing = users_collection.find_one({
            "email": email
        })

        if existing:

            return jsonify({
                "error":
                "An account already exists with this email."
            }), 409

        result = users_collection.insert_one({
            "name":
            name,
            "email":
            email,
            "password_hash":
            generate_password_hash(
                password
            ),
            "created_at":
            datetime.now(
                timezone.utc
            ),
        })

        user_id = str(
            result.inserted_id
        )

        return jsonify({
            "message":
            "Account created successfully.",

            "token":
            create_token(
                user_id
            ),

            "user": {
                "id":
                user_id,

                "name":
                name,

                "email":
                email,
            },

        }), 201

    except DuplicateKeyError:

        return jsonify({
            "error":
            "An account already exists with this email."
        }), 409

    except PyMongoError as exc:

        app.logger.exception(
            "MongoDB registration failed"
        )

        return jsonify({
            "error":
            f"Database error while creating account: {str(exc)}"
        }), 500


# ============================================================
# LOGIN
# ============================================================

@app.post("/auth/login")
def login():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    email = str(
        data.get(
            "email",
            "",
        )
    ).strip().lower()

    password = str(
        data.get(
            "password",
            "",
        )
    )

    try:

        user = users_collection.find_one({
            "email": email
        })

        if (
            not user
            or not check_password_hash(
                user["password_hash"],
                password,
            )
        ):

            return jsonify({
                "error":
                "Invalid email or password."
            }), 401

        user_id = str(
            user["_id"]
        )

        return jsonify({
            "message":
            "Signed in successfully.",

            "token":
            create_token(
                user_id
            ),

            "user": {
                "id":
                user_id,

                "name":
                user["name"],

                "email":
                user["email"],
            },

        })

    except PyMongoError as exc:

        app.logger.exception(
            "MongoDB login failed"
        )

        return jsonify({
            "error":
            f"Database error while signing in: {str(exc)}"
        }), 500


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/auth/me")
@auth_required
def me():

    try:

        user_id = ObjectId(
            request.current_user_id
        )

    except Exception:

        return jsonify({
            "error":
            "Invalid user id."
        }), 400

    user = users_collection.find_one({
        "_id": user_id
    })

    if not user:

        return jsonify({
            "error":
            "User not found."
        }), 404

    return jsonify({
        "user": {
            "id":
            str(user["_id"]),

            "name":
            user["name"],

            "email":
            user["email"],

            "created_at":
            serialize_datetime(
                user.get(
                    "created_at"
                )
            ),
        }
    })


# ============================================================
# MODELS
# ============================================================

@app.get("/models")
@auth_required
def models():

    return jsonify({

        "active_detector": {

            "name":
            "Behavioral Fraud Model V4",

            "type":
            "XGBoost classifier",

            "file":
            "behavioral_fraud_model_v4.json",

            "status":
            "active",

            "input":
            "behavioral transaction features",
        },

        "baseline_detector": {

            "name":
            "European credit-card baseline",

            "files": [
                "fraud_detector.pkl",
                "scaler.pkl",
            ],

            "status":
            "stored_reference",

            "input":
            "PCA features V1-V28; not used for behavioral web inputs",
        },

        "red_team": {

            "name":
            "Synthetic adversarial generator",

            "status":
            "active",
        },

        "genai":
        llm_status(),

    })


# ============================================================
# PREDICT
# ============================================================

@app.post("/predict")
@auth_required
def predict():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    validation_error = (
        validate_transaction(
            data
        )
    )

    if validation_error:

        return jsonify({
            "error":
            validation_error
        }), 400

    try:

        prediction = (
            predict_transaction(
                data
            )
        )

        return jsonify(
            prediction
        )

    except Exception as exc:

        app.logger.exception(
            "Prediction failed"
        )

        return jsonify({
            "error":
            f"Model prediction failed: {str(exc)}"
        }), 500


# ============================================================
# GENAI EXPLANATION
# ============================================================

@app.post("/genai/explain")
@auth_required
def genai_explain():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    transaction = (
        data.get(
            "transaction"
        )
        or {}
    )

    model_result = data.get(
        "model_result"
    )

    if not model_result:

        validation_error = (
            validate_transaction(
                transaction
            )
        )

        if validation_error:

            return jsonify({
                "error":
                validation_error
            }), 400

        model_result = (
            predict_transaction(
                transaction
            )
        )

    return jsonify({

        "model_result":
        model_result,

        "explanation":
        explain_prediction(
            transaction,
            model_result,
        ),

    })


# ============================================================
# GENAI ATTACK PLAN
# ============================================================

@app.post("/genai/attack-plan")
@auth_required
def genai_attack_plan():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    attack_type = data.get(
        "attack_type",
        "low_and_slow",
    )

    objective = str(
        data.get(
            "objective",
            "",
        )
    )[:500]

    difficulty = data.get(
        "difficulty",
        "hard",
    )

    previous_run = (
        latest_run_for_user(
            request.current_user_id
        )
    )

    plan = generate_attack_plan(
        attack_type,
        objective,
        difficulty,
        previous_run,
    )

    return jsonify({

        "plan":
        plan,

        "llm":
        llm_status(),

    })


# ============================================================
# GENERATE ATTACKS
# ============================================================

@app.post("/generate-attacks")
@auth_required
def generate_attacks():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    attack_type = data.get(
        "attack_type"
    )

    count = int(
        data.get(
            "count",
            100,
        )
    )

    plan = data.get(
        "plan"
    )

    if (
        count < 1
        or count > 5000
    ):

        return jsonify({
            "error":
            "Count must be between 1 and 5000."
        }), 400

    try:

        attacks = (
            generate_multiple_attacks(
                attack_type,
                count,
                plan=plan,
            )
        )

        return jsonify({

            "attack_type":
            attack_type,

            "generated":
            len(attacks),

            "attacks":
            attacks[:100],

        })

    except ValueError as exc:

        return jsonify({
            "error":
            str(exc)
        }), 400


# ============================================================
# RUN RED TEAM
# ============================================================

@app.post("/run-red-team")
@auth_required
def run_red_team():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    attack_type = data.get(
        "attack_type"
    )

    count = int(
        data.get(
            "count",
            100,
        )
    )

    plan = data.get(
        "plan"
    )

    if (
        count < 1
        or count > 5000
    ):

        return jsonify({
            "error":
            "Count must be between 1 and 5000."
        }), 400

    try:

        attacks = (
            generate_multiple_attacks(
                attack_type,
                count,
                plan=plan,
            )
        )

        detected = 0

        results = []

        missed_full = []

        for attack in attacks:

            prediction = (
                predict_transaction(
                    attack
                )
            )

            if (
                prediction[
                    "prediction"
                ]
                == "FRAUD"
            ):

                detected += 1

            else:

                missed_full.append({

                    **attack,

                    "model_probability":
                    prediction[
                        "fraud_probability"
                    ],

                })

            results.append({

                "transaction_id":
                attack[
                    "transaction_id"
                ],

                "fraud_type":
                attack[
                    "fraud_type"
                ],

                "amount":
                attack[
                    "amount"
                ],

                "ip_risk_score":
                attack[
                    "ip_risk_score"
                ],

                "velocity":
                attack[
                    "transaction_velocity_5m"
                ],

                "probability":
                prediction[
                    "fraud_probability"
                ],

                "prediction":
                prediction[
                    "prediction"
                ],

                "risk_level":
                prediction[
                    "risk_level"
                ],

            })

        missed = (
            count
            - detected
        )

        detection_rate = round(
            (
                detected
                / count
            )
            * 100,
            2,
        )

        if isinstance(
            plan,
            dict,
        ):

            strategy_source = (
                plan.get(
                    "source",
                    "default_generator",
                )
            )

        else:

            strategy_source = (
                "default_generator"
            )

        run_document = {

            "user_id":
            str(
                request.current_user_id
            ),

            "attack_type":
            attack_type,

            "total_attacks":
            count,

            "detected":
            detected,

            "missed":
            missed,

            "detection_rate":
            detection_rate,

            "strategy_source":
            strategy_source,

            "strategy_json":
            plan or {},

            "created_at":
            datetime.now(
                timezone.utc
            ),

        }

        run_result = (
            runs_collection.insert_one(
                run_document
            )
        )

        run_id = str(
            run_result.inserted_id
        )

        if missed_full:

            missed_documents = []

            for missed_attack in (
                missed_full[:1000]
            ):

                probability = float(
                    missed_attack.get(
                        "model_probability",
                        0,
                    )
                )

                risk_level = (
                    "LOW"
                    if probability < 30
                    else "MEDIUM"
                )

                missed_documents.append({

                    "run_id":
                    run_id,

                    "user_id":
                    str(
                        request.current_user_id
                    ),

                    "transaction_id":
                    missed_attack.get(
                        "transaction_id"
                    ),

                    "attack":
                    missed_attack,

                    "probability":
                    probability,

                    "risk_level":
                    risk_level,

                    "created_at":
                    datetime.now(
                        timezone.utc
                    ),

                })

            if missed_documents:

                missed_collection.insert_many(
                    missed_documents
                )

        summary = {

            "run_id":
            run_id,

            "attack_type":
            attack_type,

            "total_attacks":
            count,

            "detected":
            detected,

            "missed":
            missed,

            "detection_rate":
            detection_rate,

            "strategy_source":
            strategy_source,

        }

        return jsonify({

            **summary,

            "results":
            results[:100],

            "missed_samples":
            missed_full[:20],

        })

    except ValueError as exc:

        return jsonify({
            "error":
            str(exc)
        }), 400

    except Exception as exc:

        app.logger.exception(
            "Red Team simulation failed"
        )

        return jsonify({
            "error":
            f"Red Team simulation failed: {str(exc)}"
        }), 500


# ============================================================
# ANALYZE RED TEAM RUN
# ============================================================

@app.post("/genai/analyze-run")
@auth_required
def genai_analyze_run():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    run_id = data.get(
        "run_id"
    )

    try:

        if run_id:

            try:

                run_object_id = (
                    ObjectId(
                        run_id
                    )
                )

            except Exception:

                return jsonify({
                    "error":
                    "Invalid run id."
                }), 400

            run = (
                runs_collection.find_one({

                    "_id":
                    run_object_id,

                    "user_id":
                    str(
                        request.current_user_id
                    ),

                })
            )

        else:

            run = (
                runs_collection.find_one(

                    {
                        "user_id":
                        str(
                            request.current_user_id
                        )
                    },

                    sort=[
                        (
                            "created_at",
                            -1,
                        )
                    ],

                )
            )

        if not run:

            return jsonify({
                "error":
                "No Red Team run found yet."
            }), 404

        run_id_string = str(
            run["_id"]
        )

        rows = (
            missed_collection.find({

                "run_id":
                run_id_string

            })
            .sort(
                "created_at",
                1,
            )
            .limit(
                20
            )
        )

        missed_samples = [

            row.get(
                "attack",
                {},
            )

            for row in rows
        ]

        serialized_run = (
            serialize_run(
                run
            )
        )

        analysis = (
            analyze_red_team_run(

                serialized_run,

                missed_samples,

            )
        )

        return jsonify({

            "run":
            serialized_run,

            "analysis":
            analysis,

            "missed_sample_count":
            len(
                missed_samples
            ),

        })

    except PyMongoError as exc:

        app.logger.exception(
            "MongoDB run analysis failed"
        )

        return jsonify({
            "error":
            f"Database error while analyzing run: {str(exc)}"
        }), 500


# ============================================================
# RED TEAM HISTORY
# ============================================================

@app.get("/red-team/history")
@auth_required
def red_team_history():

    try:

        rows = (
            runs_collection.find({

                "user_id":
                str(
                    request.current_user_id
                )

            })
            .sort(
                "created_at",
                -1,
            )
            .limit(
                20
            )
        )

        runs = [

            serialize_run(
                row
            )

            for row in rows
        ]

        return jsonify({

            "runs":
            runs

        })

    except PyMongoError as exc:

        app.logger.exception(
            "MongoDB history failed"
        )

        return jsonify({
            "error":
            f"Database error while loading history: {str(exc)}"
        }), 500


# ============================================================
# MISSED ATTACKS
# ============================================================

@app.get(
    "/red-team/runs/<run_id>/missed"
)
@auth_required
def red_team_missed(run_id):

    try:

        try:

            run_object_id = (
                ObjectId(
                    run_id
                )
            )

        except Exception:

            return jsonify({
                "error":
                "Invalid run id."
            }), 400

        run = (
            runs_collection.find_one({

                "_id":
                run_object_id,

                "user_id":
                str(
                    request.current_user_id
                ),

            })
        )

        if not run:

            return jsonify({
                "error":
                "Run not found."
            }), 404

        rows = (
            missed_collection.find({

                "run_id":
                run_id

            })
            .sort(
                "created_at",
                1,
            )
            .limit(
                100
            )
        )

        missed = []

        for row in rows:

            missed.append({

                "transaction_id":
                row.get(
                    "transaction_id"
                ),

                "transaction":
                row.get(
                    "attack"
                ),

                "probability":
                row.get(
                    "probability"
                ),

                "risk_level":
                row.get(
                    "risk_level"
                ),

            })

        return jsonify({

            "run_id":
            run_id,

            "missed":
            missed,

        })

    except PyMongoError as exc:

        app.logger.exception(
            "MongoDB missed attacks failed"
        )

        return jsonify({
            "error":
            f"Database error while loading missed attacks: {str(exc)}"
        }), 500


# ============================================================
# METRICS
# ============================================================

@app.get("/metrics")
@auth_required
def metrics():

    return jsonify({

        "round_2": {

            "total_attacks":
            5000,

            "detected":
            582,

            "missed":
            4418,

            "detection_rate":
            11.64,

        },

        "round_3": {

            "total_attacks":
            5000,

            "detected":
            4874,

            "missed":
            126,

            "detection_rate":
            97.48,

        },

        "note":
        "These are held-out synthetic adversarial experiment results.",

    })


# ============================================================
# RUN LOCALLY
# ============================================================

if __name__ == "__main__":

    print(
        "Starting Mastercard AI Defense Lab..."
    )

    print(
        "Frontend expected at: http://localhost:5173"
    )

    print(
        "Backend API: http://127.0.0.1:5000"
    )

    print(
        "Database: MongoDB"
    )

    print(
        "MongoDB connected:",
        mongo_health(),
    )

    print(
        "GenAI mode:",
        llm_status()["mode"],
    )

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000,
            )
        ),
        debug=True,
    )
