import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
from utils.supabase_client import supabase

response = supabase.table("amount_bucket_summary").select("*").execute()
amount_bucket_summary = response.data

df = pd.DataFrame(response.data)

print(df.columns.tolist())

# Convert numeric columns
numeric_cols = [
    "total_transactions",
    "fraud_transactions",
    "total_amount",
    "fraud_amount",
    "fraud_rate"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Create missing average columns
df["avg_transaction_amount"] = df["total_amount"] / df["total_transactions"]
df["avg_transaction_amount"] = df["avg_transaction_amount"].fillna(0)

df["avg_fraud_amount"] = df["fraud_amount"] / df["fraud_transactions"]
df["avg_fraud_amount"] = df["avg_fraud_amount"].replace([float("inf"), -float("inf")], 0).fillna(0)

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
]

X_scaled = StandardScaler().fit_transform(features)

dbscan = DBSCAN(eps=0.8, min_samples=2)
df["cluster"] = dbscan.fit_predict(X_scaled)

print(df[["amount_range", "fraud_rate", "fraud_amount", "cluster"]])

print("\nCluster Counts:")
print(df["cluster"].value_counts())

outliers = df[df["cluster"] == -1]
print("\nOutliers:")
print(outliers[["amount_range", "fraud_rate", "fraud_amount"]])

plt.figure(figsize=(8, 5))
plt.scatter(
    df["fraud_rate"],
    df["fraud_amount"],
    c=df["cluster"],
    s=100
)

for i, txt in enumerate(df["amount_range"]):
    plt.annotate(
        txt,
        (df["fraud_rate"].iloc[i], df["fraud_amount"].iloc[i])
    )

plt.title("DBSCAN Clusters by Amount Bucket")
plt.xlabel("Fraud Rate")
plt.ylabel("Fraud Amount")
plt.colorbar(label="Cluster")
plt.tight_layout()
plt.savefig("./plots/dbscan-amount-bucket.png", dpi=300)