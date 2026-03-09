import pytest
from unittest.mock import patch, MagicMock
from agent.agent import classify_health
from agent.hardware_monitor import (
    get_cpu_model, 
    get_ram_size_gb, 
    get_disk_info,
    collect_snapshot
)

def test_classify_health_green():
    snapshot = {
        "cpu_temp_c": 50,
        "disk_usage_pct": 50
    }
    # Reset tracking state if needed (classify_health uses globals)
    from agent.agent import classify_health as agent_classify
    assert agent_classify(snapshot) == "green"

def test_classify_health_red_disk():
    snapshot = {
        "cpu_temp_c": 50,
        "disk_usage_pct": 96
    }
    from agent.agent import classify_health as agent_classify
    assert agent_classify(snapshot) == "red"

def test_get_ram_size_gb():
    with patch("psutil.virtual_memory") as mock_vm:
        mock_vm.return_value.total = 16 * 1024 * 1024 * 1024 # 16 GB
        assert get_ram_size_gb() == 16.0

def test_get_cpu_model_windows():
    with patch("platform.system", return_value="Windows"):
        with patch("subprocess.check_output") as mock_cmd:
            mock_cmd.return_value = b"Name\nIntel Core i7\n"
            assert get_cpu_model() == "Intel Core i7"

def test_get_disk_info_ssd():
    with patch("platform.system", return_value="Windows"):
        with patch("subprocess.check_output") as mock_cmd:
            mock_cmd.return_value = b"SSD  Healthy"
            info = get_disk_info()
            assert info["type"] == "SSD"
            assert info["health"] == "GOOD"
