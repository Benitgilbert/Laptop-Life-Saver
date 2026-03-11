import logging
from typing import Optional

from .config import SUPABASE_URL, SUPABASE_KEY, DEVICE_HOSTNAME, OS_VERSION
from .hardware_monitor import get_mac_address

logger = logging.getLogger(__name__)

# ── Supabase client (lazy init) ─────────────────────────────────────
_client = None


def _get_client():
    """Lazily create the Supabase client so import doesn't fail without creds."""
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not configured — running offline only")
        return None
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialised")
        return _client
    except Exception as exc:
        logger.error("Failed to create Supabase client: %s", exc)
        return None


def get_supabase():
    """Public helper — returns the Supabase client (or None)."""
    return _get_client()


# ─────────────────────────────────────────────────────────────────────
#  Device registration
# ─────────────────────────────────────────────────────────────────────

def register_device(inventory: Optional[dict] = None, user_info: Optional[dict] = None) -> Optional[str]:
    """
    Upsert the current device into the `devices` table.
    Returns the device UUID on success, or None on failure.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        payload = {
            "hostname": DEVICE_HOSTNAME, 
            "os_version": OS_VERSION,
            "mac_address": get_mac_address()
        }
        
        # Add user metadata if provided (from first-run setup)
        if user_info:
            if "assigned_user" in user_info: payload["assigned_user"] = user_info["assigned_user"]
            if "department" in user_info: payload["location"] = user_info["department"]
            if "asset_tag" in user_info: payload["asset_tag"] = user_info["asset_tag"]
            # Email could be added to assigned_user or a new column if exists
            if "user_email" in user_info and user_info["user_email"]:
                payload["assigned_user"] = f"{payload.get('assigned_user', '')} <{user_info['user_email']}>".strip()
        
        # Add hardware inventory if provided
        if inventory:
            if "cpu_model" in inventory: payload["cpu_model"] = inventory["cpu_model"]
            if "ram_size_gb" in inventory: payload["ram_size_gb"] = inventory["ram_size_gb"]
            if "disk_type" in inventory: payload["disk_type"] = inventory["disk_type"]

        result = (
            client.table("devices")
            .upsert(payload, on_conflict="mac_address")
            .execute()
        )
        
        if not result.data:
            logger.error("Device registration returned no data. Check RLS policies or database constraints.")
            return None
            
        device_id = result.data[0]["id"]
        logger.info("Device registered: %s (%s)", DEVICE_HOSTNAME, device_id)
        return device_id
    except Exception as exc:
        logger.error("Device registration failed: %s", exc, exc_info=True)
        return None


# ─────────────────────────────────────────────────────────────────────
#  Telemetry upload
# ─────────────────────────────────────────────────────────────────────

def send_telemetry(device_id: str, record: dict) -> bool:
    """
    Insert a single telemetry record into Supabase.
    Returns True on success, False on failure (record should be buffered).
    """
    client = _get_client()
    if client is None:
        return False
    try:
        # Filter payload to only include columns defined in the `telemetry` table
        # We exclude static inventory fields like cpu_model, ram_size_gb, disk_type
        # which are stored in the `devices` table.
        allowed_keys = {
            "device_id", "recorded_at", "cpu_temp_c", "cpu_usage_pct", 
            "battery_percent", "battery_plugged", "ram_usage_pct", 
            "disk_usage_pct", "top_process", "health_status", 
            "disk_health", "disk_wear_pct", "mac_address"
        }
        
        payload = {k: v for k, v in record.items() if k in allowed_keys}
        payload["device_id"] = device_id
        
        client.table("telemetry").insert(payload).execute()
        return True
    except Exception as exc:
        logger.error("Telemetry send failed (Device ID: %s): %s", device_id, exc)
        return False


def send_alert(device_id: str, alert_type: str, severity: str, message: str) -> bool:
    """Insert an alert row into the `alerts` table."""
    client = _get_client()
    if client is None:
        return False
    try:
        client.table("alerts").insert({
            "device_id": device_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
        }).execute()
        logger.info("Alert sent: %s — %s", alert_type, severity)
        return True
    except Exception as exc:
        logger.error("Alert send failed: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────
#  Buffer flush
# ─────────────────────────────────────────────────────────────────────

def flush_buffer(buffer, device_id: str) -> int:
    """
    Attempt to push all buffered records to Supabase.
    Returns the number of successfully sent records.
    """
    records = buffer.peek()
    if not records:
        return 0

    sent = 0
    for record in records:
        if send_telemetry(device_id, record):
            sent += 1
        else:
            break  # stop on first failure — network likely down

    if sent > 0:
        # Remove the sent records from the buffer
        buffer.remove_first(sent)
        logger.info("Flushed %d/%d buffered records", sent, len(records))

    return sent
