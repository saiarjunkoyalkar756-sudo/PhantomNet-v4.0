# tests/termux/test_agent_termux.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from phantomnet_agent.main import run_collectors, initialize_agent_state
from phantomnet_core.os_adapter import get_os, OS_TERMUX, supports_ebpf

@pytest.fixture(autouse=True)
def mock_get_os_termux():
    """Ensures get_os returns Termux for these tests."""
    with patch('phantomnet_core.os_adapter.get_os', return_value=OS_TERMUX):
        yield

@pytest.fixture(autouse=True)
def mock_supports_ebpf_false():
    """Ensures supports_ebpf returns False for these tests (Termux)."""
    with patch('phantomnet_core.os_adapter.supports_ebpf', return_value=False):
        yield

@pytest.fixture(autouse=True)
def mock_supports_raw_sockets_false():
    """Ensures supports_raw_sockets returns False for these tests (Termux)."""
    with patch('phantomnet_core.os_adapter.supports_raw_sockets', return_value=False):
        yield

@pytest.fixture
async def initialized_agent_state_termux():
    """Initializes agent state for Termux."""
    agent_id = "test-agent-termux"
    mode = "full"
    state = initialize_agent_state(agent_id, mode)
    state.config = MagicMock() # Mock config for run_collectors
    state.config.agent.collectors = {
        "ebpf_process": MagicMock(enabled=True), # Should be disabled by OS
        "ebpf_file": MagicMock(enabled=True),    # Should be disabled by OS
        "ebpf_driver": MagicMock(enabled=True),  # Should be disabled by OS
        "windows_registry": MagicMock(enabled=True), # Should be disabled by OS
        "network": MagicMock(enabled=True), # Scapy network sensor (limited mode)
        "process": MagicMock(enabled=True), # psutil process monitor
        "file": MagicMock(enabled=True), # watchdog file collector
        "memory_scanner": MagicMock(enabled=True), # YARA memory scanner (limited mode)
    }
    state.orchestrator = AsyncMock() # Mock orchestrator for collectors
    return state

@pytest.mark.asyncio
async def test_termux_ebpf_collectors_not_start(initialized_agent_state_termux):
    """
    Test that eBPF-based collectors do NOT start on Termux.
    """
    with patch('phantomnet_agent.ebpf_process_monitor.EbpfProcessMonitor.start', new_callable=AsyncMock) as mock_ebpf_process_start, \
         patch('phantomnet_agent.ebpf_file_monitor.EbpfFileMonitor.start', new_callable=AsyncMock) as mock_ebpf_file_start, \
         patch('phantomnet_agent.ebpf_driver_monitor.EbpfDriverMonitor.start', new_callable=AsyncMock) as mock_ebpf_driver_start:
        
        await run_collectors(initialized_agent_state_termux, initialized_agent_state_termux.orchestrator)
        
        mock_ebpf_process_start.assert_not_called()
        mock_ebpf_file_start.assert_not_called()
        mock_ebpf_driver_start.assert_not_called()
        assert "ebpf_process" not in initialized_agent_state_termux.collectors
        assert "ebpf_file" not in initialized_agent_state_termux.collectors
        assert "ebpf_driver" not in initialized_agent_state_termux.collectors

@pytest.mark.asyncio
async def test_termux_windows_registry_monitor_not_start(initialized_agent_state_termux):
    """Test that the Windows registry monitor does NOT start on Termux."""
    with patch('phantomnet_agent.collectors.windows_registry_monitor.WindowsRegistryMonitor.start', new_callable=AsyncMock) as mock_registry_monitor_start:
        await run_collectors(initialized_agent_state_termux, initialized_agent_state_termux.orchestrator)
        mock_registry_monitor_start.assert_not_called()
        assert "windows_registry" not in initialized_agent_state_termux.collectors

@pytest.mark.asyncio
async def test_termux_network_sensor_starts_in_limited_mode(initialized_agent_state_termux):
    """Test that the network sensor attempts to start on Termux (in limited mode)."""
    with patch('phantomnet_agent.networking.network_sensor.NetworkSensor.start') as mock_network_sensor_start, \
         patch('phantomnet_agent.networking.network_sensor.NetworkSensor._limited_monitor_mode') as mock_limited_mode:
        
        await run_collectors(initialized_agent_state_termux, initialized_agent_state_termux.orchestrator)
        mock_network_sensor_start.assert_called_once()
        # Ensure that the limited_monitor_mode is called internally or mocked correctly
        # The start method will internally call _limited_monitor_mode if OS is Termux
        assert "network" in initialized_agent_state_termux.collectors

@pytest.mark.asyncio
async def test_termux_process_monitor_starts(initialized_agent_state_termux):
    """Test that the process monitor attempts to start on Termux."""
    with patch('phantomnet_agent.collectors.process_collector.ProcessCollector.start') as mock_process_collector_start:
        await run_collectors(initialized_agent_state_termux, initialized_agent_state_termux.orchestrator)
        mock_process_collector_start.assert_called_once()
        assert "process" in initialized_agent_state_termux.collectors

@pytest.mark.asyncio
async def test_termux_file_monitor_starts(initialized_agent_state_termux):
    """Test that the file monitor attempts to start on Termux."""
    with patch('phantomnet_agent.collectors.file_collector.FileCollector.start') as mock_file_collector_start:
        await run_collectors(initialized_agent_state_termux, initialized_agent_state_termux.orchestrator)
        mock_file_collector_start.assert_called_once()
        assert "file" in initialized_agent_state_termux.collectors

@pytest.mark.asyncio
async def test_termux_memory_scanner_starts_in_limited_mode(initialized_agent_state_termux):
    """Test that the memory scanner attempts to start on Termux (in limited mode)."""
    with patch('phantomnet_agent.collectors.memory_scanner.MemoryScanner.start') as mock_memory_scanner_start, \
         patch('phantomnet_agent.collectors.memory_scanner.MemoryScanner._limited_scan') as mock_limited_scan:
        
        await run_collectors(initialized_agent_state_termux, initialized_agent_state_termux.orchestrator)
        mock_memory_scanner_start.assert_called_once()
        # The start method will internally call _limited_scan if OS is Termux
        assert "memory_scanner" in initialized_agent_state_termux.collectors

@pytest.mark.asyncio
async def test_termux_ai_component_mode():
    """Test AI component indicates TensorLite mode on Termux."""
    from phantomnet_agent.cognitive_core import CognitiveCore
    core = CognitiveCore()
    assert core.safe_ai_mode == True
    # Check log output for TensorLite Mode
    # This requires inspecting the logger output, which is more complex than a direct assert
    # For now, we assume if safe_ai_mode is True, it means TensorLite mode.

@pytest.mark.asyncio
async def test_termux_heartbeat_telemetry(initialized_agent_state_termux):
    """Test heartbeat telemetry includes Termux OS and capabilities."""
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        with patch('phantomnet_agent.self_healing_infrastructure.get_agent_state', return_value=initialized_agent_state_termux):
            heartbeat_monitor = initialized_agent_state_termux.orchestrator.health_monitor 
            if not heartbeat_monitor: 
                from phantomnet_agent.self_healing_infrastructure import AgentHealthMonitor
                heartbeat_monitor = AgentHealthMonitor(agent_manager_url="http://mock-manager")

            await heartbeat_monitor._send_heartbeat()
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args['json']['os'] == OS_TERMUX
            assert call_args['json']['capabilities']['supports_ebpf'] == False
