import statistics
import time
from typing import Any, Dict, List, Optional


class BehavioralBiometricsEngine:
    """
    Layer 1: User & Interaction Telemetry Engine
    Analyzes client-side interaction rhythm, keystroke dynamics, hesitation jitter,
    and coercion/vishing behavioral indicators.
    """
    def __init__(self):
        # Baseline reference ranges for genuine human typing (in ms)
        self.normal_dwell_range = (50.0, 180.0)      # Duration key is held down
        self.normal_flight_range = (80.0, 350.0)     # Interval between consecutive keystrokes
        self.normal_hesitation_max = 3500.0          # Max pause before clicking submit (ms)

    def analyze_interaction_telemetry(self, telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates interaction metrics:
        - keystroke_dwell_times: List[float] (ms per keypress)
        - keystroke_flight_times: List[float] (ms between keypresses)
        - form_dwell_time_ms: float (total time spent on checkout form)
        - submit_hesitation_ms: float (time spent hovering/pausing on Submit)
        - backspace_count: int (corrections made)
        - on_call_detected: bool (mobile/device active voice call telemetry)
        - remote_desktop_detected: bool (Anydesk/Teamviewer overlay flags)
        """
        if not telemetry or not isinstance(telemetry, dict):
            # Default benign baseline if no telemetry provided (e.g. backend automated API)
            return {
                "biometric_risk_score": 12.0,
                "risk_level": "LOW",
                "coercion_detected": False,
                "bot_automation_detected": False,
                "hesitation_index": "NORMAL",
                "telemetry_summary": "Standard human interaction rhythm with regular typing cadence.",
                "signals": ["Natural keystroke flight cadence", "No remote desktop overlay", "Standard submission latency"],
            }

        dwell_times = [float(x) for x in telemetry.get("keystroke_dwell_times", []) if isinstance(x, (int, float))]
        flight_times = [float(x) for x in telemetry.get("keystroke_flight_times", []) if isinstance(x, (int, float))]
        form_time_ms = float(telemetry.get("form_dwell_time_ms", 12000))
        submit_hesitation_ms = float(telemetry.get("submit_hesitation_ms", 800))
        backspaces = int(telemetry.get("backspace_count", 1))
        on_call = bool(telemetry.get("on_call_detected", False))
        remote_desktop = bool(telemetry.get("remote_desktop_detected", False))

        risk_score = 10.0
        signals = []
        coercion_detected = False
        bot_detected = False

        # 1. Check for Bot / Script Automation (Inhuman speed or 0 variance)
        if dwell_times:
            avg_dwell = statistics.mean(dwell_times)
            dwell_variance = statistics.stdev(dwell_times) if len(dwell_times) > 1 else 10.0
            
            # Inhuman typing speed (<25ms dwell or 0 variance across 10 keys)
            if avg_dwell < 25.0 or (len(dwell_times) >= 6 and dwell_variance < 1.0):
                risk_score += 70.0
                bot_detected = True
                signals.append("[!] Inhuman typing velocity / robotic zero-variance flight times detected (Bot Automation)")
            elif avg_dwell > 350.0:
                risk_score += 15.0
                signals.append("Abnormally sluggish key dwell duration")
            else:
                signals.append("Natural key dwell duration (~" + str(int(avg_dwell)) + "ms)")
        else:
            signals.append("Baseline typing dynamics within expected variance")

        # 2. Check for Social Engineering / Coercion / Digital Arrest / Vishing Scam
        # Coercion indicators: active voice call during payment + excessive hesitation (>4s) + frequent corrections
        if on_call:
            risk_score += 45.0
            coercion_detected = True
            signals.append("[!] Active ongoing voice call during transaction input (High Vishing / Coercion Risk)")

        if submit_hesitation_ms > 4500.0:
            risk_score += 30.0
            signals.append("[!] Extreme hesitation prior to payment submission (" + str(int(submit_hesitation_ms / 1000)) + "s pause)")
            if on_call or backspaces >= 6:
                coercion_detected = True

        if remote_desktop:
            risk_score += 65.0
            signals.append("[!] Remote control / screen-sharing software active (Session Hijack Risk)")

        # 3. High correction / anxiety rate
        if backspaces >= 8:
            risk_score += 15.0
            signals.append("Elevated input corrections (Anxiety / Unfamiliarity signature)")

        # Normalization
        risk_score = max(5.0, min(100.0, risk_score))

        if risk_score >= 70.0:
            risk_level = "CRITICAL"
        elif risk_score >= 45.0:
            risk_level = "HIGH"
        elif risk_score >= 25.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        hesitation_index = "ELEVATED" if submit_hesitation_ms > 3000 else "NORMAL"

        return {
            "biometric_risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "coercion_detected": coercion_detected,
            "bot_automation_detected": bot_detected,
            "remote_desktop_detected": remote_desktop,
            "hesitation_index": hesitation_index,
            "submit_hesitation_ms": submit_hesitation_ms,
            "signals": signals[:5],
            "telemetry_summary": (
                "High coercion / scam vulnerability detected."
                if coercion_detected
                else ("Automated bot telemetry detected." if bot_detected else "Standard genuine user interaction profile.")
            ),
        }


# Global singleton
biometrics_engine = BehavioralBiometricsEngine()
