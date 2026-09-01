import time
from collections import defaultdict
from datetime import datetime, timezone
import hashlib


class RealTimeFeatureStore:
    """
    Simulates a production real-time banking feature store (e.g. Redis / Feast / Flink)
    that computes behavioral aggregates server-side to prevent client-side feature injection.
    """
    def __init__(self):
        # User transaction timestamps: user_id -> list of float timestamps
        self.user_tx_timestamps = defaultdict(list)
        # User amounts: user_id -> list of (timestamp, amount)
        self.user_tx_amounts = defaultdict(list)
        # User devices: user_id -> dict(device_id -> first_seen_timestamp)
        self.user_devices = defaultdict(dict)
        # User locations/countries: user_id -> set of countries seen
        self.user_locations = defaultdict(set)
        # User beneficiaries: user_id -> dict(beneficiary_id -> first_seen_timestamp)
        self.user_beneficiaries = defaultdict(dict)
        # User failed attempts: user_id -> list of float timestamps
        self.user_failed_attempts = defaultdict(list)
        # User account created timestamps
        self.user_account_created = {}
        # Known IP risk cache
        self.ip_reputation_cache = {}

    def record_failed_attempt(self, user_id):
        now = time.time()
        self.user_failed_attempts[user_id].append(now)

    def record_successful_transaction(self, user_id, amount, device_id=None, country=None, beneficiary_id=None):
        now = time.time()
        self.user_tx_timestamps[user_id].append(now)
        self.user_tx_amounts[user_id].append((now, float(amount)))

        if device_id:
            if device_id not in self.user_devices[user_id]:
                self.user_devices[user_id][device_id] = now

        if country:
            self.user_locations[user_id].add(country)

        if beneficiary_id:
            if beneficiary_id not in self.user_beneficiaries[user_id]:
                self.user_beneficiaries[user_id][beneficiary_id] = now

    def _get_ip_risk_score(self, ip_address):
        """
        Simulates threat-intelligence IP reputation lookup.
        """
        if not ip_address:
            return 15.0
        if ip_address in self.ip_reputation_cache:
            return self.ip_reputation_cache[ip_address]
        
        # Deterministic simulation hash for demo IP addresses
        h = int(hashlib.md5(ip_address.encode('utf-8')).hexdigest()[:4], 16)
        # Most IPs have low risk (5-25), suspicious ones have 60-95
        score = (h % 35) + 5.0
        if "vpn" in ip_address.lower() or "tor" in ip_address.lower() or "proxy" in ip_address.lower():
            score = 88.5
        self.ip_reputation_cache[ip_address] = score
        return score

    def enrich_transaction(self, raw_tx):
        """
        Takes a raw transaction payload (which may only have user_id, amount,
        payment_channel, merchant_category, country, device_id, etc.) and
        derives the exact behavioral feature vector server-side.
        """
        now = time.time()
        now_dt = datetime.now(timezone.utc)
        user_id = str(raw_tx.get("user_id", "GUEST_USER"))
        amount = float(raw_tx.get("amount", 100.0))
        device_id = str(raw_tx.get("device_id", "DEV_DEFAULT"))
        country = str(raw_tx.get("country", "IN"))
        beneficiary_id = str(raw_tx.get("beneficiary_id", "BENEFICIARY_DEFAULT")) if raw_tx.get("beneficiary_id") else None

        # 1. Rolling 5-minute velocity
        five_min_ago = now - 300
        recent_txs = [t for t in self.user_tx_timestamps[user_id] if t >= five_min_ago]
        velocity_5m = max(1, len(recent_txs) + 1 if raw_tx.get("transaction_velocity_5m") is None else int(raw_tx.get("transaction_velocity_5m")))

        # 2. Failed attempts in last 1 hour
        one_hour_ago = now - 3600
        recent_fails = [t for t in self.user_failed_attempts[user_id] if t >= one_hour_ago]
        failed_attempts = len(recent_fails) if raw_tx.get("failed_attempts_1h") is None else int(raw_tx.get("failed_attempts_1h"))

        # 3. 30-Day Rolling Average Amount & Deviation
        thirty_days_ago = now - (30 * 86400)
        recent_amounts = [amt for t, amt in self.user_tx_amounts[user_id] if t >= thirty_days_ago]
        if raw_tx.get("avg_amount_30d") is not None:
            avg_amount_30d = float(raw_tx.get("avg_amount_30d"))
        elif recent_amounts:
            avg_amount_30d = sum(recent_amounts) / len(recent_amounts)
        else:
            avg_amount_30d = max(amount * 0.8, 500.0)

        amount_deviation = round(amount / max(avg_amount_30d, 1.0), 3)

        # 4. Device history
        if raw_tx.get("new_device") is not None:
            new_device = int(raw_tx.get("new_device"))
        else:
            new_device = 1 if (device_id not in self.user_devices[user_id] and len(self.user_devices[user_id]) > 0) else 0

        device_first_seen = self.user_devices[user_id].get(device_id, now)
        device_age_days = int((now - device_first_seen) / 86400) if raw_tx.get("device_age_days") is None else int(raw_tx.get("device_age_days"))

        # 5. Location history
        if raw_tx.get("new_location") is not None:
            new_location = int(raw_tx.get("new_location"))
        else:
            new_location = 1 if (country not in self.user_locations[user_id] and len(self.user_locations[user_id]) > 0) else 0

        # 6. Beneficiary history
        if raw_tx.get("new_beneficiary") is not None:
            new_beneficiary = int(raw_tx.get("new_beneficiary"))
        else:
            new_beneficiary = 1 if beneficiary_id and beneficiary_id not in self.user_beneficiaries[user_id] else 0

        ben_first_seen = self.user_beneficiaries[user_id].get(beneficiary_id, now)
        beneficiary_age_days = int((now - ben_first_seen) / 86400) if raw_tx.get("beneficiary_age_days") is None else int(raw_tx.get("beneficiary_age_days"))

        # 7. Account Age
        if user_id not in self.user_account_created:
            self.user_account_created[user_id] = now - (150 * 86400)  # Default 150 days
        account_age_days = int((now - self.user_account_created[user_id]) / 86400) if raw_tx.get("account_age_days") is None else int(raw_tx.get("account_age_days"))

        # 8. IP Risk Score
        ip_risk_score = float(raw_tx.get("ip_risk_score")) if raw_tx.get("ip_risk_score") is not None else self._get_ip_risk_score(raw_tx.get("ip_address"))

        # 9. Time signals
        hour_of_day = now_dt.hour if raw_tx.get("hour_of_day") is None else int(raw_tx.get("hour_of_day"))
        is_weekend = (1 if now_dt.weekday() >= 5 else 0) if raw_tx.get("is_weekend") is None else int(raw_tx.get("is_weekend"))

        enriched = {
            "amount": amount,
            "payment_channel": raw_tx.get("payment_channel", "UPI"),
            "merchant_category": raw_tx.get("merchant_category", "ECOMMERCE"),
            "country": country,
            "account_age_days": account_age_days,
            "device_age_days": device_age_days,
            "new_device": new_device,
            "new_location": new_location,
            "new_beneficiary": new_beneficiary,
            "transaction_velocity_5m": velocity_5m,
            "failed_attempts_1h": failed_attempts,
            "avg_amount_30d": round(avg_amount_30d, 2),
            "amount_deviation": amount_deviation,
            "ip_risk_score": round(ip_risk_score, 2),
            "beneficiary_age_days": beneficiary_age_days,
            "hour_of_day": hour_of_day,
            "is_weekend": is_weekend,
            "user_id": user_id,
        }

        # Auto-record in real-time store for progressive state tracking
        self.record_successful_transaction(user_id, amount, device_id, country, beneficiary_id)
        return enriched


# Global Singleton Real-Time Feature Store
feature_store = RealTimeFeatureStore()
