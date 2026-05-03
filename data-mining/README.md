# Data Mining

Clustering, anomaly detection, and data warehouse for the fraud detection project.

---

## Directory Structure

```
data-mining/
  clustering/
    dbscan-category.py              ← DBSCAN on fraud_category_summary → cluster_results
    dbscan-location.py              ← DBSCAN on fraud_geo_summary → cluster_results
    dbscan-amount.py                ← DBSCAN on amount_bucket_summary → cluster_results
    hierarchical-clustering-*.py   ← Dendrograms (visual only, not written to Supabase)
    plots/                          ← Saved PNG outputs

  data-warehouse/
    run_warehouse.py                ← Runs all SQL files in order against Supabase
    create_dim_category.sql
    create_dim_amount_bucket.sql
    create_dim_geography.sql
    create_cluster_results.sql
    create_fraud_summary.sql
    create_lof_scores.sql
    create_fraud_category_summary.sql
    create_fraud_location_summary.sql
    create_fraud_geo_summary.sql
    create_geo_bucket_summary.sql
    create_amount_bucket_summary.sql
    create_fraud_category_monthly.sql
    create_fraud_location_monthly.sql

  lof/
    lof_baseline.py                 ← Baseline LOF model (trained on fraud_data.csv)
    artifacts/                      ← Saved model + preprocessor

  lof_recall_first/
    lof_fraud_detection.py          ← Recall-first LOF model (primary)
    lof_batch_score.py              ← Scores transactions_detailed → writes to lof_scores
    artifacts/                      ← primary_lof_model.joblib + primary_preprocessor.joblib

  utils/
    supabase_client.py              ← Shared Supabase connection for all Python scripts

  requirements.txt
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment variables
The `.env` file lives at the **repo root** (`fraud-detection-backend/.env`), not here. All scripts load it automatically — no setup needed beyond filling in your credentials there.

Required variables:
```
SUPABASE_URL=https://xkfmuohnstxgzfdkslog.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
DATABASE_URL=postgresql://postgres:<password>@db.xkfmuohnstxgzfdkslog.supabase.co:5432/postgres
```

Obtain the `SUPABASE_SERVICE_KEY` from: **Supabase → Project Settings → API Keys → service_role**.
Obtain the DB password from: **Supabase → Project Settings → Database → Connection string**.

---

## Running the Pipeline

### Step 1 — Rebuild all warehouse tables
```bash
cd data-mining
python data-warehouse/run_warehouse.py
```

Runs all 13 SQL files in order. Safe to re-run — each file starts with `DROP TABLE IF EXISTS`.

### Step 2 — Populate cluster results
```bash
cd data-mining/clustering
python dbscan-category.py
python dbscan-location.py
python dbscan-amount.py
```

Each script reads from a Supabase summary table, runs DBSCAN, and upserts results into `cluster_results`.

### Step 3 — Populate LOF scores
```bash
cd data-mining
python lof_recall_first/lof_batch_score.py
```

Loads `transactions_detailed` from Supabase, runs the saved primary LOF model, writes one row per transaction to `lof_scores`.

---

## Database Tables

### Dimension tables (reference / lookup)
| Table | PK | Description |
|---|---|---|
| `dim_category` | `category` | 14 merchant categories — display label, group, sort order |
| `dim_amount_bucket` | `bucket_id` | 11 amount ranges — min/max, sort order, risk tier |
| `dim_geography` | `(state, city)` | Cities derived from data — full state name, US Census region |

### Results tables (written by scripts)
| Table | PK | Written by |
|---|---|---|
| `cluster_results` | `id` | DBSCAN scripts — unique on `(dimension, label)` |
| `fraud_summary` | `id` | `run_warehouse.py` — single KPI row |
| `lof_scores` | `transaction_id` | `lof_batch_score.py` — one row per transaction |

### Fact / aggregate tables (derived from transactions_detailed)
| Table | PK | Description |
|---|---|---|
| `fraud_category_summary` | `category` | Fraud metrics by category |
| `fraud_location_summary` | `(state, city)` | Fraud metrics by city/state |
| `fraud_geo_summary` | `(state, city, lat, long)` | Coordinate-level rollup |
| `geo_bucket_summary` | `geo_buckets` | 16 geographic grid regions |
| `amount_bucket_summary` | `amount_range` | Fraud metrics per amount range |
| `fraud_category_monthly` | `(month, category)` | Monthly time-series by category |
| `fraud_location_monthly` | `(month, state, city)` | Monthly time-series by location |

### Raw tables (read-only, do not modify)
| Table | Description |
|---|---|
| `transactions_simple` | 100k rows — simple schema |
| `transactions_detailed` | 14k rows — full schema with geo, category, demographic data |

---

## Notes
- Hierarchical clustering scripts produce dendrograms only — results are not written to Supabase
- LOF transfer pipeline (`lof_recall_first`) was evaluated but cut — near-zero precision on external dataset
- `cluster_results` location labels use `"state|city"` format (e.g. `"CA|Fresno"`); use `split_part` in SQL to join with `dim_geography`
- sklearn version warning when loading LOF artifacts is expected and does not affect results
