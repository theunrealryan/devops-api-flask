BEGIN;
SELECT count(*) FROM orders WHERE status = 'paid';
SELECT pg_sleep(60);
COMMIT;
