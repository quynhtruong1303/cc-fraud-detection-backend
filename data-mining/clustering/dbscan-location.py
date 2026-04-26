import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from utils import supabase_client

response = supabase_client.supabase.table("fraud_geo_summary").select("*").execute()

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
plt.show()