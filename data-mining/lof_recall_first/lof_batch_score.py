import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from utils.supabase_client import supabase

MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
THRESHOLD = -0.059

NUMERIC_FEATURES = [
    "amt", "amt_log1p", "lat", "long",
    "city_pop", "city_pop_log1p",
    "merch_lat", "merch_long",
    "hour", "day_of_week", "month",
    "is_weekend", "age", "merchant_distance_km",
]
CATEGORICAL_FEATURES = ["category", "state"]


def fetch_transactions():
    rows = []
    batch_size = 1000
    offset = 0
    while True:
        response = (
            supabase.table("transactions_detailed")
            .select("trans_num,trans_date_trans_time,dob,amt,lat,long,city_pop,merch_lat,merch_long,category,state")
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        if not response.data:
            break
        rows.extend(response.data)
        if len(response.data) < batch_size:
            break
        offset += batch_size
    return pd.DataFrame(rows)


def add_features(df):
    df = df.copy()
    df["trans_date_trans_time"] = pd.to_datetime(
        df["trans_date_trans_time"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    df["dob"] = pd.to_datetime(df["dob"], format="%d-%m-%Y", errors="coerce")

    for col in ["amt", "lat", "long", "city_pop", "merch_lat", "merch_long"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["hour"] = df["trans_date_trans_time"].dt.hour
    df["day_of_week"] = df["trans_date_trans_time"].dt.dayofweek
    df["month"] = df["trans_date_trans_time"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["age"] = (df["trans_date_trans_time"] - df["dob"]).dt.days / 365.25
    df["merchant_distance_km"] = (
        ((df["lat"] - df["merch_lat"]) ** 2 + (df["long"] - df["merch_long"]) ** 2) ** 0.5
    ) * 111
    df["amt_log1p"] = np.log1p(df["amt"].clip(lower=0))
    df["city_pop_log1p"] = np.log1p(df["city_pop"].clip(lower=0))
    return df


def main():
    print("Loading transactions_detailed from Supabase...")
    df = fetch_transactions()
    print(f"  {len(df)} rows loaded")

    df = add_features(df)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    print("Loading model and preprocessor...")
    preprocessor = joblib.load(MODEL_DIR / "primary_preprocessor.joblib")
    model = joblib.load(MODEL_DIR / "primary_lof_model.joblib")

    print("Running LOF inference...")
    X_transformed = preprocessor.transform(X)
    scores = -model.decision_function(X_transformed)
    is_anomaly = scores >= THRESHOLD

    rows = [
        {
            "transaction_id": str(tid),
            "lof_score": round(float(score), 6),
            "is_anomaly": bool(flag),
        }
        for tid, score, flag in zip(df["trans_num"], scores, is_anomaly)
    ]

    print(f"Writing {len(rows)} scores to lof_scores...")
    batch_size = 1000
    for i in range(0, len(rows), batch_size):
        supabase.table("lof_scores").upsert(rows[i:i + batch_size]).execute()

    flagged = int(sum(is_anomaly))
    print(f"Done. {flagged} anomalies flagged ({flagged / len(rows) * 100:.1f}%)")


if __name__ == "__main__":
    main()
