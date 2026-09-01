import sys
import time

print("==================================================")
print("TESTING 3-LAYER MULTI-DIMENSIONAL DEFENSE TRIAD")
print("==================================================")

# ----------------------------------------------------
# 1. TEST LAYER 1: BEHAVIORAL BIOMETRICS & COERCION
# ----------------------------------------------------
print("\n[LAYER 1] Testing Behavioral Biometrics Telemetry Engine...")
from services.biometrics_service import biometrics_engine

# A. Normal user typing
normal_telemetry = {
    "keystroke_dwell_times": [95.0, 110.0, 105.0, 120.0, 88.0, 115.0],
    "keystroke_flight_times": [150.0, 180.0, 220.0, 160.0, 190.0],
    "submit_hesitation_ms": 650.0,
    "backspace_count": 1,
    "on_call_detected": False,
}
res_normal = biometrics_engine.analyze_interaction_telemetry(normal_telemetry)
print("Normal Biometric Score:", res_normal["biometric_risk_score"], f"({res_normal['risk_level']})")
assert res_normal["risk_level"] == "LOW"

# B. Coercion / Vishing Scam (Digital Arrest)
coercion_telemetry = {
    "keystroke_dwell_times": [160.0, 190.0, 140.0, 220.0],
    "keystroke_flight_times": [350.0, 520.0, 480.0],
    "submit_hesitation_ms": 6800.0,  # 6.8s hesitation
    "backspace_count": 9,
    "on_call_detected": True,        # Active voice call during payment
}
res_coercion = biometrics_engine.analyze_interaction_telemetry(coercion_telemetry)
print("Coercion Biometric Score:", res_coercion["biometric_risk_score"], f"({res_coercion['risk_level']})")
print("Coercion Detected:", res_coercion["coercion_detected"])
print("Signals:", res_coercion["signals"])
assert res_coercion["coercion_detected"] is True
assert res_coercion["biometric_risk_score"] >= 70.0
print("[PASS] Layer 1 (Behavioral Biometrics & Coercion Engine) verified!")

# ----------------------------------------------------
# 2. TEST LAYER 3: GNN GRAPH & MULE TOPOLOGY
# ----------------------------------------------------
print("\n[LAYER 3] Testing GNN & Graph Mule Topology Analyzer...")
from services.gnn_service import gnn_analyzer

# A. Cyclic laundering flow detection (NodeX -> NodeY -> NodeZ -> NodeX)
gnn_analyzer.add_transaction("ACC_RING_1", "ACC_RING_2", 35000)
gnn_analyzer.add_transaction("ACC_RING_2", "ACC_RING_3", 34500)
gnn_analyzer.add_transaction("ACC_RING_3", "ACC_RING_1", 34000)

res_graph = gnn_analyzer.evaluate_network_risk("ACC_RING_1", "ACC_RING_2", 35000)
print("Network Mule Risk Score:", res_graph["network_mule_risk_score"], f"({res_graph['risk_level']})")
print("Cyclic Laundering Detected:", res_graph["cyclic_flow_detected"])
print("Cycle Path:", res_graph["cycle_path"])
assert res_graph["cyclic_flow_detected"] is True
assert res_graph["mule_syndicate_detected"] is True

# B. Export Topology
topology = gnn_analyzer.get_network_topology()
print(f"Topology Graph contains {topology['total_nodes']} nodes and {topology['total_edges']} directed transaction edges.")
assert topology["total_nodes"] > 5
assert topology["total_edges"] > 5
print("[PASS] Layer 3 (GNN Graph & Mule Network Analyzer) verified!")

# ----------------------------------------------------
# 3. TEST UNIFIED DEFENSE TRIAD FUSION ENGINE
# ----------------------------------------------------
print("\n[TRIAD FUSION] Testing Unified 3-Layer Fusion Engine...")
from services.defense_triad import defense_triad

# Case 1: Normal Frictionless Payment
tx_clean = {
    "amount": 1500,
    "payment_channel": "UPI",
    "merchant_category": "FOOD",
    "country": "IN",
    "user_id": "ACC_USER_CLEAN",
}
eval_clean = defense_triad.evaluate_triad(tx_clean, normal_telemetry, "ACC_USER_CLEAN", "MERCHANT_SWIGGY")
print(f"Clean Transaction -> Composite Risk: {eval_clean['composite_risk_score']}%, Tier: {eval_clean['decision_tier']}")
assert eval_clean["decision_tier"] == "FRICTIONLESS_APPROVAL"

# Case 2: Coerced Scam Payment
tx_coerced = {
    "amount": 75000,
    "payment_channel": "BANK_TRANSFER",
    "merchant_category": "OTHER",
    "country": "IN",
    "user_id": "VICTIM_USER_99",
}
eval_coerced = defense_triad.evaluate_triad(tx_coerced, coercion_telemetry, "VICTIM_USER_99", "MULE_RECV_1")
print(f"Coerced Payment -> Composite Risk: {eval_coerced['composite_risk_score']}%, Tier: {eval_coerced['decision_tier']}")
print("Policy Directive:", eval_coerced["policy_action"])
assert eval_coerced["decision_tier"] == "COERCION_SAFETY_INTERVENTION"

print("[PASS] Unified Defense Triad Fusion Engine verified!")

# ----------------------------------------------------
# 4. TEST FLASK API ENDPOINTS
# ----------------------------------------------------
print("\n[API ENDPOINTS] Testing Triad Endpoints via Flask Test Client...")
import app as flask_app
client = flask_app.app.test_client()

# Register Analyst
reg_res = client.post(
    "/auth/register",
    json={"name": "Triad Analyst", "email": "triad@aitpune.edu.in", "password": "Password123!"},
    headers={"X-Forwarded-For": "192.168.10.1"},
)
token = reg_res.get_json().get("token")
headers = {
    "Authorization": f"Bearer {token}",
    "X-Forwarded-For": "192.168.10.1",
}

# POST /predict/triad
triad_req = {
    "transaction": tx_clean,
    "interaction_telemetry": normal_telemetry,
    "sender_id": "ACC_USER_CLEAN",
    "receiver_id": "MERCHANT_SWIGGY",
}
res_triad = client.post("/predict/triad", json=triad_req, headers=headers)
print("POST /predict/triad status:", res_triad.status_code)
triad_data = res_triad.get_json()
print("Triad Decision Tier:", triad_data.get("decision_tier"))
assert res_triad.status_code == 200
assert "triad_breakdown" in triad_data

# GET /network/topology
res_topo = client.get("/network/topology", headers=headers)
print("GET /network/topology status:", res_topo.status_code)
topo_data = res_topo.get_json()
print("Topology Total Nodes:", topo_data.get("total_nodes"))
assert res_topo.status_code == 200
assert topo_data.get("total_nodes") > 0

# POST /simulate/mule-syndicate
res_sim = client.post("/simulate/mule-syndicate", headers=headers)
print("POST /simulate/mule-syndicate status:", res_sim.status_code)
sim_data = res_sim.get_json()
print("Simulated Syndicate ID:", sim_data.get("syndicate_cluster_id"))
assert res_sim.status_code == 200
assert "syndicate_cluster_id" in sim_data

print("\n==================================================")
print(">>> ALL 3 DEFENSE TRIAD LAYERS VERIFIED 100%! <<<")
print("==================================================")
