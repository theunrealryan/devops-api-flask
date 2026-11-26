CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_customer_created ON orders (customer_id, created_at DESC);
