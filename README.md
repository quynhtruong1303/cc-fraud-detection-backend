# Fraud Detection Backend

## Structure

```
fraud-detection-backend/
  .env                  ← shared env file (single source of truth)
  backend/              ← Express API 
  data-mining/          ← Clustering, LOF, and data warehouse
```

---

## Environment Setup

The `.env` file lives at the **repo root** (`fraud-detection-backend/.env`), not inside `backend/`.

```
PORT=3000
SUPABASE_URL=https://xkfmuohnstxgzfdkslog.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
DATABASE_URL=postgresql://postgres:<password>@db.xkfmuohnstxgzfdkslog.supabase.co:5432/postgres
```

- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` — used by the Express server and Python scripts to query Supabase via the REST API
- `DATABASE_URL` — used by `run_warehouse.py` to run raw SQL (DDL) against the database directly

---

## Backend (Express API)

### Deployment
- **Production:** https://cc-fraud-detection-backend.onrender.com
- **Platform:** Render (Root Directory: `backend`, Build: `npm install`, Start: `node server.js`)

### Local setup
```bash
cd backend
npm install
npm run dev    # development (nodemon auto-restart)
npm start      # production
```

### API Endpoints

#### Transactions — raw historical data
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions/simple` | `transactions_simple` (paginated) |
| GET | `/api/transactions/detailed` | `transactions_detailed` (paginated) |

Query params: `?page=1&limit=100`

#### Analytics — dashboard data (all implemented)
| Method | Endpoint | Source table(s) | Notes |
|---|---|---|---|
| GET | `/api/analytics/summary` | `fraud_summary` | Single KPI row |
| GET | `/api/analytics/by-category` | `fraud_category_summary` + `dim_category` | Merged, sorted by `sort_order` |
| GET | `/api/analytics/by-location` | `fraud_location_summary` | Ordered by `fraud_rate DESC` |
| GET | `/api/analytics/clusters` | `cluster_results` | Optional `?dimension=category\|location\|amount` |
| GET | `/api/analytics/by-amount` | `amount_bucket_summary` + `dim_amount_bucket` | **Not yet implemented** |
| GET | `/api/analytics/flagged` | `lof_scores` + `transactions_detailed` | **Not yet implemented** — LOF-flagged transactions |

---

## Data Warehouse

All warehouse tables are managed through SQL files in `data-mining/data-warehouse/`.

### Rebuild all tables
```bash
cd data-mining
pip install -r requirements.txt
python data-warehouse/run_warehouse.py
```

This drops and recreates all 13 tables in order: dimension tables first, then results tables, then fact/aggregate tables.

### Populate cluster results (run after warehouse rebuild)
```bash
cd data-mining/clustering
python dbscan-category.py
python dbscan-location.py
python dbscan-amount.py
```

### Populate LOF scores (run after warehouse rebuild)
```bash
cd data-mining
python lof_recall_first/lof_batch_score.py
```

---

## Tech Stack
- Node.js, Express.js, Supabase JS client
- Supabase (PostgreSQL)
- Python, pandas, scikit-learn, psycopg2
