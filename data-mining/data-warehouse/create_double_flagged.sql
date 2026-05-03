DROP TABLE IF EXISTS public.double_flagged;
DROP VIEW  IF EXISTS public.double_flagged;

CREATE OR REPLACE VIEW public.double_flagged AS
SELECT
    td.trans_num::text           AS transaction_id,
    td.trans_date_trans_time,
    td.category,
    td.state,
    td.city,
    td.amt,
    ls.lof_score,
    (cr_cat.label IS NOT NULL)   AS flagged_by_category_dbscan,
    (cr_loc.label IS NOT NULL)   AS flagged_by_location_dbscan,
    (cr_amt.label IS NOT NULL)   AS flagged_by_amount_dbscan
FROM public.transactions_detailed td
JOIN public.lof_scores ls
    ON  ls.transaction_id = td.trans_num::text
    AND ls.is_anomaly = true
LEFT JOIN public.cluster_results cr_cat
    ON  cr_cat.dimension         = 'category'
    AND cr_cat.label             = td.category
    AND cr_cat.cluster_assignment = -1
LEFT JOIN public.cluster_results cr_loc
    ON  cr_loc.dimension         = 'location'
    AND cr_loc.label             = (td.state || '|' || td.city)
    AND cr_loc.cluster_assignment = -1
LEFT JOIN public.cluster_results cr_amt
    ON  cr_amt.dimension         = 'amount'
    AND cr_amt.label             = CASE
        WHEN td.amt::numeric < 100  THEN '0-100'
        WHEN td.amt::numeric < 200  THEN '100-200'
        WHEN td.amt::numeric < 300  THEN '200-300'
        WHEN td.amt::numeric < 400  THEN '300-400'
        WHEN td.amt::numeric < 500  THEN '400-500'
        WHEN td.amt::numeric < 1000 THEN '500-1000'
        WHEN td.amt::numeric < 1500 THEN '1000-1500'
        WHEN td.amt::numeric < 2000 THEN '1500-2000'
        WHEN td.amt::numeric < 2500 THEN '2000-2500'
        WHEN td.amt::numeric < 3000 THEN '2500-3000'
        ELSE '3000+'
    END
    AND cr_amt.cluster_assignment = -1
WHERE
    cr_cat.label IS NOT NULL
    OR cr_loc.label IS NOT NULL
    OR cr_amt.label IS NOT NULL;
