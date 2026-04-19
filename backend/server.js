// load environment variables
require('dotenv').config();

const express = require('express');
const cors = require('cors');

// import route handlers
const transactionRoutes = require('./routes/transactions');
const analyticsRoutes = require('./routes/analytics');

const app = express();
const PORT = process.env.PORT || 3000;

// allow cross-origin requests (for React frontend)
app.use(cors());

// parse incoming JSON request bodies
app.use(express.json());

// raw historical data endpoints
app.use('/api/transactions', transactionRoutes);

// aggregated analytics endpoints for the dashboard
app.use('/api/analytics', analyticsRoutes);

// start the server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

