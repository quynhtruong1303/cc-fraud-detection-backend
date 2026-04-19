# Data Mining — Getting Started

This directory contains the data mining and clustering work for the fraud detection project.

## Setup

### 1. Create your virtual environment (Optional)

Virtual environment if you don't want to install the dependencies for this project globally (potential conflict, but not necessarily).

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Fill in `.env` with the Supabase URL and service role key. 
- **REQUREMENT**: Obtain Joey's Supabase invitation first.
- Go to **Project Settings** -> **API Keys** -> **Legacy anon, service_role API keys** -> copy `service_role`.

---

## EXAMPLE Directory Structure

```
data-mining/
  notebooks/
    01_explore_data.ipynb         ← load + inspect transactions_simple and transactions_detailed
    02_normalize.ipynb            ← clean, scale, reconcile schemas across both tables
    03_clustering.ipynb           ← run clustering algorithms (your choice of method)
    04_warehouse.ipynb            ← write normalized + clustered results back to Supabase
    05_dashboard_queries.ipynb    ← verify aggregated queries that Sybil's dashboard needs
  utils/
    supabase_client.py            ← Supabase connection, import this in each notebook
  requirements.txt
  .env.example
  README.md
```

---

## Database Tables

### Raw tables (read-only)
| Table | Description |
|---|---|
| `transactions_simple` | 100k rows, simple schema |
| `transactions_detailed` | 14k rows, rich schema with geo, category, demographic data |

### Warehouse tables (Example)
| Table | Description |
|---|---|
| `transactions_normalized` | combined + cleaned data from both raw tables |
| `cluster_results` | clustering output with cluster assignments |
| `fraud_summary` | aggregated stats for the dashboard |

---

## Connecting to Supabase in a Notebook

```python
import sys
sys.path.append('..')

from utils.supabase_client import supabase
import pandas as pd

df = pd.DataFrame(supabase.table("transactions_detailed").select("*").execute().data)
print(df.shape)
df.head()
```

---

## Notes
- Do not modify `transactions_simple` or `transactions_detailed` — these are raw historical data
- Warehouse tables (`transactions_normalized`, `cluster_results`) are yours to define 
- Cluster results will be consumed by Nha's Express API and displayed on our dashboard
