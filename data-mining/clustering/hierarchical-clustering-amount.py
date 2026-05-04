import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score, silhouette_samples
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import fcluster
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils import supabase_client

response = supabase_client.supabase.table("amount_bucket_summary").select("*").execute()

amount_bucket_summary = response.data

# Load from Supabase table export or query result
df = pd.DataFrame(amount_bucket_summary.copy())

# Choose numeric columns for clustering
features = df[
    [
        "total_transactions",
        "fraud_transactions",
        "total_amount",
        "fraud_amount",
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
    labels=(df["amount_range"]).values,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Transaction Amount - Ward Linkage")
plt.xlabel("Amount")
plt.tight_layout()
plt.savefig("./plots/hierarchical_amount_clustering.png", dpi=300)

def plot_silhouette_with_clusters(points, labels):
    # Overall score
    overall_score = silhouette_score(points, labels)
    print("Silhouette Score:", overall_score)

    # Per-point scores
    scores = silhouette_samples(points, labels)

    unique_clusters = sorted(set(labels))
    if -1 in unique_clusters:
        unique_clusters.remove(-1)

    plt.figure(figsize=(8, 6))
    y_lower = 0

    for cluster in unique_clusters:
        cluster_scores = scores[labels == cluster]
        cluster_scores.sort()

        y_upper = y_lower + len(cluster_scores)

        plt.barh(
            range(y_lower, y_upper),
            cluster_scores,
            height=1.0,
            label=f"Cluster {cluster}"
        )

        y_lower = y_upper + 2

    plt.title(f"Silhouette Plot (Score = {overall_score:.3f})")
    plt.xlabel("Silhouette Coefficient")
    plt.ylabel("Samples")
    plt.savefig("./plots/hierarchical_amount_silhouette.png", dpi=300)

# Create cluster labels from dendrogram
for k in range(2, min(8, len(df))):
    cluster_labels = fcluster(Z, t=k, criterion="maxclust")
    print(k, silhouette_score(X_scaled, cluster_labels))

# Compute silhouette score
score = silhouette_score(X_scaled, cluster_labels)

# Plot silhouette
plot_silhouette_with_clusters(X_scaled, cluster_labels)