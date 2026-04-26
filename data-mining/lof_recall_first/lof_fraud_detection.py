from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs" / "lof_recall_first"
PRIMARY_DIR = OUTPUT_DIR / "fraud_data"
EXTERNAL_DIR = OUTPUT_DIR / "credit_card_fraud_dataset"
MODEL_DIR = OUTPUT_DIR / "artifacts"
DATA_PATH = BASE_DIR / "fraud_data.csv"
EXTERNAL_DATA_PATH = BASE_DIR / "credit_card_fraud_dataset.csv"

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
from sklearn.model_selection import ParameterGrid, train_test_split
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

matplotlib.use("Agg")


@dataclass
class SearchResult:
    n_neighbors: int
    contamination: float
    threshold: float
    metrics: dict[str, float]
    model: LocalOutlierFactor
    preprocessor: ColumnTransformer
    validation_scores: np.ndarray


def prepare_directories() -> None:
    for path in [OUTPUT_DIR, PRIMARY_DIR, EXTERNAL_DIR, MODEL_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_primary_data(path: Path) -> pd.DataFrame:
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


def add_primary_features(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["hour"] = work["trans_date_trans_time"].dt.hour
    work["day_of_week"] = work["trans_date_trans_time"].dt.dayofweek
    work["month"] = work["trans_date_trans_time"].dt.month
    work["is_weekend"] = work["day_of_week"].isin([5, 6]).astype(int)
    work["age"] = (work["trans_date_trans_time"] - work["dob"]).dt.days / 365.25

    work["merchant_distance_km"] = (
        ((work["lat"] - work["merch_lat"]) ** 2 + (work["long"] - work["merch_long"]) ** 2)
        ** 0.5
    ) * 111

    work["amt_log1p"] = np.log1p(work["amt"].clip(lower=0))
    work["city_pop_log1p"] = np.log1p(work["city_pop"].clip(lower=0))
    return work


def build_primary_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    numeric_features = [
        "amt",
        "amt_log1p",
        "lat",
        "long",
        "city_pop",
        "city_pop_log1p",
        "merch_lat",
        "merch_long",
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "age",
        "merchant_distance_km",
    ]
    categorical_features = ["category", "state"]
    feature_cols = numeric_features + categorical_features
    return df[feature_cols], df["is_fraud"], numeric_features, categorical_features


def load_external_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["IsFraud"] = pd.to_numeric(df["IsFraud"], errors="coerce")
    return df


def build_transfer_features_from_primary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    transfer = pd.DataFrame(
        {
            "amount": df["amt"],
            "amount_log1p": np.log1p(df["amt"].clip(lower=0)),
            "hour": df["trans_date_trans_time"].dt.hour,
            "day_of_week": df["trans_date_trans_time"].dt.dayofweek,
            "month": df["trans_date_trans_time"].dt.month,
            "is_weekend": df["trans_date_trans_time"].dt.dayofweek.isin([5, 6]).astype(int),
        }
    )
    return transfer, df["is_fraud"]


def build_transfer_features_from_external(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    transfer = pd.DataFrame(
        {
            "amount": df["Amount"],
            "amount_log1p": np.log1p(df["Amount"].clip(lower=0)),
            "hour": df["TransactionDate"].dt.hour,
            "day_of_week": df["TransactionDate"].dt.dayofweek,
            "month": df["TransactionDate"].dt.month,
            "is_weekend": df["TransactionDate"].dt.dayofweek.isin([5, 6]).astype(int),
        }
    )
    return transfer, df["IsFraud"].fillna(0).astype(int)


def build_preprocessor(
    numeric_features: list[str],
    categorical_features: list[str] | None = None,
) -> ColumnTransformer:
    transformers = [
        (
            "num",
            Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            ),
            numeric_features,
        )
    ]

    if categorical_features:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
                    ]
                ),
                categorical_features,
            )
        )

    return ColumnTransformer(transformers=transformers)


def fbeta_score_local(precision: float, recall: float, beta: float = 2.0) -> float:
    if precision == 0 and recall == 0:
        return 0.0
    beta_sq = beta**2
    return (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)


def metrics_from_scores(y_true: pd.Series, scores: np.ndarray, threshold: float) -> dict[str, float]:
    y_true_array = np.asarray(y_true).astype(int)
    y_pred = (scores >= threshold).astype(int)

    precision = precision_score(y_true_array, y_pred, zero_division=0)
    recall = recall_score(y_true_array, y_pred, zero_division=0)
    f1 = f1_score(y_true_array, y_pred, zero_division=0)
    f2 = fbeta_score_local(precision, recall, beta=2.0)
    cm = confusion_matrix(y_true_array, y_pred)

    tn, fp, fn, tp = cm.ravel()
    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "f2": float(f2),
        "roc_auc": float(roc_auc_score(y_true_array, scores)),
        "pr_auc": float(average_precision_score(y_true_array, scores)),
        "false_negatives": int(fn),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "true_positives": int(tp),
        "alert_rate": float(np.mean(y_pred)),
    }


def choose_recall_first_threshold(y_true: pd.Series, scores: np.ndarray) -> tuple[float, dict[str, float], pd.DataFrame]:
    quantiles = np.linspace(0.0, 1.0, 201)
    threshold_candidates = np.unique(
        np.concatenate(
            (
                [scores.min() - 1e-9],
                np.quantile(scores, quantiles),
                [scores.max() + 1e-9],
            )
        )
    )

    rows: list[dict[str, float]] = []
    for threshold in threshold_candidates:
        metric_row = metrics_from_scores(y_true, scores, float(threshold))
        rows.append(metric_row)

    threshold_table = pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)

    # Recall-first selection:
    # 1. Prefer thresholds that hit at least 95% recall on validation
    # 2. Within that group, maximize precision
    # 3. Then maximize F2
    # 4. If no threshold reaches 95% recall, maximize recall directly
    target_recall = 0.95
    eligible = [row for row in rows if row["recall"] >= target_recall]

    if eligible:
        best_metrics = max(
            eligible,
            key=lambda row: (
                row["precision"],
                row["f2"],
                row["recall"],
                -row["false_negatives"],
            ),
        )
    else:
        best_metrics = max(
            rows,
            key=lambda row: (
                row["recall"],
                row["f2"],
                row["precision"],
                -row["false_negatives"],
            ),
        )

    return float(best_metrics["threshold"]), best_metrics, threshold_table


def search_lof_model(
    X_train_normal: pd.DataFrame,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    numeric_features: list[str],
    categorical_features: list[str] | None,
) -> tuple[SearchResult, pd.DataFrame]:
    search_rows: list[dict[str, float]] = []
    best_result: SearchResult | None = None

    param_grid = ParameterGrid(
        {
            "n_neighbors": [15, 35, 75],
            "contamination": [0.03, 0.08, 0.16, 0.20],
        }
    )

    for params in param_grid:
        preprocessor = build_preprocessor(numeric_features, categorical_features)
        X_train_normal_tx = preprocessor.fit_transform(X_train_normal)
        X_val_tx = preprocessor.transform(X_val)

        model = LocalOutlierFactor(
            n_neighbors=params["n_neighbors"],
            contamination=params["contamination"],
            novelty=True,
        )
        model.fit(X_train_normal_tx)
        val_scores = -model.decision_function(X_val_tx)
        threshold, metrics, _ = choose_recall_first_threshold(y_val, val_scores)

        row = {
            "n_neighbors": params["n_neighbors"],
            "contamination": params["contamination"],
            **metrics,
        }
        search_rows.append(row)

        candidate = SearchResult(
            n_neighbors=params["n_neighbors"],
            contamination=params["contamination"],
            threshold=threshold,
            metrics=metrics,
            model=model,
            preprocessor=preprocessor,
            validation_scores=val_scores,
        )

        if best_result is None:
            best_result = candidate
            continue

        best_key = (
            best_result.metrics["f2"],
            best_result.metrics["recall"],
            -best_result.metrics["false_negatives"],
            best_result.metrics["precision"],
        )
        candidate_key = (
            candidate.metrics["f2"],
            candidate.metrics["recall"],
            -candidate.metrics["false_negatives"],
            candidate.metrics["precision"],
        )
        if candidate_key > best_key:
            best_result = candidate

    assert best_result is not None
    return best_result, pd.DataFrame(search_rows).sort_values(
        ["f2", "recall", "precision"], ascending=False
    )


def save_confusion_matrix_plot(cm: np.ndarray, title: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Reds")
    fig.colorbar(im, ax=ax)
    ax.set_title(title)
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


def save_roc_plot(y_true: pd.Series, scores: np.ndarray, title: str, out_path: Path) -> None:
    fpr, tpr, _ = roc_curve(y_true, scores)
    auc = roc_auc_score(y_true, scores)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, label=f"ROC AUC = {auc:.3f}", linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random baseline")
    ax.set_title(title)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_pr_plot(y_true: pd.Series, scores: np.ndarray, title: str, out_path: Path) -> None:
    precision, recall, _ = precision_recall_curve(y_true, scores)
    ap = average_precision_score(y_true, scores)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(recall, precision, linewidth=2, label=f"PR AUC = {ap:.3f}")
    ax.set_title(title)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_score_distribution_plot(y_true: pd.Series, scores: np.ndarray, threshold: float, title: str, out_path: Path) -> None:
    normal_scores = scores[np.asarray(y_true == 0)]
    fraud_scores = scores[np.asarray(y_true == 1)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(normal_scores, bins=40, alpha=0.65, label="Normal", density=True)
    ax.hist(fraud_scores, bins=40, alpha=0.65, label="Fraud", density=True)
    ax.axvline(threshold, color="black", linestyle="--", linewidth=2, label="Selected threshold")
    ax.set_title(title)
    ax.set_xlabel("Fraud Score (higher = more anomalous)")
    ax.set_ylabel("Density")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def save_threshold_tradeoff_plot(threshold_table: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(threshold_table["threshold"], threshold_table["recall"], label="Recall", linewidth=2)
    ax.plot(threshold_table["threshold"], threshold_table["precision"], label="Precision", linewidth=2)
    ax.plot(threshold_table["threshold"], threshold_table["f2"], label="F2", linewidth=2)
    ax.set_title("Validation Threshold Tradeoff")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Score")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def write_metrics_file(
    out_path: Path,
    title: str,
    split_sizes: dict[str, int],
    best_result: SearchResult,
    metrics: dict[str, float],
) -> None:
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(f"{title}\n")
        fh.write("=" * len(title) + "\n")
        for key, value in split_sizes.items():
            fh.write(f"{key}={value}\n")
        fh.write(f"best_n_neighbors={best_result.n_neighbors}\n")
        fh.write(f"best_contamination={best_result.contamination:.6f}\n")
        fh.write(f"selected_threshold={best_result.threshold:.6f}\n")
        for name, value in metrics.items():
            if isinstance(value, int):
                fh.write(f"{name}={value}\n")
            else:
                fh.write(f"{name}={value:.6f}\n")


def print_metrics_block(title: str, metrics: dict[str, float]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for key in [
        "precision",
        "recall",
        "f1",
        "f2",
        "roc_auc",
        "pr_auc",
        "false_negatives",
        "false_positives",
        "alert_rate",
    ]:
        value = metrics[key]
        if isinstance(value, int):
            print(f"{key:>16}: {value}")
        else:
            print(f"{key:>16}: {value:.4f}")


def run_primary_pipeline() -> SearchResult:
    raw_df = load_primary_data(DATA_PATH)
    df = add_primary_features(raw_df)
    X, y, numeric_features, categorical_features = build_primary_xy(df)

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.25,
        random_state=42,
        stratify=y_train_val,
    )

    X_train_normal = X_train[y_train == 0]

    best_result, search_table = search_lof_model(
        X_train_normal=X_train_normal,
        X_val=X_val,
        y_val=y_val,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )

    X_test_tx = best_result.preprocessor.transform(X_test)
    test_scores = -best_result.model.decision_function(X_test_tx)
    test_metrics = metrics_from_scores(y_test, test_scores, best_result.threshold)
    test_cm = confusion_matrix(y_test, (test_scores >= best_result.threshold).astype(int))

    _, _, threshold_table = choose_recall_first_threshold(y_val, best_result.validation_scores)

    search_table.to_csv(PRIMARY_DIR / "model_search_results.csv", index=False)
    threshold_table.to_csv(PRIMARY_DIR / "validation_threshold_tradeoff.csv", index=False)

    write_metrics_file(
        PRIMARY_DIR / "metrics.txt",
        "Recall-First LOF Results on fraud_data.csv",
        {
            "train_rows": len(X_train),
            "validation_rows": len(X_val),
            "test_rows": len(X_test),
            "train_normal_rows": len(X_train_normal),
        },
        best_result,
        test_metrics,
    )

    save_confusion_matrix_plot(
        test_cm,
        "Recall-First LOF Confusion Matrix (Test)",
        PRIMARY_DIR / "confusion_matrix.png",
    )
    save_roc_plot(y_test, test_scores, "Recall-First LOF ROC Curve (Test)", PRIMARY_DIR / "roc_curve.png")
    save_pr_plot(
        y_test,
        test_scores,
        "Recall-First LOF Precision-Recall Curve (Test)",
        PRIMARY_DIR / "precision_recall_curve.png",
    )
    save_score_distribution_plot(
        y_test,
        test_scores,
        best_result.threshold,
        "Recall-First LOF Score Distribution (Test)",
        PRIMARY_DIR / "score_distribution.png",
    )
    save_threshold_tradeoff_plot(threshold_table, PRIMARY_DIR / "validation_threshold_tradeoff.png")

    joblib.dump(best_result.preprocessor, MODEL_DIR / "primary_preprocessor.joblib")
    joblib.dump(best_result.model, MODEL_DIR / "primary_lof_model.joblib")

    print("\nPrimary fraud_data.csv model")
    print("----------------------------")
    print(f"Best n_neighbors: {best_result.n_neighbors}")
    print(f"Best contamination: {best_result.contamination:.4f}")
    print(f"Selected threshold: {best_result.threshold:.6f}")
    print_metrics_block("Test performance", test_metrics)

    return best_result


def run_external_transfer_pipeline() -> None:
    primary_raw = load_primary_data(DATA_PATH)
    primary_featured = add_primary_features(primary_raw)
    X_all, y_all = build_transfer_features_from_primary(primary_featured)

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X_all,
        y_all,
        test_size=0.20,
        random_state=42,
        stratify=y_all,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.25,
        random_state=42,
        stratify=y_train_val,
    )

    X_train_normal = X_train[y_train == 0]
    numeric_features = list(X_train.columns)

    best_result, search_table = search_lof_model(
        X_train_normal=X_train_normal,
        X_val=X_val,
        y_val=y_val,
        numeric_features=numeric_features,
        categorical_features=None,
    )

    X_test_tx = best_result.preprocessor.transform(X_test)
    test_scores = -best_result.model.decision_function(X_test_tx)
    test_metrics = metrics_from_scores(y_test, test_scores, best_result.threshold)
    test_cm = confusion_matrix(y_test, (test_scores >= best_result.threshold).astype(int))

    external_raw = load_external_data(EXTERNAL_DATA_PATH)
    X_external, y_external = build_transfer_features_from_external(external_raw)
    X_external_tx = best_result.preprocessor.transform(X_external)
    external_scores = -best_result.model.decision_function(X_external_tx)
    external_metrics = metrics_from_scores(y_external, external_scores, best_result.threshold)
    external_cm = confusion_matrix(y_external, (external_scores >= best_result.threshold).astype(int))

    _, _, threshold_table = choose_recall_first_threshold(y_val, best_result.validation_scores)
    search_table.to_csv(EXTERNAL_DIR / "model_search_results.csv", index=False)
    threshold_table.to_csv(EXTERNAL_DIR / "validation_threshold_tradeoff.csv", index=False)

    write_metrics_file(
        EXTERNAL_DIR / "fraud_data_transfer_test_metrics.txt",
        "Transfer-Safe LOF Results on fraud_data.csv",
        {
            "train_rows": len(X_train),
            "validation_rows": len(X_val),
            "test_rows": len(X_test),
            "train_normal_rows": len(X_train_normal),
        },
        best_result,
        test_metrics,
    )

    write_metrics_file(
        EXTERNAL_DIR / "credit_card_fraud_dataset_metrics.txt",
        "External Test on credit_card_fraud_dataset.csv",
        {
            "external_rows": len(X_external),
        },
        best_result,
        external_metrics,
    )

    save_confusion_matrix_plot(
        test_cm,
        "Transfer Model Confusion Matrix on fraud_data.csv",
        EXTERNAL_DIR / "fraud_data_transfer_confusion_matrix.png",
    )
    save_confusion_matrix_plot(
        external_cm,
        "Transfer Model Confusion Matrix on credit_card_fraud_dataset.csv",
        EXTERNAL_DIR / "credit_card_fraud_dataset_confusion_matrix.png",
    )
    save_roc_plot(
        y_external,
        external_scores,
        "Transfer Model ROC Curve on credit_card_fraud_dataset.csv",
        EXTERNAL_DIR / "credit_card_fraud_dataset_roc_curve.png",
    )
    save_pr_plot(
        y_external,
        external_scores,
        "Transfer Model PR Curve on credit_card_fraud_dataset.csv",
        EXTERNAL_DIR / "credit_card_fraud_dataset_precision_recall_curve.png",
    )
    save_score_distribution_plot(
        y_external,
        external_scores,
        best_result.threshold,
        "Transfer Model Score Distribution on credit_card_fraud_dataset.csv",
        EXTERNAL_DIR / "credit_card_fraud_dataset_score_distribution.png",
    )
    save_threshold_tradeoff_plot(threshold_table, EXTERNAL_DIR / "validation_threshold_tradeoff.png")

    joblib.dump(best_result.preprocessor, MODEL_DIR / "transfer_preprocessor.joblib")
    joblib.dump(best_result.model, MODEL_DIR / "transfer_lof_model.joblib")

    print("\nExternal credit_card_fraud_dataset.csv transfer test")
    print("----------------------------------------------------")
    print(f"Best n_neighbors: {best_result.n_neighbors}")
    print(f"Best contamination: {best_result.contamination:.4f}")
    print(f"Selected threshold: {best_result.threshold:.6f}")
    print_metrics_block("Transfer model test performance on fraud_data.csv", test_metrics)
    print_metrics_block("Transfer model external performance", external_metrics)


def main() -> None:
    prepare_directories()
    run_primary_pipeline()
    run_external_transfer_pipeline()
    print("\nOutputs saved under:")
    print(f"  {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
