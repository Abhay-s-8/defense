from typing import Any, Dict, Optional
from services.biometrics_service import biometrics_engine
from services.fraud_service import predict_transaction
from services.gnn_service import gnn_analyzer
from services.feature_store import feature_store


class DefenseTriadEngine:
    """
    Unified Multi-Layer Defense Triad Engine
    Fuses:
      Layer 1: Behavioral Biometrics (Keystroke dynamics, hesitation, coercion detection)
      Layer 2: Real-Time Tabular Engine (Fortified XGBoost V4 + Feature Store)
      Layer 3: Graph Neural Network & Mule Ring Link Analysis (Topology & Smurfing)
    """
    def evaluate_triad(
        self,
        transaction: Dict[str, Any],
        interaction_telemetry: Optional[Dict[str, Any]] = None,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        # 1. Enrich transaction server-side if needed
        enriched_tx = feature_store.enrich_transaction(transaction)
        user_node = sender_id or str(enriched_tx.get("user_id", "ACC_USER_CURRENT"))
        recv_node = receiver_id or str(transaction.get("beneficiary_id") or enriched_tx.get("merchant_category", "MERCHANT_DEFAULT"))
        amount = float(enriched_tx.get("amount", 100.0))

        # ----------------------------------------------------
        # LAYER 1: BEHAVIORAL BIOMETRICS & INTERACTION TELEMETRY
        # ----------------------------------------------------
        layer1_result = biometrics_engine.analyze_interaction_telemetry(interaction_telemetry)
        bio_score = float(layer1_result.get("biometric_risk_score", 10.0))

        # ----------------------------------------------------
        # LAYER 2: XGBOOST TABULAR BEHAVIORAL INFERENCE
        # ----------------------------------------------------
        layer2_result = predict_transaction(enriched_tx)
        xgb_score = float(layer2_result.get("fraud_probability", 5.0))

        # ----------------------------------------------------
        # LAYER 3: GRAPH NETWORK & MULE RING LINK ANALYSIS
        # ----------------------------------------------------
        layer3_result = gnn_analyzer.evaluate_network_risk(user_node, recv_node, amount)
        gnn_score = float(layer3_result.get("network_mule_risk_score", 8.0))

        # ----------------------------------------------------
        # UNIFIED FUSION RISK SCORING (Ensemble Weights: 20% Bio + 50% XGB + 30% GNN)
        # ----------------------------------------------------
        composite_risk = round((0.20 * bio_score) + (0.50 * xgb_score) + (0.30 * gnn_score), 2)
        composite_risk = max(0.0, min(100.0, composite_risk))

        # Differentiated Policy Actions
        if layer1_result.get("coercion_detected"):
            decision_tier = "COERCION_SAFETY_INTERVENTION"
            policy_action = "ACTIVE_SCAM_INTERVENTION: Potential Digital Arrest / Vishing Scam. Alert user with scam warning and introduce cooling delay."
            status_color = "#f59e0b"  # Amber
        elif layer3_result.get("mule_syndicate_detected"):
            decision_tier = "MULE_SYNDICATE_FREEZE"
            policy_action = "MULE_NETWORK_BLOCK: Destination account flagged in multi-hop laundering topology. Freeze fund outflow immediately."
            status_color = "#dc2626"  # Deep Red
        elif composite_risk >= 70.0:
            decision_tier = "BLOCK_FRAUDULENT_TRANSACTION"
            policy_action = "HARD_DECLINE: Extreme multi-layer anomalous velocity and risk vectors detected."
            status_color = "#ef4444"  # Red
        elif composite_risk >= 35.0 or layer2_result.get("risk_level") in ["HIGH", "MEDIUM"]:
            decision_tier = "STEP_UP_BIOMETRIC_CHALLENGE"
            policy_action = "STEP_UP_2FA: Moderate behavioral variance. Trigger FIDO2 WebAuthn / Biometric Passkey challenge."
            status_color = "#eab308"  # Yellow
        else:
            decision_tier = "FRICTIONLESS_APPROVAL"
            policy_action = "ALLOW: Frictionless approval granted across all 3 defense layers."
            status_color = "#10b981"  # Emerald

        # Unified Multi-Layer Defense Summary
        summary_points = []
        if layer1_result.get("signals"):
            summary_points.append(f"Layer 1 (Biometrics): {layer1_result['signals'][0]}")
        if layer2_result.get("mathematical_contributions", {}).get("top_positive"):
            top_xgb = layer2_result["mathematical_contributions"]["top_positive"][0]
            summary_points.append(f"Layer 2 (XGBoost): [+] {top_xgb['feature'].replace('_', ' ').title()} (+{top_xgb['weight']})")
        if layer3_result.get("signals"):
            summary_points.append(f"Layer 3 (GNN Graph): {layer3_result['signals'][0]}")

        return {
            "composite_risk_score": composite_risk,
            "decision_tier": decision_tier,
            "policy_action": policy_action,
            "status_color": status_color,
            "triad_breakdown": {
                "layer_1_biometrics": {
                    "score": bio_score,
                    "level": layer1_result["risk_level"],
                    "coercion_detected": layer1_result["coercion_detected"],
                    "bot_detected": layer1_result["bot_automation_detected"],
                    "signals": layer1_result["signals"],
                    "weight_in_fusion": "20%",
                },
                "layer_2_xgboost": {
                    "score": xgb_score,
                    "prediction": layer2_result["prediction"],
                    "level": layer2_result["risk_level"],
                    "mathematical_drivers": layer2_result.get("mathematical_contributions", {}).get("top_positive", []),
                    "weight_in_fusion": "50%",
                },
                "layer_3_gnn_network": {
                    "score": gnn_score,
                    "level": layer3_result["risk_level"],
                    "mule_syndicate_detected": layer3_result["mule_syndicate_detected"],
                    "cyclic_flow_detected": layer3_result["cyclic_flow_detected"],
                    "signals": layer3_result["signals"],
                    "weight_in_fusion": "30%",
                },
            },
            "multi_layer_summary": summary_points,
            "server_enriched_signals": enriched_tx,
        }


# Global singleton
defense_triad = DefenseTriadEngine()
