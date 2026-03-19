const express = require('express');
const router = express.Router();

// handles POST /api/transactions
router.post('/', (req, res) => {
    const transaction = req.body;

    // returns 400 error is body is empty
    if (!transaction || Object.keys(transaction).length === 0) {
        return res.status(400).json({
            error: 'No transaction data provided.'
        })
    }

    console.log('Received transaction:', transaction);

    // returns a 200 if data received
    res.status(200).json({
        message: 'Transaction received',
        data: transaction
    });
});

module.exports = router;
