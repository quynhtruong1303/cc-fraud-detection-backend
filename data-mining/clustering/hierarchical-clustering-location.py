import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
from utils import supabase_client

response = supabase_client.supabase.table("geo_bucket_summary").select("*").execute()

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


# Create linkage matrix for dendrogram using single linkage
# =========================================================
Z_single = linkage(X_scaled, method="single")

location_labels = (
    df["geo_buckets"]
).values

plt.figure(figsize=(12, 6))
dendrogram(
    Z_single,
    labels=location_labels,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Location - Single Linkage")
plt.xlabel("Longitude, Latitude")
plt.ylabel("Distance")
plt.tight_layout()
plt.show()

# Create linkage matrix for dendrogram using complete linkage
# =========================================================
Z_complete = linkage(X_scaled, method="complete")

plt.figure(figsize=(12, 6))
dendrogram(
    Z_complete,
    labels=location_labels,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Location - Complete Linkage")
plt.xlabel("Longitude, Latitude")
plt.ylabel("Distance")
plt.tight_layout()
plt.show()