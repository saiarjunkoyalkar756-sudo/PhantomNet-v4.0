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
    with patch('phantomnet_core.os_adapter.get_os', return_value=OS_LINUX), \
         patch('phantomnet_agent.main.IS_LINUX', True), \
         patch('phantomnet_agent.main.IS_WINDOWS', False):
        yield

@pytest.fixture(autouse=True)
def mock_supports_ebpf_true():
    """Ensures supports_ebpf returns True for these tests."""
    with patch('phantomnet_core.os_adapter.supports_ebpf', return_value=True), \
         patch('phantomnet_agent.main.HAS_EBPF', True):
        yield

@pytest.fixture(autouse=True)
def mock_supports_raw_sockets_true():
    """Ensures raw sockets support returns True for Linux tests."""
    with patch('phantomnet_core.os_adapter.supports_raw_sockets', return_value=True), \
         patch('phantomnet_agent.main.SUPPORTS_RAW_SOCKETS', True):
        yield

@pytest.fixture
async def initialized_agent_state_linux():
    """Initializes agent state for Linux with eBPF support."""
    agent_id = "test-agent-linux"
    mode = "full"
    state = initialize_agent_state(agent_id, mode, os_type=OS_LINUX)
    
    def make_mock_collector(enabled=True, **kwargs):
        m = MagicMock(enabled=enabled)
        d = {"enabled": enabled, "interval_seconds": 10}
        d.update(kwargs)
        m.dict.return_value = d
        return m

    state.config = MagicMock() # Mock config for run_collectors
    state.config.agent.collectors = {
        "ebpf_process": make_mock_collector(True),
        "ebpf_file": make_mock_collector(True),
        "ebpf_driver": make_mock_collector(True),
        "network": make_mock_collector(True), # Scapy network sensor
        "process": make_mock_collector(True), # psutil process monitor
        "file": make_mock_collector(True, paths=["/var/log"]), # watchdog file collector
        "memory_scanner": make_mock_collector(True), # YARA memory scanner
    }
    state.orchestrator = AsyncMock() # Mock orchestrator for collectors
    state.adapter = MagicMock() # Mock adapter for OS operations
    return state

@pytest.mark.asyncio
async def test_linux_ebpf_collectors_start(initialized_agent_state_linux):
    """
    Test that eBPF-based collectors attempt to start on Linux.
    Note: Actual eBPF functionality requires kernel. This only tests startup logic.
    """
    with patch('ebpf_process_monitor.EbpfProcessMonitor.start', new_callable=AsyncMock) as mock_ebpf_process_start, \
         patch('ebpf_file_monitor.EbpfFileMonitor.start', new_callable=AsyncMock) as mock_ebpf_file_start, \
         patch('ebpf_driver_monitor.EbpfDriverMonitor.start', new_callable=AsyncMock) as mock_ebpf_driver_start:
        
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        await asyncio.sleep(0.01)
        
        mock_ebpf_process_start.assert_called_once()
        mock_ebpf_file_start.assert_called_once()
        mock_ebpf_driver_start.assert_called_once()
        assert "ebpf_process" in initialized_agent_state_linux.collectors
        assert "ebpf_file" in initialized_agent_state_linux.collectors
        assert "ebpf_driver" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_network_sensor_starts(initialized_agent_state_linux):
    """Test that the network sensor attempts to start on Linux."""
    with patch('collectors.network_collector.NetworkCollector.start') as mock_network_sensor_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        await asyncio.sleep(0.01) # Yield control to let async task execute
        mock_network_sensor_start.assert_called_once()
        assert "network" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_process_monitor_starts(initialized_agent_state_linux):
    """Test that the process monitor attempts to start on Linux."""
    with patch('collectors.process_collector.ProcessCollector.start') as mock_process_collector_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        await asyncio.sleep(0.01)
        mock_process_collector_start.assert_called_once()
        assert "process" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_file_monitor_starts(initialized_agent_state_linux):
    """Test that the file monitor attempts to start on Linux."""
    with patch('collectors.file_collector.FileCollector.start') as mock_file_collector_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        await asyncio.sleep(0.01)
        mock_file_collector_start.assert_called_once()
        assert "file" in initialized_agent_state_linux.collectors

@pytest.mark.asyncio
async def test_linux_memory_scanner_starts(initialized_agent_state_linux):
    """Test that the memory scanner attempts to start on Linux."""
    with patch('collectors.memory_scanner.MemoryScanner.start') as mock_memory_scanner_start:
        await run_collectors(initialized_agent_state_linux, initialized_agent_state_linux.orchestrator)
        await asyncio.sleep(0.01)
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
    with patch('phantomnet_agent.self_healing_infrastructure.httpx.AsyncClient') as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_post = mock_client.post
        
        # Mock the entire heartbeat process to avoid real network calls
        with patch('phantomnet_agent.self_healing_infrastructure.get_agent_state', return_value=initialized_agent_state_linux):
            from phantomnet_agent.self_healing_infrastructure import AgentHealthMonitor
            heartbeat_monitor = AgentHealthMonitor(agent_manager_url="http://mock-manager")

            await heartbeat_monitor._send_heartbeat()
            mock_post.assert_called_once()
            call_args = mock_post.call_args[1]
            assert call_args['json']['os'] == OS_LINUX
