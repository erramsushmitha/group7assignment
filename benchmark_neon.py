"""Group 7 Neon PostgreSQL latency experiment.

Run after setting DATABASE_URL. Results are written to neon_results.csv
and a short summary is written to neon_summary.txt.
"""
import csv
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import psycopg2
from psycopg2 import sql

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise SystemExit("ERROR: DATABASE_URL is not set. Set it in PowerShell first.")

CSV_FILE = "neon_results.csv"
SUMMARY_FILE = "neon_summary.txt"


def connect():
    return psycopg2.connect(DB_URL, connect_timeout=20, application_name="group7_neon_benchmark")


def ensure_table():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS group7_benchmark (
                    id BIGSERIAL PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("SELECT COUNT(*) FROM group7_benchmark")
            count = cur.fetchone()[0]
            if count < 5000:
                cur.execute("""
                    INSERT INTO group7_benchmark(payload)
                    SELECT 'Group 7 sample record ' || g
                    FROM generate_series(%s, 5000) AS g
                """, (count + 1,))
            cur.execute("CREATE INDEX IF NOT EXISTS idx_group7_benchmark_created_at ON group7_benchmark(created_at)")


def timed_query(condition, trial):
    started = time.perf_counter()
    status = "success"
    error = ""
    row_count = ""
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*), MAX(id) FROM group7_benchmark WHERE id > 0")
                row_count, _ = cur.fetchone()
    except Exception as exc:
        status = "error"
        error = str(exc).replace("\n", " ")[:300]
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "condition": condition,
        "trial": trial,
        "elapsed_ms": round(elapsed_ms, 3),
        "status": status,
        "row_count": row_count,
        "error": error,
    }


def main():
    print("Group 7 Neon benchmark starting...")
    print("Preparing table and 5,000 sample records...")
    ensure_table()
    rows = []

    print("Running 10 warm-query trials...")
    for i in range(1, 11):
        result = timed_query("warm", i)
        rows.append(result)
        print(f"warm trial {i}: {result['elapsed_ms']} ms ({result['status']})")
        time.sleep(1)

    print("\nWaiting 370 seconds (just over six minutes) to allow free compute to suspend...")
    print("Keep this terminal open. Do not run queries against this project during the wait.")
    for remaining in range(370, 0, -10):
        print(f"Idle wait: approximately {remaining} seconds remaining")
        time.sleep(min(10, remaining))

    print("\nMeasuring first request after idle...")
    first = timed_query("first_after_idle", 1)
    rows.append(first)
    print(f"first_after_idle: {first['elapsed_ms']} ms ({first['status']})")

    print("Running 5 subsequent requests after resume...")
    for i in range(1, 6):
        result = timed_query("after_resume", i)
        rows.append(result)
        print(f"after_resume trial {i}: {result['elapsed_ms']} ms ({result['status']})")
        time.sleep(1)

    print("\nRunning 10 concurrent requests...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(timed_query, "concurrent_burst", i) for i in range(1, 11)]
        for future in as_completed(futures):
            result = future.result()
            rows.append(result)
            print(f"concurrent trial {result['trial']}: {result['elapsed_ms']} ms ({result['status']})")

    fields = ["timestamp_utc", "condition", "trial", "elapsed_ms", "status", "row_count", "error"]
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    lines = ["Group 7 Neon PostgreSQL benchmark summary", f"Generated UTC: {datetime.now(timezone.utc).isoformat()}", ""]
    for condition in ["warm", "first_after_idle", "after_resume", "concurrent_burst"]:
        values = [r["elapsed_ms"] for r in rows if r["condition"] == condition and r["status"] == "success"]
        errors = sum(1 for r in rows if r["condition"] == condition and r["status"] != "success")
        if values:
            lines.append(f"{condition}: n={len(values)}, mean_ms={statistics.mean(values):.3f}, median_ms={statistics.median(values):.3f}, min_ms={min(values):.3f}, max_ms={max(values):.3f}, errors={errors}")
        else:
            lines.append(f"{condition}: no successful measurements; errors={errors}")
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nFinished. Saved {len(rows)} measurements to {CSV_FILE}")
    print(f"Summary saved to {SUMMARY_FILE}")
    print("Check the status column; failed trials must be investigated before reporting results.")


if __name__ == "__main__":
    main()
