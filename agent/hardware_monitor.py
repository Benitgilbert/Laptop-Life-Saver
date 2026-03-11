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
    Highly dynamic: tries WMI (standard & vendor-specific), typeperf (perf counters), and psutil.
    """
    # 1. Try WMI (Standard ACPI)
    if WMI_AVAILABLE and _wmi_client is not None:
        try:
            sensors = _wmi_client.MSAcpi_ThermalZoneTemperature()
            for s in sensors:
                c = (s.CurrentTemperature / 10.0) - 273.15
                if 10 < c < 120: 
                    logger.info("Temp: Using MSAcpi (%.1f°C)", c)
                    return round(c, 1)
        except Exception as e:
            logger.debug("MSAcpi failed: %s", e)

    # 2. Try Vendor-Specific WMI Namespaces (Dynamic Discovery)
    try:
        if WMI_AVAILABLE:
            import wmi
            # HP-specific
            try:
                hp = wmi.WMI(namespace=r"root\HP\InstrumentedBIOS")
                hp_sensors = hp.HP_BIOSNumericSensor(Name="CPU Temperature")
                if hp_sensors:
                    c = float(hp_sensors[0].CurrentReading)
                    logger.info("Temp: Using HP Sensor (%.1f°C)", c)
                    return c
            except Exception: pass
            
            # Dell-specific
            try:
                dell = wmi.WMI(namespace=r"root\dcim\sysman")
                dell_sensors = dell.DCIM_NumericSensor(Caption="CPU Temperature")
                if dell_sensors:
                    c = float(dell_sensors[0].CurrentReading)
                    logger.info("Temp: Using Dell Sensor (%.1f°C)", c)
                    return c
            except Exception: pass
    except Exception: pass

    # 3. Try Performance Counters via typeperf (Very reliable fallback on Windows)
    if platform.system() == "Windows":
        try:
            # -sc 1 means sample count 1 (immediate)
            cmd = 'typeperf "\\Thermal Zone Information(*)\\Temperature" -sc 1'
            output = subprocess.check_output(cmd, shell=True, timeout=5, stderr=subprocess.STDOUT).decode(errors='ignore').strip()
            lines = [l.strip() for l in output.split('\n') if l.strip()]
            for line in lines:
                if line.startswith('"') and ',' in line:
                    data_row = line.replace('"', '').split(',')
                    for val in data_row[1:]: # Skip timestamp
                        try:
                            k = float(val)
                            # typeperf can return Celsius directly or Kelvin (usually > 200).
                            # If it's Kelvin (most common for Thermal Zone counters)
                            if k > 200:
                                c = k - 273.15
                            else:
                                c = k
                            
                            if 10 < c < 120:
                                logger.info("Temp: Using typeperf (%.1f°C)", c)
                                return round(c, 1)
                        except (ValueError, IndexError): continue
        except Exception as e:
            logger.info("Temp: typeperf failed: %s", str(e))

    # 4. Try psutil (Cross-platform standard)
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name in ['coretemp', 'cpu_thermal', 'k10temp', 'zenpower', 'acpitz', 'thermal']:
                if name in temps and temps[name]:
                    c = temps[name][0].current
                    logger.info("Temp: Using psutil %s (%.1f°C)", name, c)
                    return round(c, 1)
    except Exception: pass
    
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
    mac_addr = get_mac_address()
    
    return {
        "recorded_at":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mac_address":    mac_addr,
        
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
