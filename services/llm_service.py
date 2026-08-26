import json
import os
import re
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").strip().rstrip("/")
LLM_MODEL = os.environ.get("LLM_MODEL", "").strip()
LLM_PROVIDER_NAME = os.environ.get("LLM_PROVIDER_NAME", "OpenAI-compatible LLM").strip()
LLM_TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT_SECONDS", "45"))


def llm_status() -> Dict[str, Any]:
    configured = bool(LLM_BASE_URL and LLM_MODEL)
    return {
        "configured": configured,
        "mode": "remote_llm" if configured else "local_fallback",
        "provider": LLM_PROVIDER_NAME if configured else "Built-in deterministic fallback",
        "model": LLM_MODEL if configured else "rules-v1",
        "note": (
            "Remote LLM is configured."
            if configured
            else "Set LLM_BASE_URL and LLM_MODEL (and LLM_API_KEY when required) to enable the remote LLM."
        ),
    }


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain JSON")
    return json.loads(match.group(0))


def _call_remote_llm(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    if not (LLM_BASE_URL and LLM_MODEL):
        raise RuntimeError("Remote LLM is not configured")

    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    response = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=LLM_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"]["content"]
    return _extract_json(text)


def _clamp(value: Any, low: float, high: float, default: float) -> float:
    try:
        return max(low, min(high, float(value)))
    except Exception:
        return default


def _int_clamp(value: Any, low: int, high: int, default: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except Exception:
        return default


def _sanitize_plan(raw: Dict[str, Any], attack_type: str, difficulty: str) -> Dict[str, Any]:
    defaults = _fallback_attack_plan(attack_type, "", difficulty)
    params = raw.get("parameters", {}) if isinstance(raw.get("parameters"), dict) else {}
    dparams = defaults["parameters"]

    plan = {
        "attack_type": attack_type,
        "title": str(raw.get("title") or defaults["title"])[:100],
        "strategy": str(raw.get("strategy") or defaults["strategy"])[:600],
        "why_it_is_hard": str(raw.get("why_it_is_hard") or defaults["why_it_is_hard"])[:600],
        "difficulty": difficulty,
        "parameters": {
            "amount_ratio_min": _clamp(params.get("amount_ratio_min"), 0.05, 8.0, dparams["amount_ratio_min"]),
            "amount_ratio_max": _clamp(params.get("amount_ratio_max"), 0.05, 8.0, dparams["amount_ratio_max"]),
            "ip_risk_min": _clamp(params.get("ip_risk_min"), 0, 100, dparams["ip_risk_min"]),
            "ip_risk_max": _clamp(params.get("ip_risk_max"), 0, 100, dparams["ip_risk_max"]),
            "velocity_min": _int_clamp(params.get("velocity_min"), 1, 50, dparams["velocity_min"]),
            "velocity_max": _int_clamp(params.get("velocity_max"), 1, 50, dparams["velocity_max"]),
            "failed_attempts_min": _int_clamp(params.get("failed_attempts_min"), 0, 20, dparams["failed_attempts_min"]),
            "failed_attempts_max": _int_clamp(params.get("failed_attempts_max"), 0, 20, dparams["failed_attempts_max"]),
            "new_device_probability": _clamp(params.get("new_device_probability"), 0, 1, dparams["new_device_probability"]),
            "new_location_probability": _clamp(params.get("new_location_probability"), 0, 1, dparams["new_location_probability"]),
            "new_beneficiary_probability": _clamp(params.get("new_beneficiary_probability"), 0, 1, dparams["new_beneficiary_probability"]),
            "hour_min": _int_clamp(params.get("hour_min"), 0, 23, dparams["hour_min"]),
            "hour_max": _int_clamp(params.get("hour_max"), 0, 23, dparams["hour_max"]),
        },
    }

    p = plan["parameters"]
    for lo, hi in [
        ("amount_ratio_min", "amount_ratio_max"),
        ("ip_risk_min", "ip_risk_max"),
        ("velocity_min", "velocity_max"),
        ("failed_attempts_min", "failed_attempts_max"),
        ("hour_min", "hour_max"),
    ]:
        if p[lo] > p[hi]:
            p[lo], p[hi] = p[hi], p[lo]

    return plan


def _fallback_attack_plan(attack_type: str, objective: str, difficulty: str) -> Dict[str, Any]:
    presets = {
        "account_takeover": {
            "title": "Adaptive account takeover",
            "strategy": "Simulate a compromised account using a fresh device or location, elevated IP risk, and an amount above the customer's normal range.",
            "why_it_is_hard": "The scenario mixes strong takeover indicators with otherwise realistic account history so the model must use several signals together.",
            "parameters": dict(amount_ratio_min=1.4, amount_ratio_max=3.2, ip_risk_min=55, ip_risk_max=92, velocity_min=3, velocity_max=9, failed_attempts_min=1, failed_attempts_max=5, new_device_probability=0.85, new_location_probability=0.65, new_beneficiary_probability=0.55, hour_min=0, hour_max=23),
        },
        "card_testing": {
            "title": "Rapid low-value card testing",
            "strategy": "Generate repeated low-value card attempts with high short-window velocity, failed attempts, and elevated IP risk.",
            "why_it_is_hard": "Each payment is small, so the detector must recognize the behavioral pattern rather than relying on amount alone.",
            "parameters": dict(amount_ratio_min=0.01, amount_ratio_max=0.15, ip_risk_min=65, ip_risk_max=98, velocity_min=10, velocity_max=30, failed_attempts_min=4, failed_attempts_max=14, new_device_probability=0.5, new_location_probability=0.45, new_beneficiary_probability=0.0, hour_min=0, hour_max=23),
        },
        "mule_activity": {
            "title": "Mule-style fund movement",
            "strategy": "Move higher-than-normal value toward a new beneficiary with moderate-to-high transaction velocity and medium IP risk.",
            "why_it_is_hard": "The account can appear established while the beneficiary relationship and flow pattern are abnormal.",
            "parameters": dict(amount_ratio_min=1.5, amount_ratio_max=4.5, ip_risk_min=35, ip_risk_max=78, velocity_min=4, velocity_max=12, failed_attempts_min=0, failed_attempts_max=2, new_device_probability=0.25, new_location_probability=0.25, new_beneficiary_probability=0.95, hour_min=0, hour_max=23),
        },
        "low_and_slow": {
            "title": "Stealth low-and-slow campaign",
            "strategy": "Keep amounts close to historical behavior, use an established device and familiar location, keep velocity low, and introduce only one subtle anomaly at a time.",
            "why_it_is_hard": "Most features look legitimate, so only weak combinations such as a younger beneficiary or moderate IP risk separate the attack from normal activity.",
            "parameters": dict(amount_ratio_min=0.85, amount_ratio_max=1.35, ip_risk_min=12, ip_risk_max=40, velocity_min=1, velocity_max=3, failed_attempts_min=0, failed_attempts_max=1, new_device_probability=0.05, new_location_probability=0.08, new_beneficiary_probability=0.25, hour_min=8, hour_max=21),
        },
    }
    base = presets.get(attack_type, presets["low_and_slow"])
    base = json.loads(json.dumps(base))
    base["attack_type"] = attack_type
    base["difficulty"] = difficulty
    if objective:
        base["strategy"] += f" Analyst objective: {objective[:250]}"

    if difficulty == "easy":
        base["parameters"]["ip_risk_min"] = min(90, base["parameters"]["ip_risk_min"] + 15)
        base["parameters"]["new_device_probability"] = min(1.0, base["parameters"]["new_device_probability"] + 0.15)
    elif difficulty == "hard":
        base["parameters"]["ip_risk_max"] = max(base["parameters"]["ip_risk_min"], base["parameters"]["ip_risk_max"] - 12)
        base["parameters"]["new_device_probability"] = max(0.0, base["parameters"]["new_device_probability"] - 0.10)
        base["parameters"]["new_location_probability"] = max(0.0, base["parameters"]["new_location_probability"] - 0.10)

    return base


def generate_attack_plan(attack_type: str, objective: str = "", difficulty: str = "hard", previous_run: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    attack_type = attack_type if attack_type in {"account_takeover", "card_testing", "mule_activity", "low_and_slow"} else "low_and_slow"
    difficulty = difficulty if difficulty in {"easy", "medium", "hard"} else "hard"

    if not (LLM_BASE_URL and LLM_MODEL):
        plan = _fallback_attack_plan(attack_type, objective, difficulty)
        plan["source"] = "local_fallback"
        return plan

    system_prompt = """
You are a defensive payment-security Red Team planner working only in a synthetic lab.
Create a high-level transaction-behavior scenario for testing a fraud classifier.
Do not provide instructions for stealing credentials, bypassing real payment controls, or committing real fraud.
Return JSON only with: title, strategy, why_it_is_hard, parameters.
parameters must contain numeric values for amount_ratio_min, amount_ratio_max, ip_risk_min, ip_risk_max,
velocity_min, velocity_max, failed_attempts_min, failed_attempts_max, new_device_probability,
new_location_probability, new_beneficiary_probability, hour_min, hour_max.
""".strip()

    user_prompt = json.dumps({
        "attack_type": attack_type,
        "objective": objective,
        "difficulty": difficulty,
        "previous_run_summary": previous_run or {},
    })

    try:
        raw = _call_remote_llm(system_prompt, user_prompt)
        plan = _sanitize_plan(raw, attack_type, difficulty)
        plan["source"] = "remote_llm"
        return plan
    except Exception as exc:
        plan = _fallback_attack_plan(attack_type, objective, difficulty)
        plan["source"] = "local_fallback"
        plan["fallback_reason"] = str(exc)[:250]
        return plan


def _signal_summary(transaction: Dict[str, Any]) -> List[str]:
    signals = []
    amount = float(transaction.get("amount", 0) or 0)
    avg = float(transaction.get("avg_amount_30d", 0) or 0)
    ratio = amount / max(avg, 1)

    if ratio >= 2.0:
        signals.append(f"amount is {ratio:.1f}x the 30-day average")
    elif ratio <= 1.3:
        signals.append("amount is close to the normal spending range")

    if int(transaction.get("new_device", 0) or 0):
        signals.append("a new device is being used")
    if int(transaction.get("new_location", 0) or 0):
        signals.append("the location is new")
    if int(transaction.get("new_beneficiary", 0) or 0):
        signals.append("the beneficiary is new")

    velocity = int(transaction.get("transaction_velocity_5m", 0) or 0)
    if velocity >= 6:
        signals.append(f"transaction velocity is high ({velocity} in 5 minutes)")
    elif velocity <= 2:
        signals.append("short-window transaction velocity is low")

    failed = int(transaction.get("failed_attempts_1h", 0) or 0)
    if failed >= 3:
        signals.append(f"there are {failed} failed attempts in the last hour")

    ip_risk = float(transaction.get("ip_risk_score", 0) or 0)
    if ip_risk >= 70:
        signals.append(f"IP risk is high ({ip_risk:.0f})")
    elif ip_risk <= 20:
        signals.append(f"IP risk is low ({ip_risk:.0f})")

    return signals[:6]


def explain_prediction(transaction: Dict[str, Any], model_result: Dict[str, Any]) -> Dict[str, Any]:
    if LLM_BASE_URL and LLM_MODEL:
        system_prompt = """
You are a payment-fraud analyst. Explain a model prediction using only the supplied behavioral features and model output.
Do not claim causality or reveal hidden model internals. Return JSON only with summary, key_signals (array), and recommended_action.
Keep it concise and defensive.
""".strip()
        try:
            raw = _call_remote_llm(system_prompt, json.dumps({"transaction": transaction, "model_result": model_result}))
            return {
                "summary": str(raw.get("summary", ""))[:700],
                "key_signals": [str(x)[:180] for x in raw.get("key_signals", [])[:6]],
                "recommended_action": str(raw.get("recommended_action", ""))[:400],
                "source": "remote_llm",
            }
        except Exception:
            pass

    signals = _signal_summary(transaction)
    probability = float(model_result.get("fraud_probability", 0) or 0)
    prediction = model_result.get("prediction", "UNKNOWN")
    if prediction == "FRAUD":
        action = "Review or step-up authenticate the transaction before approval."
        summary = f"The model marked this transaction as {prediction} with {probability:.2f}% fraud probability because several behavioral signals are unusual together."
    else:
        action = "Allow normal processing while keeping standard monitoring active."
        summary = f"The model marked this transaction as {prediction} with {probability:.2f}% fraud probability because most observed behavior is consistent with normal activity."

    return {"summary": summary, "key_signals": signals, "recommended_action": action, "source": "local_fallback"}


def analyze_red_team_run(summary: Dict[str, Any], missed_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    if LLM_BASE_URL and LLM_MODEL:
        system_prompt = """
You are a defensive payment-security analyst. Review a synthetic Red Team simulation summary and examples that the fraud model missed.
Return JSON only with: finding, likely_weaknesses (array), next_test (string), retraining_note (string).
Do not provide real-world fraud instructions. Focus on model evaluation and safe synthetic testing.
""".strip()
        try:
            raw = _call_remote_llm(system_prompt, json.dumps({"summary": summary, "missed_samples": missed_samples[:8]}))
            return {
                "finding": str(raw.get("finding", ""))[:700],
                "likely_weaknesses": [str(x)[:200] for x in raw.get("likely_weaknesses", [])[:6]],
                "next_test": str(raw.get("next_test", ""))[:500],
                "retraining_note": str(raw.get("retraining_note", ""))[:500],
                "source": "remote_llm",
            }
        except Exception:
            pass

    total = int(summary.get("total_attacks", 0) or 0)
    missed = int(summary.get("missed", 0) or 0)
    rate = float(summary.get("detection_rate", 0) or 0)
    attack_type = summary.get("attack_type", "unknown")
    weaknesses = []
    if missed_samples:
        avg_ip = sum(float(x.get("ip_risk_score", 0) or 0) for x in missed_samples) / len(missed_samples)
        avg_vel = sum(float(x.get("transaction_velocity_5m", 0) or 0) for x in missed_samples) / len(missed_samples)
        new_dev = sum(int(x.get("new_device", 0) or 0) for x in missed_samples) / len(missed_samples)
        weaknesses.append(f"Missed samples averaged IP risk {avg_ip:.1f} and velocity {avg_vel:.1f}.")
        if new_dev < 0.3:
            weaknesses.append("Many missed attacks used established devices, reducing obvious takeover signals.")
    if not weaknesses:
        weaknesses.append("No missed sample details were available for deeper analysis.")

    return {
        "finding": f"The model detected {rate:.2f}% of {total} synthetic {attack_type} attacks and missed {missed}.",
        "likely_weaknesses": weaknesses,
        "next_test": "Generate a fresh unseen attack batch that preserves the missed samples' subtle behavior but changes random values and user contexts.",
        "retraining_note": "Missed attacks can be curated for adversarial retraining, but evaluation must use a different unseen attack set afterward.",
        "source": "local_fallback",
    }
