EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, total, created_at
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC
LIMIT 20;
