import random
import numpy as np
from datetime import datetime


def generate_account_takeover():

    avg_amount = np.random.uniform(500, 5000)

    amount = avg_amount * np.random.uniform(1.5, 5)

    return {
        "transaction_id":
            "RED_ATO_" + str(random.randint(100000, 999999)),

        "user_id":
            "U" + str(random.randint(1000, 9999)),

        "timestamp":
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "amount":
            round(amount, 2),

        "payment_channel":
            random.choice([
                "CARD",
                "UPI",
                "BANK_TRANSFER"
            ]),

        "merchant_category":
            random.choice([
                "ECOMMERCE",
                "ELECTRONICS",
                "TRAVEL"
            ]),

        "country":
            random.choice([
                "IN",
                "SG",
                "AE"
            ]),

        "account_age_days":
            random.randint(200, 3000),

        "device_age_days":
            random.randint(0, 10),

        "new_device":
            1,

        "new_location":
            random.choice([0, 1]),

        "new_beneficiary":
            random.choice([0, 1]),

        "transaction_velocity_5m":
            random.randint(3, 10),

        "failed_attempts_1h":
            random.randint(1, 6),

        "avg_amount_30d":
            round(avg_amount, 2),

        "amount_deviation":
            round(amount / avg_amount, 3),

        "ip_risk_score":
            round(np.random.uniform(50, 95), 2),

        "beneficiary_age_days":
            random.randint(0, 20),

        "hour_of_day":
            random.randint(0, 23),

        "is_weekend":
            random.choice([0, 1]),

        "fraud_type":
            "account_takeover",

        "attack_difficulty":
            0.7,

        "is_synthetic":
            1,

        "is_fraud":
            1
    }


def generate_card_testing():

    avg_amount = np.random.uniform(500, 5000)

    amount = np.random.uniform(1, 100)

    return {
        "transaction_id":
            "RED_CARD_" + str(random.randint(100000, 999999)),

        "user_id":
            "U" + str(random.randint(1000, 9999)),

        "timestamp":
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "amount":
            round(amount, 2),

        "payment_channel":
            "CARD",

        "merchant_category":
            random.choice([
                "ECOMMERCE",
                "FOOD",
                "ENTERTAINMENT"
            ]),

        "country":
            "IN",

        "account_age_days":
            random.randint(100, 3000),

        "device_age_days":
            random.randint(0, 100),

        "new_device":
            random.choice([0, 1]),

        "new_location":
            random.choice([0, 1]),

        "new_beneficiary":
            0,

        "transaction_velocity_5m":
            random.randint(8, 30),

        "failed_attempts_1h":
            random.randint(3, 15),

        "avg_amount_30d":
            round(avg_amount, 2),

        "amount_deviation":
            round(amount / avg_amount, 3),

        "ip_risk_score":
            round(np.random.uniform(60, 99), 2),

        "beneficiary_age_days":
            random.randint(100, 1000),

        "hour_of_day":
            random.randint(0, 23),

        "is_weekend":
            random.choice([0, 1]),

        "fraud_type":
            "card_testing",

        "attack_difficulty":
            0.6,

        "is_synthetic":
            1,

        "is_fraud":
            1
    }


def generate_mule_activity():

    avg_amount = np.random.uniform(1000, 8000)

    amount = avg_amount * np.random.uniform(1.5, 6)

    return {
        "transaction_id":
            "RED_MULE_" + str(random.randint(100000, 999999)),

        "user_id":
            "U" + str(random.randint(1000, 9999)),

        "timestamp":
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "amount":
            round(amount, 2),

        "payment_channel":
            random.choice([
                "UPI",
                "BANK_TRANSFER",
                "WALLET"
            ]),

        "merchant_category":
            "OTHER",

        "country":
            "IN",

        "account_age_days":
            random.randint(50, 1200),

        "device_age_days":
            random.randint(50, 500),

        "new_device":
            random.choice([0, 0, 1]),

        "new_location":
            random.choice([0, 0, 1]),

        "new_beneficiary":
            1,

        "transaction_velocity_5m":
            random.randint(4, 15),

        "failed_attempts_1h":
            random.randint(0, 2),

        "avg_amount_30d":
            round(avg_amount, 2),

        "amount_deviation":
            round(amount / avg_amount, 3),

        "ip_risk_score":
            round(np.random.uniform(30, 80), 2),

        "beneficiary_age_days":
            random.randint(0, 10),

        "hour_of_day":
            random.randint(0, 23),

        "is_weekend":
            random.choice([0, 1]),

        "fraud_type":
            "mule_activity",

        "attack_difficulty":
            0.75,

        "is_synthetic":
            1,

        "is_fraud":
            1
    }


def generate_low_and_slow():

    avg_amount = np.random.uniform(500, 5000)

    amount = avg_amount * np.random.uniform(0.8, 1.6)

    return {
        "transaction_id":
            "RED_LOW_" + str(random.randint(100000, 999999)),

        "user_id":
            "U" + str(random.randint(1000, 9999)),

        "timestamp":
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "amount":
            round(amount, 2),

        "payment_channel":
            random.choice([
                "CARD",
                "UPI",
                "WALLET",
                "BANK_TRANSFER"
            ]),

        "merchant_category":
            random.choice([
                "GROCERY",
                "FOOD",
                "FUEL",
                "ECOMMERCE",
                "TRAVEL"
            ]),

        "country":
            "IN",

        "account_age_days":
            random.randint(500, 3000),

        "device_age_days":
            random.randint(100, 1000),

        "new_device":
            int(np.random.choice(
                [0, 1],
                p=[0.90, 0.10]
            )),

        "new_location":
            int(np.random.choice(
                [0, 1],
                p=[0.92, 0.08]
            )),

        "new_beneficiary":
            int(np.random.choice(
                [0, 1],
                p=[0.70, 0.30]
            )),

        "transaction_velocity_5m":
            random.randint(1, 4),

        "failed_attempts_1h":
            random.randint(0, 1),

        "avg_amount_30d":
            round(avg_amount, 2),

        "amount_deviation":
            round(amount / avg_amount, 3),

        "ip_risk_score":
            round(np.random.uniform(10, 50), 2),

        "beneficiary_age_days":
            random.randint(10, 500),

        "hour_of_day":
            random.randint(7, 22),

        "is_weekend":
            random.choice([0, 1]),

        "fraud_type":
            "low_and_slow",

        "attack_difficulty":
            0.95,

        "is_synthetic":
            1,

        "is_fraud":
            1
    }


def _sample_probability(probability):
    probability = max(0.0, min(1.0, float(probability)))
    return 1 if random.random() < probability else 0


def _apply_plan(attack, plan):
    if not plan or not isinstance(plan, dict):
        return attack

    params = plan.get("parameters", {})
    if not isinstance(params, dict):
        return attack

    avg_amount = max(float(attack.get("avg_amount_30d", 1) or 1), 1.0)

    ratio_min = float(params.get("amount_ratio_min", attack.get("amount_deviation", 1.0)))
    ratio_max = float(params.get("amount_ratio_max", attack.get("amount_deviation", 1.0)))
    if ratio_min > ratio_max:
        ratio_min, ratio_max = ratio_max, ratio_min
    ratio = np.random.uniform(max(0.01, ratio_min), max(0.02, ratio_max))
    attack["amount"] = round(avg_amount * ratio, 2)
    attack["amount_deviation"] = round(ratio, 3)

    ip_min = float(params.get("ip_risk_min", attack.get("ip_risk_score", 0)))
    ip_max = float(params.get("ip_risk_max", attack.get("ip_risk_score", 100)))
    if ip_min > ip_max:
        ip_min, ip_max = ip_max, ip_min
    attack["ip_risk_score"] = round(np.random.uniform(max(0, ip_min), min(100, ip_max)), 2)

    velocity_min = int(params.get("velocity_min", attack.get("transaction_velocity_5m", 1)))
    velocity_max = int(params.get("velocity_max", attack.get("transaction_velocity_5m", 1)))
    if velocity_min > velocity_max:
        velocity_min, velocity_max = velocity_max, velocity_min
    attack["transaction_velocity_5m"] = random.randint(max(1, velocity_min), max(1, velocity_max))

    failed_min = int(params.get("failed_attempts_min", attack.get("failed_attempts_1h", 0)))
    failed_max = int(params.get("failed_attempts_max", attack.get("failed_attempts_1h", 0)))
    if failed_min > failed_max:
        failed_min, failed_max = failed_max, failed_min
    attack["failed_attempts_1h"] = random.randint(max(0, failed_min), max(0, failed_max))

    if "new_device_probability" in params:
        attack["new_device"] = _sample_probability(params["new_device_probability"])
    if "new_location_probability" in params:
        attack["new_location"] = _sample_probability(params["new_location_probability"])
    if "new_beneficiary_probability" in params:
        attack["new_beneficiary"] = _sample_probability(params["new_beneficiary_probability"])

    hour_min = int(params.get("hour_min", attack.get("hour_of_day", 0)))
    hour_max = int(params.get("hour_max", attack.get("hour_of_day", 23)))
    if hour_min > hour_max:
        hour_min, hour_max = hour_max, hour_min
    attack["hour_of_day"] = random.randint(max(0, hour_min), min(23, hour_max))

    attack["ai_strategy_title"] = str(plan.get("title", ""))[:120]
    attack["ai_strategy_source"] = str(plan.get("source", "manual"))[:40]
    return attack


def generate_attack(attack_type, plan=None):
    if attack_type == "account_takeover":
        attack = generate_account_takeover()
    elif attack_type == "card_testing":
        attack = generate_card_testing()
    elif attack_type == "mule_activity":
        attack = generate_mule_activity()
    elif attack_type == "low_and_slow":
        attack = generate_low_and_slow()
    else:
        raise ValueError("Unsupported attack type: " + str(attack_type))

    return _apply_plan(attack, plan)


def generate_multiple_attacks(attack_type, count, plan=None):
    return [generate_attack(attack_type, plan=plan) for _ in range(count)]
