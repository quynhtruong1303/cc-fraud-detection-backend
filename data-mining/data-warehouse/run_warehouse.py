import os
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in backend/.env")

SQL_FILES = [
    # dimension tables
    "create_dim_category.sql",
    "create_dim_amount_bucket.sql",
    "create_dim_geography.sql",
    # results tables
    "create_cluster_results.sql",
    "create_fraud_summary.sql",
    "create_lof_scores.sql",
    # fact tables
    "create_fraud_category_summary.sql",
    "create_fraud_location_summary.sql",
    "create_fraud_geo_summary.sql",
    "create_geo_bucket_summary.sql",
    "create_amount_bucket_summary.sql",
    "create_fraud_category_monthly.sql",
    "create_fraud_location_monthly.sql",
]

script_dir = os.path.dirname(__file__)

with psycopg2.connect(DATABASE_URL) as conn:
    conn.autocommit = True
    with conn.cursor() as cur:
        for filename in SQL_FILES:
            path = os.path.join(script_dir, filename)
            print(f"Running {filename}...")
            with open(path) as f:
                cur.execute(f.read())
            print(f"  done")

print("\nAll warehouse tables created successfully.")
