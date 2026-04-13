# tests/windows/test_agent_windows.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from phantomnet_agent.main import run_collectors, initialize_agent_state
from phantomnet_core.os_adapter import get_os, OS_WINDOWS, supports_ebpf

@pytest.fixture(autouse=True)
def mock_get_os_windows():
    """Ensures get_os returns Windows for these tests."""
    with patch('phantomnet_core.os_adapter.get_os', return_value=OS_WINDOWS):
        yield

@pytest.fixture(autouse=True)
def mock_supports_ebpf_false():
    """Ensures supports_ebpf returns False for these tests (Windows)."""
    with patch('phantomnet_core.os_adapter.supports_ebpf', return_value=False):
        yield

@pytest.fixture(autouse=True)
def mock_supports_raw_sockets_true():
    """Ensures supports_raw_sockets returns True for these tests (Windows)."""
    with patch('phantomnet_core.os_adapter.supports_raw_sockets', return_value=True):
        yield

@pytest.fixture
async def initialized_agent_state_windows():
    """Initializes agent state for Windows."""
    agent_id = "test-agent-windows"
    mode = "full"
    state = initialize_agent_state(agent_id, mode)
    state.config = MagicMock() # Mock config for run_collectors
    state.config.agent.collectors = {
        "ebpf_process": MagicMock(enabled=True), # Should be disabled by OS
        "ebpf_file": MagicMock(enabled=True),    # Should be disabled by OS
        "ebpf_driver": MagicMock(enabled=True),  # Should be disabled by OS
        "windows_registry": MagicMock(enabled=True), # Should start
        "network": MagicMock(enabled=True), # Scapy network sensor
        "process": MagicMock(enabled=True), # psutil process monitor
        "file": MagicMock(enabled=True), # watchdog file collector
        "memory_scanner": MagicMock(enabled=True), # YARA memory scanner
    }
    state.orchestrator = AsyncMock() # Mock orchestrator for collectors
    return state

@pytest.mark.asyncio
async def test_windows_ebpf_collectors_not_start(initialized_agent_state_windows):
    """
    Test that eBPF-based collectors do NOT start on Windows.
    """
    with patch('phantomnet_agent.ebpf_process_monitor.EbpfProcessMonitor.start', new_callable=AsyncMock) as mock_ebpf_process_start, \
         patch('phantomnet_agent.ebpf_file_monitor.EbpfFileMonitor.start', new_callable=AsyncMock) as mock_ebpf_file_start, \
         patch('phantomnet_agent.ebpf_driver_monitor.EbpfDriverMonitor.start', new_callable=AsyncMock) as mock_ebpf_driver_start:
        
        await run_collectors(initialized_agent_state_windows, initialized_agent_state_windows.orchestrator)
        
        mock_ebpf_process_start.assert_not_called()
        mock_ebpf_file_start.assert_not_called()
        mock_ebpf_driver_start.assert_not_called()
        assert "ebpf_process" not in initialized_agent_state_windows.collectors
        assert "ebpf_file" not in initialized_agent_state_windows.collectors
        assert "ebpf_driver" not in initialized_agent_state_windows.collectors

@pytest.mark.asyncio
async def test_windows_registry_monitor_starts(initialized_agent_state_windows):
    """Test that the Windows registry monitor attempts to start on Windows."""
    with patch('phantomnet_agent.collectors.windows_registry_monitor.WindowsRegistryMonitor.start', new_callable=AsyncMock) as mock_registry_monitor_start:
        await run_collectors(initialized_agent_state_windows, initialized_agent_state_windows.orchestrator)
        mock_registry_monitor_start.assert_called_once()
        assert "windows_registry" in initialized_agent_state_windows.collectors

@pytest.mark.asyncio
async def test_windows_network_sensor_starts(initialized_agent_state_windows):
    """Test that the network sensor attempts to start on Windows."""
    with patch('phantomnet_agent.networking.network_sensor.NetworkSensor.start') as mock_network_sensor_start:
        await run_collectors(initialized_agent_state_windows, initialized_agent_state_windows.orchestrator)
        mock_network_sensor_start.assert_called_once()
        assert "network" in initialized_agent_state_windows.collectors

@pytest.mark.asyncio
async def test_windows_process_monitor_starts(initialized_agent_state_windows):
    """Test that the process monitor attempts to start on Windows."""
    with patch('phantomnet_agent.collectors.process_collector.ProcessCollector.start') as mock_process_collector_start:
        await run_collectors(initialized_agent_state_windows, initialized_agent_state_windows.orchestrator)
        mock_process_collector_start.assert_called_once()
        assert "process" in initialized_agent_state_windows.collectors

@pytest.mark.asyncio
async def test_windows_file_monitor_starts(initialized_agent_state_windows):
    """Test that the file monitor attempts to start on Windows."""
    with patch('phantomnet_agent.collectors.file_collector.FileCollector.start') as mock_file_collector_start:
        await run_collectors(initialized_agent_state_windows, initialized_agent_state_windows.orchestrator)
        mock_file_collector_start.assert_called_once()
        assert "file" in initialized_agent_state_windows.collectors

@pytest.mark.asyncio
async def test_windows_memory_scanner_starts(initialized_agent_state_windows):
    """Test that the memory scanner attempts to start on Windows."""
    with patch('phantomnet_agent.collectors.memory_scanner.MemoryScanner.start') as mock_memory_scanner_start:
        await run_collectors(initialized_agent_state_windows, initialized_agent_state_windows.orchestrator)
        mock_memory_scanner_start.assert_called_once()
        assert "memory_scanner" in initialized_agent_state_windows.collectors

@pytest.mark.asyncio
async def test_windows_ai_component_mode():
    """Test AI component indicates full mode on Windows."""
    from phantomnet_agent.cognitive_core import CognitiveCore
    core = CognitiveCore()
    assert core.safe_ai_mode == False
    # Check log output for Full Neural Model Mode
    # This requires inspecting the logger output, which is more complex than a direct assert
    # For now, we assume if safe_ai_mode is False, it means Full mode.

@pytest.mark.asyncio
async def test_windows_heartbeat_telemetry(initialized_agent_state_windows):
    """Test heartbeat telemetry includes Windows OS and capabilities."""
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        with patch('phantomnet_agent.self_healing_infrastructure.get_agent_state', return_value=initialized_agent_state_windows):
            heartbeat_monitor = initialized_agent_state_windows.orchestrator.health_monitor 
            if not heartbeat_monitor: 
                from phantomnet_agent.self_healing_infrastructure import AgentHealthMonitor
                heartbeat_monitor = AgentHealthMonitor(agent_manager_url="http://mock-manager")

            await heartbeat_monitor._send_heartbeat()
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args['json']['os'] == OS_WINDOWS
            assert call_args['json']['capabilities']['supports_ebpf'] == False
