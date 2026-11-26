CREATE TABLE orders (
    id          bigserial PRIMARY KEY,
    customer_id integer       NOT NULL,
    status      text          NOT NULL,
    total       numeric(10,2) NOT NULL,
    created_at  timestamptz   NOT NULL DEFAULT now()
);

INSERT INTO orders (customer_id, status, total, created_at)
SELECT (random() * 99999)::int + 1,
       (ARRAY['pending', 'paid', 'shipped', 'cancelled'])[1 + (random() * 3)::int],
       round((random() * 1000)::numeric, 2),
       now() - random() * interval '365 days'
FROM generate_series(1, 3000000);

ANALYZE orders;
