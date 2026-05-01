DROP TABLE IF EXISTS public.amount_bucket_summary;

CREATE TABLE public.amount_bucket_summary AS
SELECT
    CASE
        WHEN amt < 100 THEN '0-100'
        WHEN amt < 200 THEN '0-200'
        WHEN amt < 300 THEN '0-300'
        WHEN amt < 400 THEN '0-400'
        WHEN amt < 500 THEN '0-500'
        WHEN amt < 1000 THEN '500-1000'
        WHEN amt < 1500 THEN '1000-1500'
        WHEN amt < 2000 THEN '1500-2000'
        WHEN amt < 2500 THEN '2000-2500'
        WHEN amt < 3000 THEN '2500-3000'
        ELSE '3000+'
    END AS amount_range,

    COUNT(*) AS total_transactions,

    COUNT(*) FILTER (WHERE is_fraud = '1') AS fraud_transactions,

    SUM(amt) AS total_amount,

    SUM(amt) FILTER (WHERE is_fraud = '1') AS fraud_amount,

    ROUND(
        COUNT(*) FILTER (WHERE is_fraud = '1')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate

FROM public.transactions_detailed
GROUP BY amount_range
ORDER BY amount_range;

ALTER TABLE public.fraud_category_monthly
ADD CONSTRAINT pk_fraud_category_monthly
PRIMARY KEY (month, category);