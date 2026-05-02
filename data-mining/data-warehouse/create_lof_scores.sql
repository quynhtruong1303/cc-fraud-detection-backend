DROP TABLE IF EXISTS public.lof_scores;

CREATE TABLE public.lof_scores (
    transaction_id  TEXT    PRIMARY KEY,
    lof_score       NUMERIC NOT NULL,
    is_anomaly      BOOLEAN NOT NULL
);
