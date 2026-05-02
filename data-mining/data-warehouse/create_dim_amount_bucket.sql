DROP TABLE IF EXISTS public.dim_amount_bucket;

CREATE TABLE public.dim_amount_bucket (
    bucket_id     SERIAL PRIMARY KEY,
    amount_range  TEXT    NOT NULL UNIQUE,
    min_amount    NUMERIC NOT NULL,
    max_amount    NUMERIC,
    sort_order    INT     NOT NULL,
    risk_tier     TEXT    NOT NULL
);

INSERT INTO public.dim_amount_bucket (amount_range, min_amount, max_amount, sort_order, risk_tier) VALUES
('0-100',     0,    100,  1,  'Low'),
('100-200',   100,  200,  2,  'Low'),
('200-300',   200,  300,  3,  'Medium'),
('300-400',   300,  400,  4,  'Medium'),
('400-500',   400,  500,  5,  'Medium'),
('500-1000',  500,  1000, 6,  'High'),
('1000-1500', 1000, 1500, 7,  'High'),
('1500-2000', 1500, 2000, 8,  'Very High'),
('2000-2500', 2000, 2500, 9,  'Very High'),
('2500-3000', 2500, 3000, 10, 'Very High'),
('3000+',     3000, NULL, 11, 'Very High');
