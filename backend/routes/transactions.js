const express = require('express');
const router = express.Router();
const supabase = require('../utils/supabase');

router.get('/simple', async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 100;
  const offset = (page - 1) * limit;

  const { data, error } = await supabase
    .from('transactions_simple')
    .select('*')
    .range(offset, offset + limit - 1);

  if (error) {
    console.error('Supabase error:', error);
    return res.status(500).json({ error: 'Failed to fetch transactions.' });
  }

  res.status(200).json({ page, limit, data });
});

router.get('/detailed', async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 100;
  const offset = (page - 1) * limit;

  const { data, error } = await supabase
    .from('transactions_detailed')
    .select('*')
    .range(offset, offset + limit - 1);

  if (error) {
    console.error('Supabase error:', error);
    return res.status(500).json({ error: 'Failed to fetch transactions.' });
  }

  res.status(200).json({ page, limit, data });
});

module.exports = router;
