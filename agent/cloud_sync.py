"""
cloud_sync.py — Supabase Cloud Synchronisation
Laptop Life-Saver System | Nyanza District

Handles device registration, telemetry uploads, and offline buffer flush.
"""

import logging
from typing import Optional

from .config import SUPABASE_URL, SUPABASE_KEY, DEVICE_HOSTNAME, OS_VERSION

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

def register_device() -> Optional[str]:
    """
    Upsert the current device into the `devices` table.
    Returns the device UUID on success, or None on failure.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        result = (
            client.table("devices")
            .upsert(
                {"hostname": DEVICE_HOSTNAME, "os_version": OS_VERSION},
                on_conflict="hostname",
            )
            .execute()
        )
        device_id = result.data[0]["id"]
        logger.info("Device registered: %s (%s)", DEVICE_HOSTNAME, device_id)
        return device_id
    except Exception as exc:
        logger.error("Device registration failed: %s", exc)
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
        payload = {**record, "device_id": device_id}
        client.table("telemetry").insert(payload).execute()
        return True
    except Exception as exc:
        logger.error("Telemetry send failed: %s", exc)
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
