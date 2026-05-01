import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils.supabase_client import supabase

response = supabase.table("geo_bucket_summary").select("*").execute()

geo_bucket_summary = response.data

# Load from Supabase table export or query result
df = pd.DataFrame(geo_bucket_summary.copy())

# Choose numeric columns for clustering
features = df[
    [
        "total_transactions",
        "fraud_transactions",
        "fraud_amount",
        "fraud_rate"
    ]
].fillna(0)

# Scale values so large dollar amounts do not dominate
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)


# Create linkage matrix for dendrogram using ward linkage
# =========================================================
Z = linkage(X_scaled, method="ward")

location_labels = (
    df["geo_buckets"]
).values

plt.figure(figsize=(12, 6))
dendrogram(
    Z,
    labels=location_labels,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Location - Ward Linkage")
plt.xlabel("Longitude, Latitude")
plt.ylabel("Distance")
plt.tight_layout()
plt.savefig("./plots/hierarchical_clustering_location.png", dpi=300)