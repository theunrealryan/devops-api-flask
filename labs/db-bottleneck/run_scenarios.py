import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parent
K6 = shutil.which("k6") or r"C:\Program Files\k6\k6.exe"
RESULTS = LAB / "results"
DB_TX = "SELECT xact_commit FROM pg_stat_database WHERE datname = 'shop'"


def compose(env, *args, check=True, capture=False):
    cmd = ["docker", "compose", "--env-file", f"envs/{env}.env", *args]
    return subprocess.run(cmd, cwd=LAB, check=check, capture_output=capture, text=True, encoding="utf-8")


def compose_bg(env, *args, stdout=subprocess.DEVNULL):
    cmd = ["docker", "compose", "--env-file", f"envs/{env}.env", *args]
    return subprocess.Popen(cmd, cwd=LAB, stdout=stdout, stderr=subprocess.STDOUT)


def psql(sql_file, check=True):
    return compose("baseline", "exec", "-T", "db", "psql", "-U", "lab", "-d", "shop", "-f", f"/sql/{sql_file}",
                   check=check, capture=True)


def psql_value(query):
    out = compose("baseline", "exec", "-T", "db", "psql", "-U", "lab", "-d", "shop", "-Atc", query, capture=True)
    return int(out.stdout.strip())


def use_machine(env):
    compose(env, "up", "-d", "--wait", capture=True)
    compose(env, "restart", "api", capture=True)
    compose(env, "up", "-d", "--wait", capture=True)
    time.sleep(2)


def k6_cmd(name, script, rate, duration):
    return [K6, "run", "--quiet", "-e", "BASE_URL=http://localhost:8080", "-e", f"RATE={rate}",
            "-e", f"DURATION={duration}", f"--summary-export={RESULTS / (name + '.json')}", str(LAB / "k6" / script)]


def summary(name):
    metrics = json.loads((RESULTS / f"{name}.json").read_text(encoding="utf-8"))["metrics"]
    duration = metrics["http_req_duration"]
    return {
        "requests": metrics["http_reqs"]["count"],
        "failed_pct": round(metrics["http_req_failed"]["value"] * 100, 1),
        "p95_ms": round(duration["p(95)"], 1),
        "p99_ms": round(duration["p(99)"], 1),
        "avg_ms": round(duration["avg"], 1),
        "dropped": metrics.get("dropped_iterations", {}).get("count", 0),
    }


def cache_stats():
    out = compose("cache", "exec", "-T", "cache", "valkey-cli", "info", "stats", capture=True).stdout
    stats = dict(line.split(":", 1) for line in out.splitlines() if line.startswith("keyspace_"))
    hits, misses = int(stats["keyspace_hits"]), int(stats["keyspace_misses"])
    return round(100 * hits / max(hits + misses, 1), 1)


def read_scenario(name, env, rate, duration="20s"):
    use_machine(env)
    if env == "cache":
        compose(env, "exec", "-T", "cache", "valkey-cli", "FLUSHALL", capture=True)
        compose(env, "exec", "-T", "cache", "valkey-cli", "CONFIG", "RESETSTAT", capture=True)
    tx_before = psql_value(DB_TX)
    subprocess.run(k6_cmd(name, "read.js", rate, duration), cwd=LAB, capture_output=True)
    result = summary(name)
    result["db_queries"] = psql_value(DB_TX) - tx_before
    if env == "cache":
        result["cache_hit_pct"] = cache_stats()
    return result


def lock_scenario(name, migration):
    use_machine("baseline")
    psql("migration-reset.sql")
    k6 = subprocess.Popen(k6_cmd(name, "write.js", 20, "50s"), cwd=LAB, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)
    time.sleep(8)
    long_tx = compose_bg("baseline", "exec", "-T", "db", "psql", "-U", "lab", "-d", "shop", "-f", "/sql/long-transaction.sql")
    time.sleep(4)
    migration_out = RESULTS / f"{name}-migration.txt"
    with migration_out.open("w", encoding="utf-8") as fh:
        mig = compose_bg("baseline", "exec", "-T", "db", "psql", "-U", "lab", "-d", "shop", "-f", f"/sql/{migration}",
                         stdout=fh)
        time.sleep(6)
        (RESULTS / f"{name}-locks.txt").write_text(psql("locks.sql").stdout, encoding="utf-8")
        for proc in (k6, long_tx, mig):
            proc.wait()
    psql("migration-reset.sql")
    return summary(name)


def explain(name):
    (RESULTS / f"{name}.txt").write_text(psql("explain.sql").stdout, encoding="utf-8")


def main():
    RESULTS.mkdir(exist_ok=True)
    compose("baseline", "up", "-d", "--build", "--wait", "--remove-orphans", capture=True)
    psql("index-drop.sql")
    psql("migration-reset.sql")

    results = {}
    results["1-baseline-50rps"] = read_scenario("1-baseline-50rps", "baseline", 50)
    explain("explain-sem-indice")
    results["2-scaleup-50rps"] = read_scenario("2-scaleup-50rps", "scale-up", 50)
    use_machine("baseline")
    psql("index-create.sql")
    explain("explain-com-indice")
    results["3-indice-50rps"] = read_scenario("3-indice-50rps", "baseline", 50)
    for rate in (200, 500):
        results[f"4-indice-{rate}rps"] = read_scenario(f"4-indice-{rate}rps", "baseline", rate)
        results[f"5-indice-valkey-{rate}rps"] = read_scenario(f"5-indice-valkey-{rate}rps", "cache", rate)
    results["6-migracao-sem-timeout"] = lock_scenario("6-migracao-sem-timeout", "migration-unsafe.sql")
    results["7-migracao-com-timeout"] = lock_scenario("7-migracao-com-timeout", "migration-safe.sql")
    use_machine("baseline")

    (RESULTS / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    header = "| Cenário | Requisições | Falhas | p95 (ms) | p99 (ms) | Descartadas | Consultas no banco | Acerto do cache |"
    lines = [header, "|---|---|---|---|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {r['requests']} | {r['failed_pct']}% | {r['p95_ms']} | {r['p99_ms']} | {r['dropped']} | "
                     f"{r.get('db_queries', '-')} | {str(r['cache_hit_pct']) + '%' if 'cache_hit_pct' in r else '-'} |")
    table = "\n".join(lines)
    (RESULTS / "results.md").write_text(table + "\n", encoding="utf-8")
    print(table)


if __name__ == "__main__":
    sys.exit(main())
