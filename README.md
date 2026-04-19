# Fraud Detection Backend

## Structure

```
fraud-detection-backend/
  backend/        ← Express API
  data-mining/    ← Clustering & data analysis
```

## Backend Setup

```bash
cd backend
npm install
```

Create a `.env` file in `backend/`:
```
PORT=3000
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_role_key
```

```bash
npm run dev    # development (auto-restart)
npm start      # production
```

## API Endpoints

### Transactions (raw historical data)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions/simple` | Fetch from transactions_simple (paginated) |
| GET | `/api/transactions/detailed` | Fetch from transactions_detailed (paginated) |

**Pagination query params:**
```
?page=1&limit=100
```

### Analytics (dashboard)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/analytics/summary` | Fraud rate, total transactions, total amount |
| GET | `/api/analytics/by-category` | Fraud breakdown by merchant category |
| GET | `/api/analytics/by-location` | Fraud breakdown by city/state |
| GET | `/api/analytics/clusters` | Cluster results from data-mining notebooks |

> Analytics endpoints return `501 Coming soon` until Jessica completes the data-mining notebooks.

## Tech Stack
- Node.js, Express.js
- Supabase (PostgreSQL)
- dotenv, cors, nodemon
