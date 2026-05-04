import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score, silhouette_samples
import numpy as np
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils.supabase_client import supabase

response = supabase.table("fraud_category_summary").select("*").execute()
amount_bucket_summary = response.data

fraud_category_summary = response.data

# Load from Supabase table export or query result
df = pd.DataFrame(fraud_category_summary.copy())

# Select features for clustering
features = df[
    [
        "total_transactions",
        "fraud_transactions",
        "fraud_amount",
        "avg_transaction_amount",
        "avg_fraud_amount",
        "fraud_rate"
    ]
].fillna(0)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)

# Run DBSCAN
dbscan = DBSCAN(
    eps=0.8,
    min_samples=2
)

df["cluster"] = dbscan.fit_predict(X_scaled)

# View results
print(df[["category", "fraud_rate", "fraud_amount", "cluster"]])

# Cluster counts
print("\nCluster Counts:")
print(df["cluster"].value_counts())


# Outliers / unusual fraud locations
outliers = df[df["cluster"] == -1]
print("\nOutliers:")
print(outliers[["category", "fraud_rate", "fraud_amount"]])


# Plot longitude/latitude clusters
plt.figure(figsize=(8, 5))
plt.scatter(
    df["fraud_rate"],
    df["fraud_amount"],
    c=df["cluster"],
    s=100
)
for i, txt in enumerate(df["category"]):
    plt.annotate(txt, (df["fraud_rate"][i], df["fraud_amount"][i]))

plt.title("DBSCAN Clusters (Fraud by Category)")
plt.xlabel("Fraud Rate")
plt.ylabel("Fraud Amount")
plt.colorbar(label="Cluster")
plt.savefig("./plots/dbscan-category.png", dpi=300)

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

    return overall_score

cluster_labels = df["cluster"].values

category_score = plot_dbscan_silhouette(
    X_scaled,
    cluster_labels,
    df["category"].values,
    "./plots/dbscan_category_silhouette.png",
    "DBSCAN Category"
)

rows = [
    {
        "dimension": "category",
        "label": row["category"],
        "cluster_assignment": int(row["cluster"]),
        "fraud_rate": float(row["fraud_rate"]) if row["fraud_rate"] is not None else None,
        "total_transactions": int(row["total_transactions"]),
        "silhouette_score": float(category_score) if category_score is not None else None,
    }
    for _, row in df.iterrows()
]
supabase.table("cluster_results").upsert(rows, on_conflict="dimension,label").execute()
print("Cluster results written to Supabase.")