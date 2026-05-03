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

router.get('/by-amount', async (_req, res) => {
  const [summaryRes, dimRes] = await Promise.all([
    supabase.from('amount_bucket_summary').select('*'),
    supabase.from('dim_amount_bucket').select('*'),
  ]);

  if (summaryRes.error) return res.status(500).json({ error: summaryRes.error.message });
  if (dimRes.error) return res.status(500).json({ error: dimRes.error.message });

  const dimMap = Object.fromEntries(dimRes.data.map(d => [d.amount_range, d]));
  const data = summaryRes.data
    .map(row => ({ ...row, ...dimMap[row.amount_range] }))
    .sort((a, b) => (a.sort_order ?? 99) - (b.sort_order ?? 99));

  res.json(data);
});

router.get('/flagged', async (_req, res) => {
  const { data: lofRows, error: lofError } = await supabase
    .from('lof_scores')
    .select('transaction_id, lof_score, is_anomaly')
    .eq('is_anomaly', true)
    .limit(10000);

  if (lofError) return res.status(500).json({ error: lofError.message });
  if (!lofRows.length) return res.json([]);

  const ids = lofRows.map(r => r.transaction_id);

  // chunk to avoid URL length limits on the .in() filter
  const CHUNK = 200;
  const chunks = [];
  for (let i = 0; i < ids.length; i += CHUNK) chunks.push(ids.slice(i, i + CHUNK));

  const chunkResults = await Promise.all(
    chunks.map(chunk => supabase.from('transactions_detailed').select('*').in('trans_num', chunk))
  );

  const txError = chunkResults.find(r => r.error)?.error;
  if (txError) return res.status(500).json({ error: txError.message });

  const txRows = chunkResults.flatMap(r => r.data ?? []);
  const lofMap = Object.fromEntries(lofRows.map(r => [r.transaction_id, r]));
  const data = txRows.map(tx => ({ ...tx, ...lofMap[String(tx.trans_num)] }));

  res.json(data);
});

router.get('/by-geo', async (_req, res) => {
  const { data, error } = await supabase
    .from('fraud_geo_summary')
    .select('state, city, lat, long, total_transactions, fraud_transactions, fraud_rate')
    .limit(10000);

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
