DROP TABLE IF EXISTS public.fraud_geo_summary;

CREATE TABLE public.fraud_geo_summary AS
SELECT
    state,
    city,

    lat,
    long,

    COUNT(*) AS total_transactions,

    COUNT(*) FILTER (WHERE is_fraud = '1') AS fraud_transactions,

    SUM(amt) AS total_amount,

    SUM(amt) FILTER (WHERE is_fraud = '1') AS fraud_amount,

    AVG(amt) AS avg_transaction_amount,

    AVG(amt) FILTER (WHERE is_fraud = '1') AS avg_fraud_amount,

    ROUND(
        COUNT(*) FILTER (WHERE is_fraud = '1')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate

FROM public.transactions_detailed
WHERE lat IS NOT NULL
  AND long IS NOT NULL
GROUP BY
    state,
    city,
    lat,
    long
ORDER BY
    fraud_rate DESC;

ALTER TABLE public.fraud_geo_summary
ADD CONSTRAINT pk_fraud_geo_summary
PRIMARY KEY (state, city, lat, long);