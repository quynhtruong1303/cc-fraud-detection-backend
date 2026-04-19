const express = require('express');
const router = express.Router();
const supabase = require('../utils/supabase');

router.get('/summary', async (req, res) => {
  // TODO: implement once Jessica defines warehouse tables
  res.status(501).json({ message: 'Coming soon' });
});

router.get('/by-category', async (req, res) => {
  // TODO: implement once Jessica defines warehouse tables
  res.status(501).json({ message: 'Coming soon' });
});

router.get('/by-location', async (req, res) => {
  // TODO: implement once Jessica defines warehouse tables
  res.status(501).json({ message: 'Coming soon' });
});

router.get('/clusters', async (req, res) => {
  // TODO: implement once Jessica writes cluster results to Supabase
  res.status(501).json({ message: 'Coming soon' });
});

module.exports = router;
