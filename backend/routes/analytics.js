const express = require('express');
const router = express.Router();
const supabase = require('../utils/supabase');

router.get('/summary', async (_req, res) => {
  const { data, error } = await supabase
    .from('fraud_summary')
    .select('*')
    .order('id', { ascending: false })
    .limit(1)
    .single();

  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

router.get('/by-category', async (_req, res) => {
  const [summaryRes, dimRes] = await Promise.all([
    supabase.from('fraud_category_summary').select('*'),
    supabase.from('dim_category').select('*'),
  ]);

  if (summaryRes.error) return res.status(500).json({ error: summaryRes.error.message });
  if (dimRes.error) return res.status(500).json({ error: dimRes.error.message });

  const dimMap = Object.fromEntries(dimRes.data.map(d => [d.category, d]));
  const data = summaryRes.data
    .map(row => ({ ...row, ...dimMap[row.category] }))
    .sort((a, b) => (a.sort_order ?? 99) - (b.sort_order ?? 99));

  res.json(data);
});

router.get('/by-location', async (_req, res) => {
  const { data, error } = await supabase
    .from('fraud_location_summary')
    .select('*')
    .order('fraud_rate', { ascending: false });

  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

router.get('/clusters', async (req, res) => {
  const { dimension } = req.query;

  let query = supabase.from('cluster_results').select('*');
  if (dimension) query = query.eq('dimension', dimension);

  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

router.get('/double-flagged', async (_req, res) => {
  const { data, error } = await supabase
    .from('double_flagged')
    .select('*')
    .order('lof_score', { ascending: false });

  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

module.exports = router;
