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
import os
import threading
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

# ── Load environment variables (CRITICAL) ───────────────────────────
load_dotenv()

# ── Logging setup (Must be early) ───────────────────────────────────
import logging.handlers

appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", "."), "LaptopLifeSaver")
if not os.path.exists(appdata_path):
    os.makedirs(appdata_path, exist_ok=True)
log_file = os.path.join(appdata_path, "agent.log")

# Create handlers
c_handler = logging.StreamHandler(sys.stdout)
f_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)

# Create formatters and add it to handlers
log_format = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
c_handler.setFormatter(log_format)
f_handler.setFormatter(log_format)

# Add handlers to the logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[c_handler, f_handler]
)

logger = logging.getLogger("agent")
logger.info(f"Logging to file: {log_file}")

from agent.config import POLL_INTERVAL, THRESHOLDS, AGENT_VERSION
from agent.hardware_monitor import collect_snapshot
from agent.local_buffer import CircularBuffer
from agent.cloud_sync import register_device, send_telemetry, send_alert, flush_buffer
from agent.data_retention import should_run_cleanup, aggregate_and_cleanup, mark_cleanup_done
from agent.utils import get_resource_path, get_install_path, is_running_from_install_path
import shutil
import ctypes
import subprocess

# Logging is already setup above
# ── Global state for threading ─────────────────────────────────────
_stop_event = threading.Event()

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

def main_loop(device_id: Optional[str], buffer: CircularBuffer) -> None:
    cycle = 0
    try:
        while not _stop_event.is_set():
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

            # Step 3 — Local safety checks (proactive alerts)
            check_local_safety_alerts(snapshot)

            # Step 4 — Sync to cloud (or buffer)
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

            # Step 6 — Remote Action Check (Phase 1)
            if device_id:
                check_remote_actions(device_id, buffer)

            # Step 7 — Sleep (accounting for processing time)
            cycle_end = time.time()
            cycle_duration = cycle_end - cycle_start
            sleep_time = max(0, POLL_INTERVAL - cycle_duration)
            
            
            
            logger.info("Cycle took %.2fs, sleeping %.2fs...\n", cycle_duration, sleep_time)
            
            # Sleep in small chunks to remain responsive to stop_event
            for _ in range(int(sleep_time * 2)):
                if _stop_event.is_set(): break
                time.sleep(0.5)

    except Exception as e:
        logger.error("Main loop crashed: %s", e)

def load_user_config() -> Optional[dict]:
    """Load user metadata from local JSON, or return None if first run."""
    # Config is stored in user's AppData to avoid permission issues in Program Files
    appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", "."), "LaptopLifeSaver")
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path, exist_ok=True)
    
    config_path = os.path.join(appdata_path, "user_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                import json
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load user config: %s", e)
    return None

def check_for_installation():
    """If not in Program Files, ask to move there."""
    if is_running_from_install_path():
        return

    # Check if we are already 'installed' but just running a new version from elsewhere
    install_folder = get_install_path()
    target_exe = os.path.join(install_folder, "LaptopLifeSaver_Agent.exe")
    
    # If running from a temp folder or downloads, propose installation
    if not ctypes.windll.shell32.IsUserAnAdmin():
        logger.info("Relaunching as admin for installation...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
        sys.exit(0)

    # Perform Installation
    if not os.path.exists(install_folder):
        os.makedirs(install_folder, exist_ok=True)
    
    logger.info(f"Installing agent to {install_folder}...")
    try:
        shutil.copy2(sys.executable, target_exe)
        # Copy logo if it exists locally, though we also embed it
        src_logo = os.path.join(os.path.dirname(sys.executable), "Logo.png")
        if os.path.exists(src_logo):
            shutil.copy2(src_logo, os.path.join(install_folder, "Logo.png"))
            
        # Create a basic .env if URL/Key passed or use defaults
        # (This would be handled by the wizard usually)
        
        logger.info("Installation complete. Launching installed agent...")
        subprocess.Popen([target_exe])
        sys.exit(0)
    except Exception as e:
        logger.error(f"Installation failed: {e}")

def main() -> None:
    # Trigger self-installation if needed
    if getattr(sys, 'frozen', False):
        check_for_installation()

    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Laptop Life-Saver Agent v%s", AGENT_VERSION)
    logger.info("  Poll interval: %ds", POLL_INTERVAL)
    logger.info("═══════════════════════════════════════════════════")

    # Step 0 — Check for User Setup (First Run)
    user_info = load_user_config()
    if not user_info:
        logger.info("First run detected — launching Setup Wizard...")
        from agent.setup_wizard import run_wizard
        logo_path = get_resource_path("Logo.png")
        appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", "."), "LaptopLifeSaver")
        config_path = os.path.join(appdata_path, "user_config.json")
        user_info = run_wizard(logo_path, config_path)
        
    # Step 1 — Register device (with initial hardware inventory and user info)
    boot_snapshot = collect_snapshot()
    device_id = register_device(boot_snapshot, user_info=user_info)
    if device_id:
        logger.info("Device ID: %s", device_id)
        cleanup_stuck_actions(device_id)
    
    buffer = CircularBuffer()
    
    # Start the monitoring loop in a background thread
    daemon_thread = threading.Thread(
        target=main_loop, 
        args=(device_id, buffer), 
        daemon=True
    )
    daemon_thread.start()

    # Start the Tray Icon on the main thread (blocking)
    from agent.tray import AgentTray
    logo_path = get_resource_path("Logo.png")
    
    def on_exit():
        logger.info("Shutting down agent...")
        _stop_event.set()

    tray = AgentTray(logo_path, on_exit=on_exit)
    tray.run()


def check_remote_actions(device_id: str, buffer: CircularBuffer) -> None:
    """Check for pending commands in the `remote_actions` table."""
    from agent.cloud_sync import get_supabase
    client = get_supabase()
    if client is None:
        return

    try:
        # Get pending actions for this device
        result = (
            client.table("remote_actions")
            .select("*")
            .eq("device_id", device_id)
            .eq("status", "pending")
            .execute()
        )
        
        for action in result.data:
            action_id = action["id"]
            command = action["command"]
            logger.info("⚡ Remote Action received: %s", command)
            
            # Mark as processing
            client.table("remote_actions").update({"status": "processing"}).eq("id", action_id).execute()
            
            try:
                logger.info("⚡ Executing Remote Action: %s", command)
                if command == "FORCE_SYNC":
                    # Step 2 — Read hardware sensors
                    snapshot = collect_snapshot()
                    health = classify_health(snapshot)
                    snapshot["health_status"] = health
                    from agent.cloud_sync import send_telemetry, flush_buffer
                    if send_telemetry(device_id, snapshot):
                        flush_buffer(buffer, device_id)
                elif command == "SHOW_NOTIFICATION":
                    message = action.get("params", {}).get("message", "IT Maintenance Note")
                    from agent.notifications import show_toast
                    show_toast("Message from IT Admin", message)
                
                # Mark as completed
                client.table("remote_actions").update({
                    "status": "completed", 
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", action_id).execute()
                logger.info("✓ Remote Action completed: %s", command)
                
            except Exception as e:
                logger.error("✗ Remote Action failed: %s", str(e))
                client.table("remote_actions").update({
                    "status": "failed", 
                    "error_message": str(e)
                }).eq("id", action_id).execute()

    except Exception as exc:
        logger.error("Failed to check remote actions: %s", exc)

def cleanup_stuck_actions(device_id: str) -> None:
    """Reset any actions stuck in 'processing' from a previous crash."""
    from agent.cloud_sync import get_supabase
    client = get_supabase()
    if client is None:
        return

    try:
        # Check for processing actions
        result = client.table("remote_actions") \
            .select("id") \
            .eq("device_id", device_id) \
            .eq("status", "processing") \
            .execute()
        
        if result.data:
            logger.info("Found %d stuck actions — resetting to failed", len(result.data))
            for action in result.data:
                client.table("remote_actions").update({
                    "status": "failed",
                    "error_message": "Agent process interrupted/crashed"
                }).eq("id", action["id"]).execute()
    except Exception as e:
        logger.error("Failed to cleanup stuck actions: %s", e)

def check_local_safety_alerts(snapshot: dict) -> None:
    """Trigger local toast notifications if critical thresholds are breached."""
    from agent.notifications import notify_high_temp, notify_disk_full, notify_low_battery
    
    # 1. Temperature Check
    temp = snapshot.get("cpu_temp_c")
    if temp and temp >= 85: # TODO: Load from config
        notify_high_temp(temp)
        
    # 2. Disk Check
    disk = snapshot.get("disk_usage_pct")
    if disk and disk >= 95:
        notify_disk_full(disk)
        
    # 3. Battery Check
    battery = snapshot.get("battery_percent")
    plugged = snapshot.get("battery_plugged")
    if battery and battery <= 15 and not plugged:
        notify_low_battery(battery)


if __name__ == "__main__":
    main()
