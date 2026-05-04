import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils.supabase_client import supabase

response = supabase.table("fraud_geo_summary").select("*").execute()
amount_bucket_summary = response.data

fraud_geo_summary = response.data

# Load from Supabase table export or query result
df = pd.DataFrame(fraud_geo_summary.copy())

# Select features for clustering
features = df[
    [
        "lat",
        "long",
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
    min_samples=3
)

df["cluster"] = dbscan.fit_predict(X_scaled)

# View results
print(df[["state", "city", "lat", "long", "fraud_rate", "cluster"]].head())

# Cluster counts
print(df["cluster"].value_counts())

# Outliers / unusual fraud locations
outliers = df[df["cluster"] == -1]
print("\nOutliers:")
print(outliers[["state", "city", "lat", "long", "fraud_rate", "fraud_amount"]])


# Plot longitude/latitude clusters
plt.figure(figsize=(10, 6))
plt.scatter(
    df["long"],
    df["lat"],
    c=df["cluster"],
    s=60
)

plt.title("DBSCAN Fraud Geo Clusters")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.colorbar(label="Cluster")
plt.savefig("./plots/dbscan-location.png", dpi=300)

<<<<<<< HEAD
df_deduped = df.loc[df.groupby(["state", "city"])["total_transactions"].idxmax()]

rows = [
    {
        "dimension": "location",
        "label": f"{row['state']}|{row['city']}",
        "cluster_assignment": int(row["cluster"]),
        "fraud_rate": float(row["fraud_rate"]) if row["fraud_rate"] is not None else None,
        "total_transactions": int(row["total_transactions"]),
    }
    for _, row in df_deduped.iterrows()
]
supabase.table("cluster_results").upsert(rows, on_conflict="dimension,label").execute()
print("Cluster results written to Supabase.")
=======
from sklearn.metrics import silhouette_score, silhouette_samples
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def plot_dbscan_silhouette(points, cluster_labels, sample_names, output_path, title):
    cluster_labels = np.array(cluster_labels)
    sample_names = np.array(sample_names)

    # Silhouette score cannot be calculated if there is only one cluster.
    # DBSCAN noise is labeled as -1, so we exclude noise from silhouette scoring.
    non_noise_mask = cluster_labels != -1
    clean_points = points[non_noise_mask]
    clean_labels = cluster_labels[non_noise_mask]
    clean_names = sample_names[non_noise_mask]

    num_clusters = len(set(clean_labels))

    if num_clusters < 2:
        print("Cannot compute silhouette score: DBSCAN found fewer than 2 non-noise clusters.")
        print("Cluster counts:")
        print(pd.Series(cluster_labels).value_counts().sort_index())
        return None

    overall_score = silhouette_score(clean_points, clean_labels)
    sample_scores = silhouette_samples(clean_points, clean_labels)

    print(f"{title} Silhouette Score:", overall_score)
    print("Cluster counts:")
    print(pd.Series(cluster_labels).value_counts().sort_index())

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


dbscan = DBSCAN(eps=0.8, min_samples=2)
cluster_labels = dbscan.fit_predict(X_scaled)
df["location_label"] = (
    "lat " + df["lat"].round(2).astype(str)
    + ", long " + df["long"].round(2).astype(str)
)

location_score = plot_dbscan_silhouette(
    X_scaled,
    cluster_labels,
    df["location_label"].values,
    "./plots/dbscan_location_silhouette.png",
    "DBSCAN Location"
)
>>>>>>> 2ef67bb (adding silhouette score plots)
