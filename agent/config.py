"""
config.py — Configuration & Health Thresholds
Laptop Life-Saver System | Nyanza District
"""

import os
import socket
import platform
from dotenv import load_dotenv

# ── Load environment variables ──────────────────────────────────────
# Find the root .env file regardless of where we start from
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_base_dir, ".env")
load_dotenv(_env_path)

# ── Supabase credentials ────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ── Device identity ─────────────────────────────────────────────────
DEVICE_HOSTNAME = socket.gethostname()
OS_VERSION = f"{platform.system()} {platform.release()} {platform.version()}"

# ── Agent timing ────────────────────────────────────────────────────
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))   # seconds between readings

# ── Circular buffer ─────────────────────────────────────────────────
BUFFER_MAX_SIZE = 1000
BUFFER_FILE = os.path.join(os.path.dirname(__file__), "local_buffer.json")

# ── Health thresholds ───────────────────────────────────────────────
#  Based on research for Nyanza District laptop fleet.
#
#  Status       CPU Temp (°C)        Disk Usage (%)
#  ──────────   ──────────────       ──────────────
#  GREEN        < 60                 < 80
#  YELLOW       60 – 80              80 – 95
#  RED          > 80 (sustained 60s) > 95

THRESHOLDS = {
    "cpu_temp": {
        "green_max":   60,    # below this → healthy
        "yellow_max":  80,    # below this → warning, above → critical
        "sustain_secs": 60,   # seconds temp must stay > yellow_max for RED
    },
    "disk_usage": {
        "green_max":   80,
        "yellow_max":  95,
    },
}

# ── Version (for future auto-update check) ──────────────────────────
AGENT_VERSION = "1.0.0"
