SELECT pid,
       pg_blocking_pids(pid) AS blocked_by,
       wait_event_type,
       state,
       now() - query_start AS waiting_for,
       left(query, 60) AS query
FROM pg_stat_activity
WHERE datname = 'shop' AND pid <> pg_backend_pid() AND state <> 'idle'
ORDER BY query_start;
