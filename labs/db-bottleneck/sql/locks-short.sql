SELECT pid,
       pg_blocking_pids(pid) AS blocked_by,
       wait_event_type AS wait,
       left(regexp_replace(query, '\s+', ' ', 'g'), 34) AS query
FROM pg_stat_activity
WHERE datname = 'shop' AND pid <> pg_backend_pid() AND state <> 'idle'
ORDER BY query_start
LIMIT 6;

SELECT count(*) AS insert_esperando_o_alter
FROM pg_stat_activity
WHERE datname = 'shop' AND wait_event_type = 'Lock' AND query ILIKE '%INSERT INTO orders%';
