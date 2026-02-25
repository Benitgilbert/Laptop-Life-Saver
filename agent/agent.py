"""
agent.py — Main Agent Loop
Laptop Life-Saver System | Nyanza District

Implements the Agent Logic Flowchart:
  Start → Register Device → [loop] Read Sensors → Classify Health →
  Online? → Send / Buffer → Sleep → [repeat]
"""

import logging
import sys
import time
from typing import Optional

from agent.config import POLL_INTERVAL, THRESHOLDS, AGENT_VERSION
from agent.hardware_monitor import collect_snapshot
from agent.local_buffer import CircularBuffer
from agent.cloud_sync import register_device, send_telemetry, send_alert, flush_buffer
from agent.data_retention import should_run_cleanup, aggregate_and_cleanup, mark_cleanup_done

# ── Logging setup ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent")

# ── Sustained-temperature tracker ────────────────────────────────────────
_high_temp_start: Optional[float] = None

# ─────────────────────────────────────────────────────────────────────
#  Health classification
# ─────────────────────────────────────────────────────────────────────

def classify_health(snapshot: dict) -> str:
    """
    Return 'green', 'yellow', or 'red' based on thresholds.
    CPU temp must be sustained above yellow_max for `sustain_secs`
    before escalating to red.
    """
    global _high_temp_start

    temp = snapshot["cpu_temp_c"]
    disk = snapshot["disk_usage_pct"]
    t_cfg = THRESHOLDS["cpu_temp"]
    d_cfg = THRESHOLDS["disk_usage"]

    status = "green"

    # ── Disk rules ──────────────────────────────────────────────────
    if disk >= d_cfg["yellow_max"]:
        status = "red"
    elif disk >= d_cfg["green_max"]:
        status = "yellow"

    # ── CPU temp rules (can escalate but never downgrade) ───────────
    if temp >= t_cfg["yellow_max"]:
        # Track sustained high temp
        if _high_temp_start is None:
            _high_temp_start = time.time()
        elapsed = time.time() - _high_temp_start
        if elapsed >= t_cfg["sustain_secs"]:
            status = "red"
        elif status != "red":
            status = "yellow"
    elif temp >= t_cfg["green_max"]:
        _high_temp_start = None  # reset sustained counter
        if status == "green":
            status = "yellow"
    else:
        _high_temp_start = None

    return status


# ─────────────────────────────────────────────────────────────────────
#  Main loop
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Laptop Life-Saver Agent v%s", AGENT_VERSION)
    logger.info("  Poll interval: %ds", POLL_INTERVAL)
    logger.info("═══════════════════════════════════════════════════")

    # Step 1 — Register device with Supabase (returns None if offline)
    device_id = register_device()
    if device_id:
        logger.info("Device ID: %s", device_id)
    else:
        logger.warning("Running in OFFLINE mode — data buffered locally")

    # Initialise circular buffer
    buffer = CircularBuffer()
    logger.info("Buffer loaded: %d existing records", len(buffer))

    cycle = 0
    try:
        while True:
            cycle_start = time.time()
            cycle += 1
            logger.info("── Cycle %d ────────────────────────────────────────", cycle)

            # Step 2 — Read hardware sensors
            snapshot = collect_snapshot()
            battery_display = "N/A" if snapshot["battery_percent"] is None else f"{snapshot['battery_percent']}%"
            logger.info(
                "Temp=%.1f°C | CPU=%.1f%% | Battery=%s | RAM=%.1f%% | Disk=%.1f%% | Top=%s",
                snapshot["cpu_temp_c"],
                snapshot["cpu_usage_pct"],
                battery_display,
                snapshot["ram_usage_pct"],
                snapshot["disk_usage_pct"],
                snapshot["top_process"],
            )

            # Step 3 — Classify health
            health = classify_health(snapshot)
            snapshot["health_status"] = health
            logger.info("Health status: %s", health.upper())

            # Step 4 — Send or buffer
            sent = False
            if device_id:
                sent = send_telemetry(device_id, snapshot)

            if sent:
                logger.info("✓ Telemetry sent to Supabase")
                # Also try to flush any buffered offline records
                flushed = flush_buffer(buffer, device_id)
                if flushed:
                    logger.info("✓ Flushed %d buffered records", flushed)
            else:
                buffer.append(snapshot)
                logger.info("✗ Offline — buffered locally (%d total)", len(buffer))

            # Step 5 — Daily data retention cleanup
            if device_id and should_run_cleanup():
                logger.info("Running daily data retention cleanup...")
                result = aggregate_and_cleanup()
                mark_cleanup_done()
                if result["deleted"] > 0:
                    logger.info(
                        "Cleanup complete: %d hourly buckets, %d raw rows deleted",
                        result["aggregated"], result["deleted"]
                    )

            # Step 7 — Sleep (accounting for processing time)
            cycle_end = time.time()
            cycle_duration = cycle_end - cycle_start
            sleep_time = max(0, POLL_INTERVAL - cycle_duration)
            
            logger.info("Cycle took %.2fs, sleeping %.2fs...\n", cycle_duration, sleep_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("\nAgent stopped by user. Buffer has %d records.", len(buffer))
        sys.exit(0)


if __name__ == "__main__":
    main()
