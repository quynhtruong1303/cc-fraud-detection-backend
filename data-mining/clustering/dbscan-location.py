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

rows = [
    {
        "dimension": "location",
        "label": f"{row['state']}|{row['city']}",
        "cluster_assignment": int(row["cluster"]),
        "fraud_rate": float(row["fraud_rate"]) if row["fraud_rate"] is not None else None,
        "total_transactions": int(row["total_transactions"]),
    }
    for _, row in df.iterrows()
]
supabase.table("cluster_results").upsert(rows, on_conflict="dimension,label").execute()
print("Cluster results written to Supabase.")