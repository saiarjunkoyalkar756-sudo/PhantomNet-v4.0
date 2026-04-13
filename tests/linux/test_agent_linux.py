# tests/linux/test_agent_linux.py

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Assuming phantomnet_agent and phantomnet_core are in sys.path
from phantomnet_agent.main import run_collectors, initialize_agent_state
from phantomnet_core.os_adapter import get_os, OS_LINUX, supports_ebpf

@pytest.fixture(autouse=True)
def mock_get_os_linux():
    """Ensures get_os returns Linux for these tests."""
    with patch('phantomnet_core.os_adapter.get_os', return_value=OS_LINUX):
        yield

@pytest.fixture(autouse=True)
def mock_supports_ebpf_true():
    """Ensures supports_ebpf returns True for these tests."""
    with patch('phantomnet_core.os_adapter.supports_ebpf', return_value=True):
        yield

@pytest.fixture
async def initialized_agent_state_linux():
    """Initializes agent state for Linux with eBPF support."""
    agent_id = "test-agent-linux"
    mode = "full"
    state = initialize_agent_state(agent_id, mode)
    state.config = MagicMock() # Mock config for run_collectors
    state.config.agent.collectors = {
        "ebpf_process": MagicMock(enabled=True),
        "ebpf_file": MagicMock(enabled=True),
        "ebpf_driver": MagicMock(enabled=True),
        "network": MagicMock(enabled=True), # Scapy network sensor
        "process": MagicMock(enabled=True), # psutil process monitor
        "file": MagicMock(enabled=True), # watchdog file collector
        "memory_scanner": MagicMock(enabled=True), # YARA memory scanner
    }
    state.orchestrator = AsyncMock() # Mock orchestrator for collectors
    return state

@pytest.mark.asyncio
async def test_linux_ebpf_collectors_start(initialized_agent_state_linux):
    """
    Test that eBPF-based collectors attempt to start on Linux.
    Note: Actual eBPF functionality requires kernel. This only tests startup logic.
    """
    with patch('phantomnet_agent.ebpf_process_monitor.EbpfProcessMonitor.start', new_callable=AsyncMock) as mock_ebpf_process_start, \
         patch('phantomnet_agent.ebpf_file_monitor.EbpfFileMonitor.start', new_callable=AsyncMock) as mock_ebpf_file_start, \
         patch('phantomnet_agent.ebpf_driver_monitor.EbpfDriverMonitor.start', new_callable=AsyncMock) as mock_ebpf_driver_start:
        
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        
        mock_ebpf_process_start.assert_called_once()
        mock_ebpf_file_start.assert_called_once()
        mock_ebpf_driver_start.assert_called_once()
        assert "ebpf_process" in initialized_agent_state_linux.collectors
        assert "ebpf_file" in initialized_agent_state_linux.collectors
        assert "ebpf_driver" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_network_sensor_starts(initialized_agent_state_linux):
    """Test that the network sensor attempts to start on Linux."""
    with patch('phantomnet_agent.networking.network_sensor.NetworkSensor.start') as mock_network_sensor_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        mock_network_sensor_start.assert_called_once()
        assert "network" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_process_monitor_starts(initialized_agent_state_linux):
    """Test that the process monitor attempts to start on Linux."""
    with patch('phantomnet_agent.collectors.process_collector.ProcessCollector.start') as mock_process_collector_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        mock_process_collector_start.assert_called_once()
        assert "process" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_file_monitor_starts(initialized_agent_state_linux):
    """Test that the file monitor attempts to start on Linux."""
    with patch('phantomnet_agent.collectors.file_collector.FileCollector.start') as mock_file_collector_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        mock_file_collector_start.assert_called_once()
        assert "file" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_memory_scanner_starts(initialized_agent_state_linux):
    """Test that the memory scanner attempts to start on Linux."""
    with patch('phantomnet_agent.collectors.memory_scanner.MemoryScanner.start') as mock_memory_scanner_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        mock_memory_scanner_start.assert_called_once()
        assert "memory_scanner" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_ai_component_mode():
    """Test AI component indicates full mode on Linux."""
    from phantomnet_agent.cognitive_core import CognitiveCore
    core = CognitiveCore()
    assert core.safe_ai_mode == False
    assert "Full Neural Model Mode" in core.logger.handlers[0].messages['info'][0] # Check log output

@pytest.mark.asyncio
async def test_linux_heartbeat_telemetry(initialized_agent_state_linux):
    """Test heartbeat telemetry includes Linux OS and capabilities."""
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        # Mock the entire heartbeat process to avoid real network calls
        with patch('phantomnet_agent.self_healing_infrastructure.get_agent_state', return_value=initialized_agent_state_linux):
            heartbeat_monitor = initialized_agent_state_linux.orchestrator.health_monitor # Assuming monitor is accessible
            if not heartbeat_monitor: # Initialize if not set in fixture
                from phantomnet_agent.self_healing_infrastructure import AgentHealthMonitor
                heartbeat_monitor = AgentHealthMonitor(agent_manager_url="http://mock-manager")

            await heartbeat_monitor._send_heartbeat()
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args['json']['os'] == OS_LINUX
            assert call_args['json']['capabilities']['supports_ebpf'] == True
