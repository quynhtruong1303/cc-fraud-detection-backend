import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, silhouette_samples
import matplotlib.pyplot as plt
import os
import sys
import numpy as np
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils.supabase_client import supabase

response = supabase.table("amount_bucket_summary").select("*").execute()
amount_bucket_summary = response.data

df = pd.DataFrame(response.data)

print(df.columns.tolist())

# Convert numeric columns
numeric_cols = [
    "total_transactions",
    "fraud_transactions",
    "total_amount",
    "fraud_amount",
    "fraud_rate"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Create missing average columns
df["avg_transaction_amount"] = df["total_amount"] / df["total_transactions"]
df["avg_transaction_amount"] = df["avg_transaction_amount"].fillna(0)

df["avg_fraud_amount"] = df["fraud_amount"] / df["fraud_transactions"]
df["avg_fraud_amount"] = df["avg_fraud_amount"].replace([float("inf"), -float("inf")], 0).fillna(0)

features = df[
    [
        "total_transactions",
        "fraud_transactions",
        "total_amount",
        "fraud_amount",
        "avg_transaction_amount",
        "avg_fraud_amount",
        "fraud_rate"
    ]
]

X_scaled = StandardScaler().fit_transform(features)

dbscan = DBSCAN(eps=0.8, min_samples=2)
df["cluster"] = dbscan.fit_predict(X_scaled)

print(df[["amount_range", "fraud_rate", "fraud_amount", "cluster"]])

print("\nCluster Counts:")
print(df["cluster"].value_counts())

outliers = df[df["cluster"] == -1]
print("\nOutliers:")
print(outliers[["amount_range", "fraud_rate", "fraud_amount"]])

plt.figure(figsize=(8, 5))
plt.scatter(
    df["fraud_rate"],
    df["fraud_amount"],
    c=df["cluster"],
    s=100
)

for i, txt in enumerate(df["amount_range"]):
    plt.annotate(
        txt,
        (df["fraud_rate"].iloc[i], df["fraud_amount"].iloc[i])
    )

plt.title("DBSCAN Clusters by Amount Bucket")
plt.xlabel("Fraud Rate")
plt.ylabel("Fraud Amount")
plt.colorbar(label="Cluster")
plt.tight_layout()
plt.savefig("./plots/dbscan-amount-bucket.png", dpi=300)

def plot_dbscan_silhouette(points, labels, sample_names, output_path, title):
    labels = np.array(labels)
    sample_names = np.array(sample_names)

    # Silhouette score cannot be calculated if there is only one cluster.
    # DBSCAN noise is labeled as -1, so we exclude noise from silhouette scoring.
    non_noise_mask = labels != -1
    clean_points = points[non_noise_mask]
    clean_labels = labels[non_noise_mask]
    clean_names = sample_names[non_noise_mask]

    num_clusters = len(set(clean_labels))

    if num_clusters < 2:
        print("Cannot compute silhouette score: DBSCAN found fewer than 2 non-noise clusters.")
        return None

    overall_score = silhouette_score(clean_points, clean_labels)
    sample_scores = silhouette_samples(clean_points, clean_labels)

    print(f"{title} Silhouette Score:", overall_score)
    print("Cluster counts:")
    print(pd.Series(labels).value_counts().sort_index())

    unique_clusters = sorted(set(clean_labels))

    plt.figure(figsize=(10, 6))
    y_lower = 0

    for cluster in unique_clusters:
        cluster_indices = np.where(clean_labels == cluster)[0]
        cluster_scores = [(sample_scores[i], clean_names[i]) for i in cluster_indices]
        cluster_scores.sort(key=lambda x: x[0])

        y_upper = y_lower + len(cluster_scores)

        plt.barh(
            range(y_lower, y_upper),
            [score for score, name in cluster_scores],
            height=1.0,
            label=f"Cluster {cluster}"
        )

        for y_pos, (score, name) in zip(range(y_lower, y_upper), cluster_scores):
            plt.text(score + 0.01, y_pos, str(name), va="center", fontsize=8)

        y_lower = y_upper + 2

    plt.axvline(overall_score, linestyle="--")
    plt.title(f"{title} Silhouette Plot (Score = {overall_score:.3f})")
    plt.xlabel("Silhouette Coefficient")
    plt.ylabel("Samples")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()

    return overall_score

cluster_labels = df["cluster"].values

amount_score = plot_dbscan_silhouette(
    X_scaled,
    cluster_labels,
    df["amount_range"].values,
    "./plots/dbscan_amount_silhouette.png",
    "DBSCAN Amount Bucket"
)

rows = [
    {
        "dimension": "amount",
        "label": row["amount_range"],
        "cluster_assignment": int(row["cluster"]),
        "fraud_rate": float(row["fraud_rate"]) if row["fraud_rate"] is not None else None,
        "total_transactions": int(row["total_transactions"]),
        "silhouette_score": float(amount_score) if amount_score is not None else None,
    }
    for _, row in df.iterrows()
]
supabase.table("cluster_results").upsert(rows, on_conflict="dimension,label").execute()
print("Cluster results written to Supabase.")