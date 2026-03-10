"""
hardware_monitor.py — Hardware Sensor Reads
Laptop Life-Saver System | Nyanza District

Uses psutil for cross-platform metrics and WMI for Windows-specific
CPU temperature via MSAcpi_ThermalZoneTemperature.
"""

import datetime
import logging
import platform
import subprocess
from typing import Any, Optional

import psutil
import uuid

logger = logging.getLogger(__name__)

def get_mac_address() -> str:
    """Return the MAC address of the primary network interface."""
    try:
        # Get MAC address in a human-readable format (e.g., '00:1A:2B:3C:4D:5E')
        mac_num = uuid.getnode()
        mac_hex = ':'.join(['{:02x}'.format((mac_num >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
        return mac_hex.upper()
    except Exception as e:
        logger.error(f"Failed to get MAC address: {e}")
        return "00:00:00:00:00:00"

# ── WMI import (Windows-only, graceful fallback) ────────────────
_wmi_client: Any = None
WMI_AVAILABLE: bool = False
_temp_method: str | None = None  # Will be determined on first call

try:
    import wmi                        # type: ignore
    _wmi_client = wmi.WMI(namespace=r"root\wmi")
    WMI_AVAILABLE = True
except Exception:
    pass  # Will try alternative methods


# ─────────────────────────────────────────────────────────────────────
#  Individual sensor readers
# ─────────────────────────────────────────────────────────────────────

def read_cpu_temp() -> float:
    """
    Return CPU temperature in °C.
    Tries multiple methods: WMI (Windows), psutil sensors, fallback to 0.0
    """
    global _temp_method
    
    # First call: determine which method works
    if _temp_method is None:
        # Try WMI first (Windows-specific)
        if WMI_AVAILABLE and _wmi_client is not None:
            try:
                assert _wmi_client is not None
                sensors = _wmi_client.MSAcpi_ThermalZoneTemperature()
                if sensors:
                    kelvin = sensors[0].CurrentTemperature / 10.0
                    _temp_method = "wmi"
                    logger.info("Temperature monitoring: using WMI")
                    return round(kelvin - 273.15, 1)
            except Exception as exc:
                logger.debug("WMI temp read failed: %s", exc)
        
        # Try psutil sensors (cross-platform)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Try common sensor names
                for name in ['coretemp', 'cpu_thermal', 'k10temp', 'zenpower']:
                    if name in temps and temps[name]:
                        _temp_method = "psutil"
                        logger.info("Temperature monitoring: using psutil (%s)", name)
                        return round(temps[name][0].current, 1)
        except Exception as exc:
            logger.debug("psutil temp read failed: %s", exc)
        
        # No method works
        _temp_method = "unavailable"
        logger.warning("Temperature monitoring unavailable - will report 0°C (try running as administrator)")
        return 0.0
    
    # Subsequent calls: use determined method
    try:
        if _temp_method == "wmi" and _wmi_client is not None:
            sensors = _wmi_client.MSAcpi_ThermalZoneTemperature()
            if sensors:
                kelvin = sensors[0].CurrentTemperature / 10.0
                return round(kelvin - 273.15, 1)
        elif _temp_method == "psutil":
            temps = psutil.sensors_temperatures()
            for name in ['coretemp', 'cpu_thermal', 'k10temp', 'zenpower']:
                if name in temps and temps[name]:
                    return round(temps[name][0].current, 1)
    except Exception as exc:
        logger.debug("Temp read failed: %s", exc)
    
    return 0.0


def read_battery_health() -> dict:
    """Return battery percent and plug status. Returns None for desktop systems."""
    bat = psutil.sensors_battery()
    if bat is None:
        # Desktop system or battery not detectable
        return {"percent": None, "plugged": None}
    return {"percent": bat.percent, "plugged": bat.power_plugged}


def read_cpu_usage() -> float:
    """Return CPU usage as a percentage (0-100)."""
    return psutil.cpu_percent(interval=1)


def read_ram_usage() -> float:
    """Return RAM usage as a percentage (0-100)."""
    return psutil.virtual_memory().percent


def read_disk_usage() -> float:
    """Return disk usage % for the system drive."""
    import sys
    import os
    try:
        # Get system drive (cross-platform)
        if sys.platform == "win32":
            # Windows: use system drive (usually C:)
            path = os.getenv('SystemDrive', 'C:')
            if not path.endswith('\\'):
                path += '\\'
        else:
            # Unix-like: use root
            path = "/"
        
        return psutil.disk_usage(path).percent
    except Exception as exc:
        logger.error("Failed to read disk usage: %s", exc)
        return 0.0  # Return 0 on error to avoid crashing


def top_memory_process() -> str:
    """Return the name of the process using the most memory."""
    top: str = "N/A"
    top_mem = 0.0
    for proc in psutil.process_iter(["name", "memory_percent"]):
        try:
            mem = proc.info["memory_percent"] or 0.0
            if mem > top_mem:
                top_mem = mem
                top = proc.info["name"] or "N/A"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return top


# ── Inventory & S.M.A.R.T. (Phase 1) ───────────────────────────────

def get_cpu_model() -> str:
    """Return the CPU model name (e.g., 'Intel Core i7-10700K')."""
    try:
        if platform.system() == "Windows":
            cmd = "wmic cpu get name"
            output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            if len(lines) > 1:
                return lines[1]
        elif platform.system() == "Darwin":
            cmd = "sysctl -n machdep.cpu.brand_string"
            return subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
        elif platform.system() == "Linux":
            cmd = "grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2"
            return subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"


def get_ram_size_gb() -> float:
    """Return total RAM size in GB."""
    return round(psutil.virtual_memory().total / (1024**3), 1)


def get_disk_info() -> dict:
    """
    Return disk type (SSD/HDD) and basic S.M.A.R.T. health if possible.
    Note: True S.M.A.R.T. requires admin/root.
    """
    info = {
        "type": "Unknown",
        "health": "GOOD",
        "wear_pct": None
    }
    
    try:
        if platform.system() == "Windows":
            # Check for SSD vs HDD via PowerShell
            cmd = "powershell -Command \"Get-PhysicalDisk | Select-Object MediaType, Status\""
            output = subprocess.check_output(cmd, shell=True, timeout=5).decode().strip()
            if "SSD" in output:
                info["type"] = "SSD"
            elif "HDD" in output:
                info["type"] = "HDD"
            
            if "Healthy" not in output and "OK" not in output:
                info["health"] = "WARNING"
                
            # Try to get wear for SSD (Heuristic: Windows doesn't make this easy without specific vendor tools)
            # But we can check for predicted failure
            cmd_fail = "wmic diskdrive get status"
            output_fail = subprocess.check_output(cmd_fail, shell=True, timeout=5).decode().strip()
            if "PredFail" in output_fail:
                info["health"] = "FAILING"
                
    except Exception:
        pass
        
    return info


# ─────────────────────────────────────────────────────────────────────
#  Composite snapshot
# ─────────────────────────────────────────────────────────────────────

def collect_snapshot() -> dict:
    """
    Gather one complete hardware reading and return a flat dict.
    This is the single function the main loop calls each cycle.
    """
    battery = read_battery_health()
    disk_info = get_disk_info()
    
    return {
        "recorded_at":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
        
        # Performance
        "cpu_temp_c":     read_cpu_temp(),
        "cpu_usage_pct":  read_cpu_usage(),
        "battery_percent": battery["percent"],
        "battery_plugged": battery["plugged"],
        "ram_usage_pct":  read_ram_usage(),
        "disk_usage_pct": read_disk_usage(),
        "top_process":    top_memory_process(),
        
        # Inventory (Phase 1)
        "cpu_model":      get_cpu_model(),
        "ram_size_gb":    get_ram_size_gb(),
        "disk_type":      disk_info["type"],
        
        # Health (Phase 1)
        "disk_health":    disk_info["health"],
        "disk_wear_pct":  disk_info["wear_pct"],
    }
