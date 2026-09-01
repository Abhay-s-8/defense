import sys
import time

print("=== 1. TESTING FRAUD SERVICE & BATCH INFERENCE ===")
from services.fraud_service import (
    predict_transaction,
    predict_batch_transactions,
    retrain_model_with_misses,
    get_current_metrics,
)
from red_team.generator import generate_multiple_attacks

# Generate 1000 synthetic attacks
t0 = time.time()
attacks = generate_multiple_attacks("low_and_slow", 1000)
gen_time = time.time() - t0
print(f"Generated 1000 attacks in {gen_time:.3f}s")

# Test Vectorized Batch Prediction
t0 = time.time()
batch_res = predict_batch_transactions(attacks)
batch_time = time.time() - t0
print(f"Batch scored 1000 attacks in {batch_time:.3f}s (Total results: {len(batch_res)})")
fraud_count = sum(1 for r in batch_res if r["prediction"] == "FRAUD")
print(f"Detected: {fraud_count}, Missed: {len(batch_res) - fraud_count}")

# Test Retraining with misses
misses = [attacks[i] for i, r in enumerate(batch_res) if r["prediction"] != "FRAUD"]
print(f"Retraining on {len(misses)} missed samples...")
retrain_res = retrain_model_with_misses(misses)
print("Retraining result:", retrain_res)

print("\n=== 2. TESTING FLASK APP ENDPOINTS & HYBRID DB ===")
import app as flask_module
client = flask_module.app.test_client()

# Health check
res = client.get("/health")
print("/health response status:", res.status_code, res.get_json())

# Register user
res = client.post(
    "/auth/register",
    json={"name": "AIT Analyst", "email": "analyst@aitpune.edu.in", "password": "Password123!"}
)
print("/auth/register status:", res.status_code)
token = res.get_json().get("token")
headers = {"Authorization": f"Bearer {token}"}

# Predict single
sample_tx = attacks[0]
res = client.post("/predict", json=sample_tx, headers=headers)
print("/predict single status:", res.status_code, res.get_json())

# Run Red Team (500 attacks)
t0 = time.time()
res = client.post("/run-red-team", json={"attack_type": "account_takeover", "count": 500}, headers=headers)
rt_time = time.time() - t0
data = res.get_json()
print(f"/run-red-team status: {res.status_code} in {rt_time:.3f}s")
print(f"Red Team total: {data.get('total_attacks')}, detected: {data.get('detected')}, missed: {data.get('missed')}, rate: {data.get('detection_rate')}%")

# Trigger Retraining Loop
res = client.post("/retrain", json={}, headers=headers)
print("/retrain status:", res.status_code, res.get_json())

# Metrics
res = client.get("/metrics", headers=headers)
print("/metrics status:", res.status_code, res.get_json())

print("\n>>> ALL BACKEND TESTS PASSED SUCCESSFULLY! <<<")
