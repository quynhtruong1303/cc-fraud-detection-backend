from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs" / "lof"
MODEL_DIR = OUTPUT_DIR / "artifacts"
PLOT_DIR = OUTPUT_DIR / "plots"
DATA_PATH = BASE_DIR / "fraud_data.csv"

# Keep matplotlib and font caches local to the project.
os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT_DIR / "mpl_config"))
os.environ.setdefault("XDG_CACHE_HOME", str(OUTPUT_DIR / "cache"))

import joblib
import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

matplotlib.use("Agg")


def prepare_directories() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)


def load_and_clean_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df = df[df["is_fraud"].isin(["0", "1"])].copy()
    df["is_fraud"] = df["is_fraud"].astype(int)

    df["trans_date_trans_time"] = pd.to_datetime(
        df["trans_date_trans_time"],
        format="%d-%m-%Y %H:%M",
        errors="coerce",
    )
    df["dob"] = pd.to_datetime(df["dob"], format="%d-%m-%Y", errors="coerce")

    numeric_cols = ["amt", "lat", "long", "city_pop", "merch_lat", "merch_long"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def engineer_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    work = df.copy()

    work["hour"] = work["trans_date_trans_time"].dt.hour
    work["day_of_week"] = work["trans_date_trans_time"].dt.dayofweek
    work["month"] = work["trans_date_trans_time"].dt.month
    work["age"] = (work["trans_date_trans_time"] - work["dob"]).dt.days / 365.25

    # Simple distance proxy in kilometers; good enough for proof-of-concept features.
    work["merchant_distance_km"] = (
        ((work["lat"] - work["merch_lat"]) ** 2 + (work["long"] - work["merch_long"]) ** 2)
        ** 0.5
    ) * 111

    numeric_features = [
        "amt",
        "lat",
        "long",
        "city_pop",
        "merch_lat",
        "merch_long",
        "hour",
        "day_of_week",
        "month",
        "age",
        "merchant_distance_km",
    ]
    categorical_features = ["category", "state"]

    feature_cols = numeric_features + categorical_features
    X = work[feature_cols]
    y = work["is_fraud"]
    return X, y, numeric_features, categorical_features


def build_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
                    ]
                ),
                categorical_features,
            ),
        ]
    )


def evaluate_predictions(
    y_true: pd.Series,
    y_pred: np.ndarray,
    scores: np.ndarray,
) -> dict[str, float]:
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, scores),
        "pr_auc": average_precision_score(y_true, scores),
    }


def save_confusion_matrix_plot(cm: np.ndarray, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax)
    ax.set_title("LOF Confusion Matrix")
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_xticks([0, 1], labels=["Normal", "Fraud"])
    ax.set_yticks([0, 1], labels=["Normal", "Fraud"])

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, cm[i, j], ha="center", va="center", color="black")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_roc_plot(y_true: pd.Series, scores: np.ndarray, out_path: Path) -> None:
    fpr, tpr, _ = roc_curve(y_true, scores)
    auc = roc_auc_score(y_true, scores)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, label=f"LOF ROC AUC = {auc:.3f}", linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random baseline")
    ax.set_title("LOF ROC Curve")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_precision_recall_plot(y_true: pd.Series, scores: np.ndarray, out_path: Path) -> None:
    precision, recall, _ = precision_recall_curve(y_true, scores)
    ap = average_precision_score(y_true, scores)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(recall, precision, linewidth=2, label=f"LOF PR AUC = {ap:.3f}")
    ax.set_title("LOF Precision-Recall Curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_score_distribution_plot(y_true: pd.Series, scores: np.ndarray, out_path: Path) -> None:
    normal_scores = scores[np.asarray(y_true == 0)]
    fraud_scores = scores[np.asarray(y_true == 1)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(normal_scores, bins=40, alpha=0.65, label="Normal", density=True)
    ax.hist(fraud_scores, bins=40, alpha=0.65, label="Fraud", density=True)
    ax.set_title("LOF Score Distribution")
    ax.set_xlabel("Fraud Score (higher = more anomalous)")
    ax.set_ylabel("Density")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def train_and_evaluate() -> None:
    prepare_directories()

    df = load_and_clean_data(DATA_PATH)
    X, y, numeric_features, categorical_features = engineer_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y,
    )

    X_train_normal = X_train[y_train == 0]

    preprocessor = build_preprocessor(numeric_features, categorical_features)
    X_train_normal_transformed = preprocessor.fit_transform(X_train_normal)
    X_test_transformed = preprocessor.transform(X_test)

    contamination = max(0.001, min(0.20, float(y_train.mean())))
    lof = LocalOutlierFactor(
        n_neighbors=35,
        contamination=contamination,
        novelty=True,
    )
    lof.fit(X_train_normal_transformed)

    raw_predictions = lof.predict(X_test_transformed)
    y_pred = (raw_predictions == -1).astype(int)
    scores = -lof.decision_function(X_test_transformed)

    metrics = evaluate_predictions(y_test, y_pred, scores)
    cm = confusion_matrix(y_test, y_pred)

    print("\nLOF Fraud Detection Results")
    print("-" * 40)
    print(f"Training rows (normal only): {len(X_train_normal):,}")
    print(f"Test rows: {len(X_test):,}")
    print(f"Fraud rate in full dataset: {y.mean():.4f}")
    print(f"Model contamination: {contamination:.4f}")
    print()
    for name, value in metrics.items():
        print(f"{name:>10}: {value:.4f}")
    print()
    print("Confusion Matrix:")
    print(cm)

    metrics_path = OUTPUT_DIR / "metrics.txt"
    with metrics_path.open("w", encoding="utf-8") as fh:
        fh.write("LOF Fraud Detection Results\n")
        fh.write("=" * 40 + "\n")
        fh.write(f"training_rows_normal_only={len(X_train_normal)}\n")
        fh.write(f"test_rows={len(X_test)}\n")
        fh.write(f"fraud_rate={y.mean():.6f}\n")
        fh.write(f"contamination={contamination:.6f}\n")
        for name, value in metrics.items():
            fh.write(f"{name}={value:.6f}\n")
        fh.write(f"confusion_matrix={cm.tolist()}\n")

    save_confusion_matrix_plot(cm, PLOT_DIR / "confusion_matrix.png")
    save_roc_plot(y_test, scores, PLOT_DIR / "roc_curve.png")
    save_precision_recall_plot(y_test, scores, PLOT_DIR / "precision_recall_curve.png")
    save_score_distribution_plot(y_test, scores, PLOT_DIR / "score_distribution.png")

    joblib.dump(preprocessor, MODEL_DIR / "lof_preprocessor.joblib")
    joblib.dump(lof, MODEL_DIR / "lof_model.joblib")

    print()
    print(f"Saved metrics to: {metrics_path}")
    print(f"Saved plots to:   {PLOT_DIR}")
    print(f"Saved model to:   {MODEL_DIR}")


if __name__ == "__main__":
    train_and_evaluate()
