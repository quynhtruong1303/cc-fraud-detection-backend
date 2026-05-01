DROP TABLE IF EXISTS public.fraud_location_monthly;

CREATE TABLE public.fraud_location_monthly AS
SELECT
    DATE_TRUNC(
        'month',
        TO_TIMESTAMP(trans_date_trans_time, 'DD-MM-YYYY HH24:MI')
    )::date AS month,

    state,
    city,

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
WHERE trans_date_trans_time IS NOT NULL
GROUP BY
    DATE_TRUNC(
        'month',
        TO_TIMESTAMP(trans_date_trans_time, 'DD-MM-YYYY HH24:MI')
    )::date,
    state,
    city
ORDER BY
    month,
    state,
    city;

ALTER TABLE public.fraud_location_monthly
ADD CONSTRAINT pk_fraud_location_monthly
PRIMARY KEY (month, state, city);