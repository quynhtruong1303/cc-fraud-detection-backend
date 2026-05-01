import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
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