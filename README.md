## Setup

```bash
cd backend
npm install
```

Create a `.env` file in the `backend/` folder:
```
PORT=3000
```

## Running the Server

```bash
# Development (auto-restarts on save)
npm run dev

# Production
npm start
```

## API Endpoints

### POST `/api/transactions`

Receives a transaction and returns a response.

**Request body:**
```json
{
  "amount": 250.00,
  "merchant": "Amazon",
  "card_last4": "4242"
}
```

**Response:**
```json
{
  "message": "Transaction received",
  "data": {
    "amount": 250.00,
    "merchant": "Amazon",
    "card_last4": "4242"
  }
}
```

## Tech Stack
- Node.js
- Express.js
- dotenv
- cors
- nodemon (dev)