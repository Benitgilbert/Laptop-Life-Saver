"""
config.py — Configuration & Health Thresholds
Laptop Life-Saver System | Nyanza District
"""

import os
import sys
import socket
import platform
from dotenv import load_dotenv

# ── Load environment variables ──────────────────────────────────────
# Try to find the .env file
if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle, look in _MEIPASS
    _env_path = os.path.join(sys._MEIPASS, ".env")
else:
    # Development: Look in the root folder (parent of 'agent')
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(_env_path):
        _env_path = os.path.join(os.getcwd(), ".env")

if os.path.exists(_env_path):
    load_dotenv(_env_path)
else:
    # Final fallback to standard search
    load_dotenv()

# ── Supabase credentials ────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Fallback to user_config.json in AppData if not in .env
if not SUPABASE_URL or not SUPABASE_KEY:
    import json
    appdata_path = os.path.join(os.environ.get("LOCALAPPDATA", "."), "LaptopLifeSaver")
    config_path = os.path.join(appdata_path, "user_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
                if not SUPABASE_URL: SUPABASE_URL = cfg.get("supabase_url", "")
                if not SUPABASE_KEY: SUPABASE_KEY = cfg.get("supabase_key", "")
        except Exception:
            pass

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
