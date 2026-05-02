DROP TABLE IF EXISTS public.fraud_summary;

CREATE TABLE public.fraud_summary (
    id                 SERIAL PRIMARY KEY,
    total_transactions BIGINT,
    fraud_transactions BIGINT,
    fraud_rate         NUMERIC,
    total_amount       NUMERIC,
    fraud_amount       NUMERIC,
    computed_at        TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.fraud_summary (
    total_transactions,
    fraud_transactions,
    fraud_rate,
    total_amount,
    fraud_amount
)
SELECT
    COUNT(*),
    COUNT(*) FILTER (WHERE is_fraud = '1'),
    ROUND(
        COUNT(*) FILTER (WHERE is_fraud = '1')::numeric
        / NULLIF(COUNT(*), 0),
        4
    ),
    SUM(amt),
    SUM(amt) FILTER (WHERE is_fraud = '1')
FROM public.transactions_detailed;
