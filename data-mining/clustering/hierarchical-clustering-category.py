import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.metrics import silhouette_score, silhouette_samples
import matplotlib.pyplot as plt
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils.supabase_client import supabase

response = supabase.table("fraud_category_summary").select("*").execute()

fraud_category_summary = response.data

# Load from Supabase table export or query result
df = pd.DataFrame(fraud_category_summary.copy())

# Choose numeric columns for clustering
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
].fillna(0)

# Scale values so large dollar amounts do not dominate
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)

# Create linkage matrix for dendrogram
Z = linkage(X_scaled, method="ward")

plt.figure(figsize=(12, 6))
dendrogram(
    Z,
    labels=(df["category"]).values,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Category - Ward Linkage")
plt.xlabel("Category")
plt.ylabel("Distance")
plt.tight_layout()
plt.savefig("./plots/hierarchical_category_clustering.png", dpi=300)

def plot_silhouette_with_clusters(points, labels, sample_names, output_path):
    overall_score = silhouette_score(points, labels)
    print("Silhouette Score:", overall_score)

    scores = silhouette_samples(points, labels)
    unique_clusters = sorted(set(labels))

    plt.figure(figsize=(10, 6))
    y_lower = 0

    for cluster in unique_clusters:
        cluster_indices = [i for i, label in enumerate(labels) if label == cluster]
        cluster_scores = [(scores[i], sample_names[i]) for i in cluster_indices]
        cluster_scores.sort(key=lambda x: x[0])

        y_upper = y_lower + len(cluster_scores)

        plt.barh(
            range(y_lower, y_upper),
            [score for score, name in cluster_scores],
            height=1.0,
            label=f"Cluster {cluster}"
        )

        for y_pos, (score, name) in zip(range(y_lower, y_upper), cluster_scores):
            plt.text(score + 0.01, y_pos, name, va="center", fontsize=8)

        y_lower = y_upper + 2

    plt.title(f"Hierarchical Category Silhouette Plot (Score = {overall_score:.3f})")
    plt.xlabel("Silhouette Coefficient")
    plt.ylabel("Categories")
    plt.axvline(overall_score, linestyle="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)


# Create cluster labels from dendrogram
cluster_labels = fcluster(Z, t=4, criterion="maxclust")

# Silhouette requires at least 2 clusters and fewer clusters than samples
num_clusters = len(set(cluster_labels))

if 2 <= num_clusters < len(X_scaled):
    plot_silhouette_with_clusters(
        X_scaled,
        cluster_labels,
        df["category"].values,
        "./plots/hierarchical_category_silhouette.png"
    )
else:
    print(f"Cannot compute silhouette score with {num_clusters} cluster(s).")