import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
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
Z_single = linkage(X_scaled, method="single")

plt.figure(figsize=(12, 6))
dendrogram(
    Z_single,
    labels=(df["amount_range"]).values,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Transaction Amount - Single")
plt.xlabel("Amount")
plt.tight_layout()
plt.show()

Z_complete = linkage(X_scaled, method="complete")

plt.figure(figsize=(12, 6))
dendrogram(
    Z_complete,
    labels=(df["amount_range"]).values,
    leaf_rotation=90
)
plt.title("Hierarchical Clustering of Fraud by Transaction Amount - Complete")
plt.xlabel("Amount")
plt.tight_layout()
plt.show()