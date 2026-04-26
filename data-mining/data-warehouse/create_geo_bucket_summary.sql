DROP TABLE IF EXISTS public.geo_bucket_summary;

CREATE TABLE public.geo_bucket_summary AS
SELECT
    CASE
        WHEN lat < 24 and long < -155 THEN 'lat 20-24 long (-165)-(-155)'
        WHEN lat < 28 and long < -150 THEN 'lat 24-28 long (-160)-(-150)'
        WHEN lat < 32 and long < -145 THEN 'lat 28-32 long (-155)-(-145)'
        WHEN lat < 36 and long < -140 THEN 'lat 32-36 long (-150)-(-140)'
        WHEN lat < 40 and long < -135 THEN 'lat 36-40 long (-145)-(-135)'
        WHEN lat < 44 and long < -130 THEN 'lat 40-44 long (-140)-(-130)'
        WHEN lat < 48 and long < -125 THEN 'lat 44-48 long (-135)-(-125)'
        WHEN lat < 52 and long < -120 THEN 'lat 48-52 long (-130)-(-120)'
        WHEN lat < 56 and long < -115 THEN 'lat 52-56 long (-125)-(-115)'
        WHEN lat < 60 and long < -110 THEN 'lat 56-60 long (-120)-(-110)'
        WHEN lat < 64 and long < -105 THEN 'lat 60-64 long (-115)-(-105)'
        WHEN lat < 68 and long < -100 THEN 'lat 64-68 long (-105)-(-100)'
        WHEN lat < 72 and long < -95 THEN 'lat 68-72 long (-100)-(-95)'
        WHEN lat < 76 and long < -90 THEN 'lat 72-76 long (-95)-(-90)'
        WHEN lat < 80 and long < -85 THEN 'lat 76-80 long (-90)-(-85)'
        WHEN lat < 84 and long < -80 THEN 'lat 80-84 long (-85)-(-80)'
    END AS geo_buckets,

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
GROUP BY geo_buckets
ORDER BY geo_buckets;