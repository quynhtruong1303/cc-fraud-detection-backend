DROP TABLE IF EXISTS public.dim_category;

CREATE TABLE public.dim_category (
    category        TEXT PRIMARY KEY,
    display_label   TEXT NOT NULL,
    category_group  TEXT NOT NULL,
    sort_order      INT  NOT NULL
);

INSERT INTO public.dim_category (category, display_label, category_group, sort_order) VALUES
('entertainment',  'Entertainment',        'Leisure',   1),
('food_dining',    'Food & Dining',        'Food',      2),
('gas_transport',  'Gas & Transport',      'Transport', 3),
('grocery_net',    'Grocery (Online)',     'Food',      4),
('grocery_pos',    'Grocery (In-Store)',   'Food',      5),
('health_fitness', 'Health & Fitness',     'Health',    6),
('home',           'Home',                 'Home',      7),
('kids_pets',      'Kids & Pets',          'Home',      8),
('misc_net',       'Misc (Online)',        'Misc',      9),
('misc_pos',       'Misc (In-Store)',      'Misc',      10),
('personal_care',  'Personal Care',        'Health',    11),
('shopping_net',   'Shopping (Online)',    'Shopping',  12),
('shopping_pos',   'Shopping (In-Store)', 'Shopping',  13),
('travel',         'Travel',              'Travel',    14);
