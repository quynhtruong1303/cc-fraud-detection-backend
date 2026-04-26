import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from utils import supabase_client

response = supabase_client.supabase.table("fraud_category_summary").select("*").execute()

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

# Save clustered output
df.to_csv("dbscan_fraud_category_clusters.csv", index=False)

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
plt.show()