"""
data_retention.py — Automatic Data Retention & Aggregation
Laptop Life-Saver System | Nyanza District

Strategy:
  • Raw telemetry kept for 30 days (full 30-second granularity)
  • Older data aggregated into hourly summaries (avg, min, max)
  • Raw rows older than 30 days are deleted after aggregation
  • Cleanup runs once per day inside the agent loop
"""

import logging
import datetime
from agent.cloud_sync import get_supabase

logger = logging.getLogger("retention")

# ── Configuration ──────────────────────────────────────────────────
RAW_RETENTION_DAYS = 30     # Keep raw telemetry for 30 days
CLEANUP_INTERVAL_HOURS = 24 # Run cleanup once per day

_last_cleanup: float | None = None


def _cutoff_iso(days: int) -> str:
    """Return ISO timestamp for `days` ago."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    return cutoff.isoformat()


def aggregate_and_cleanup(device_id: str | None = None) -> dict:
    """
    1. Aggregate raw telemetry older than RAW_RETENTION_DAYS into hourly buckets
    2. Delete the aggregated raw rows
    
    Returns summary: { aggregated: int, deleted: int, errors: [] }
    """
    supabase = get_supabase()
    if supabase is None:
        logger.warning("Supabase unavailable — skipping cleanup")
        return {"aggregated": 0, "deleted": 0, "errors": ["supabase_offline"]}

    cutoff = _cutoff_iso(RAW_RETENTION_DAYS)
    result = {"aggregated": 0, "deleted": 0, "errors": []}

    try:
        # ── Step 1: Get old raw rows grouped by device + hour ──────
        query = supabase.from_("telemetry") \
            .select("*") \
            .lt("recorded_at", cutoff) \
            .order("recorded_at")
        
        if device_id:
            query = query.eq("device_id", device_id)

        response = query.execute()
        old_rows = response.data if response.data else []

        if not old_rows:
            logger.info("No telemetry older than %d days — nothing to clean", RAW_RETENTION_DAYS)
            return result

        # ── Step 2: Group by (device_id, hour) and aggregate ──────
        hourly_buckets: dict[tuple[str, str], list[dict]] = {}
        for row in old_rows:
            ts = datetime.datetime.fromisoformat(row["recorded_at"].replace("Z", "+00:00"))
            hour_key = ts.strftime("%Y-%m-%dT%H:00:00+00:00")
            bucket_key = (row["device_id"], hour_key)
            hourly_buckets.setdefault(bucket_key, []).append(row)

        # ── Step 3: Insert hourly summaries ───────────────────────
        for (dev_id, hour_ts), rows in hourly_buckets.items():
            summary = _build_hourly_summary(dev_id, hour_ts, rows)
            
            # Upsert: avoid duplicates if cleanup runs twice
            resp = supabase.from_("telemetry_hourly") \
                .upsert(summary, on_conflict="device_id,hour_timestamp") \
                .execute()
            
            if resp.data:
                result["aggregated"] += 1

        # ── Step 4: Delete the old raw rows ───────────────────────
        del_query = supabase.from_("telemetry") \
            .delete() \
            .lt("recorded_at", cutoff)
        
        if device_id:
            del_query = del_query.eq("device_id", device_id)

        del_resp = del_query.execute()
        result["deleted"] = len(del_resp.data) if del_resp.data else 0

        logger.info(
            "Retention cleanup: aggregated %d hourly buckets, deleted %d raw rows",
            result["aggregated"], result["deleted"]
        )

    except Exception as e:
        logger.error("Retention cleanup failed: %s", e)
        result["errors"].append(str(e))

    return result


def _build_hourly_summary(device_id: str, hour_ts: str, rows: list[dict]) -> dict:
    """Build an averaged hourly summary from a batch of raw telemetry rows."""
    def avg(field: str) -> float | None:
        vals = [r[field] for r in rows if r.get(field) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    def min_val(field: str) -> float | None:
        vals = [r[field] for r in rows if r.get(field) is not None]
        return min(vals) if vals else None

    def max_val(field: str) -> float | None:
        vals = [r[field] for r in rows if r.get(field) is not None]
        return max(vals) if vals else None

    # Determine dominant health status (worst health in the hour)
    health_priority = {"red": 3, "yellow": 2, "green": 1}
    worst_health = max(
        (r["health_status"] for r in rows if r.get("health_status")),
        key=lambda h: health_priority.get(h, 0),
        default="green"
    )

    return {
        "device_id":        device_id,
        "hour_timestamp":   hour_ts,
        "sample_count":     len(rows),
        "avg_cpu_temp":     avg("cpu_temp_c"),
        "min_cpu_temp":     min_val("cpu_temp_c"),
        "max_cpu_temp":     max_val("cpu_temp_c"),
        "avg_cpu_usage":    avg("cpu_usage_pct"),
        "avg_ram_usage":    avg("ram_usage_pct"),
        "avg_disk_usage":   avg("disk_usage_pct"),
        "avg_battery":      avg("battery_percent"),
        "worst_health":     worst_health,
    }


def should_run_cleanup() -> bool:
    """Check if enough time has passed since last cleanup."""
    import time
    global _last_cleanup
    
    if _last_cleanup is None:
        return True
    
    elapsed_hours = (time.time() - _last_cleanup) / 3600
    return elapsed_hours >= CLEANUP_INTERVAL_HOURS


def mark_cleanup_done() -> None:
    """Record that cleanup has been performed."""
    import time
    global _last_cleanup
    _last_cleanup = time.time()
