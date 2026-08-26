import os
import joblib
import pandas as pd

from xgboost import XGBClassifier


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "behavioral_fraud_model_v4.json"
)


COLUMNS_PATH = os.path.join(
    BASE_DIR,
    "models",
    "behavioral_model_columns_v4.pkl"
)


print("Loading fraud model...")


model = XGBClassifier()

model.load_model(
    MODEL_PATH
)


model_columns = joblib.load(
    COLUMNS_PATH
)


print("Fraud model loaded successfully.")


def prepare_transaction(transaction):

    df = pd.DataFrame(
        [transaction]
    )

    df = df.drop(
        columns=[
            "transaction_id",
            "user_id",
            "timestamp",
            "fraud_type",
            "attack_difficulty",
            "is_synthetic",
            "is_fraud"
        ],
        errors="ignore"
    )

    df = pd.get_dummies(
        df,
        columns=[
            "payment_channel",
            "merchant_category",
            "country"
        ],
        drop_first=False
    )

    df = df.reindex(
        columns=model_columns,
        fill_value=0
    )

    return df


def predict_transaction(transaction):

    prepared_data = prepare_transaction(
        transaction
    )

    prediction = model.predict(
        prepared_data
    )[0]

    probability = model.predict_proba(
        prepared_data
    )[0][1]

    probability_percentage = round(
        float(probability) * 100,
        2
    )

    if probability_percentage >= 80:
        risk_level = "CRITICAL"

    elif probability_percentage >= 60:
        risk_level = "HIGH"

    elif probability_percentage >= 30:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    if int(prediction) == 1:
        prediction_label = "FRAUD"

    else:
        prediction_label = "LEGITIMATE"

    return {
        "prediction": prediction_label,
        "fraud_probability": probability_percentage,
        "risk_level": risk_level
    }