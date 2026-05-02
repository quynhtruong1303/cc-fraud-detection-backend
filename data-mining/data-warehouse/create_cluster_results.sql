DROP TABLE IF EXISTS public.cluster_results;

CREATE TABLE public.cluster_results (
    id                 SERIAL PRIMARY KEY,
    dimension          TEXT    NOT NULL,
    label              TEXT    NOT NULL,
    cluster_assignment INT     NOT NULL,
    fraud_rate         NUMERIC,
    total_transactions BIGINT
);

ALTER TABLE public.cluster_results
ADD CONSTRAINT uq_cluster_results_dimension_label UNIQUE (dimension, label);
