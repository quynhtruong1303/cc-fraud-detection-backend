// load environment variables
require('dotenv').config();

const express = require('express');
const cors = require('cors');

// import transaction routes handler
const transactionRoutes = require('./routes/transactions');

const app = express();
const PORT = process.env.PORT || 3000;

// allow cross-origin requests (for REACT frontend)
app.use(cors());

// parse incomeing JSON request bodies
app.use(express.json());

// handles all requests to /api/transactions
app.use('/api/transactions', transactionRoutes);

// start the server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

