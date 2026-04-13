import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import os
import shutil

# Import the base Transport and Collectors
from phantomnet_agent.bus.base import Transport
from phantomnet_agent.collectors.base import Collector
from phantomnet_agent.collectors.process_collector import ProcessCollector
from phantomnet_agent.collectors.file_collector import FileCollector
from phantomnet_agent.collectors.network_collector import NetworkCollector
from phantomnet_agent.collectors.dns_collector import DnsCollector
from phantomnet_agent.collectors.log_collector import LogCollector

# Mock Transport for testing collectors
class MockTransport(Transport):
    def __init__(self):
        # AsyncMock for send_event to capture calls
        self.send_event = AsyncMock()
    
    async def receive_commands(self, topic: str):
        # This mock transport doesn't receive commands for collector tests
        yield

@pytest.fixture
def mock_transport():
    return MockTransport()

@pytest.fixture(autouse=True)
def disable_collector_sleep(monkeypatch):
    """Prevent collectors from actually sleeping during tests."""
    async def no_sleep(*args, **kwargs):
        pass
    monkeypatch.setattr(asyncio, "sleep", no_sleep)

# --- Test ProcessCollector ---
@pytest.mark.asyncio
async def test_process_collector(mock_transport):
    # Mock psutil.process_iter to return a predictable list of processes
    mock_process_iter = MagicMock()
    mock_proc1 = MagicMock()
    mock_proc1.info = {
        'pid': 1, 'name': 'systemd', 'exe': '/usr/lib/systemd/systemd',
        'cmdline': ['/usr/lib/systemd/systemd'], 'username': 'root',
        'status': 'running', 'ppid': 0
    }
    mock_proc1.oneshot.return_value.__enter__.return_value = mock_proc1

    mock_proc2 = MagicMock()
    mock_proc2.info = {
        'pid': 100, 'name': 'python', 'exe': '/usr/bin/python',
        'cmdline': ['/usr/bin/python', 'agent.py'], 'username': 'user',
        'status': 'running', 'ppid': 1
    }
    mock_proc2.oneshot.return_value.__enter__.return_value = mock_proc2

    mock_process_iter.return_value = [mock_proc1, mock_proc2]

    with MagicMock(return_value=mock_process_iter) as mock_psutil_process_iter:
        # We need to patch psutil at the module level where it's imported in process_collector
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr("collectors.process_collector.psutil.process_iter", mock_psutil_process_iter)
            
            config = {"interval_seconds": 1}
            collector = ProcessCollector(mock_transport, config)
            
            # Run the collector for one cycle
            await collector.start()
            await collector.run() # Manually call run to simulate one collection cycle
            await collector.stop()

            mock_transport.send_event.assert_called()
            # Assert that two events were sent
            assert mock_transport.send_event.call_count == 2
            
            # Check content of one of the calls (order might vary)
            call_args_list = mock_transport.send_event.call_args_list
            event_payloads = [call.kwargs['payload'] for call in call_args_list]

            assert any(p['payload']['name'] == 'systemd' for p in event_payloads)
            assert any(p['payload']['name'] == 'python' for p in event_payloads)


# --- Test FileCollector ---
@pytest.mark.asyncio
async def test_file_collector_periodic_scan(mock_transport, tmp_path):
    # Disable watchdog for this test to ensure periodic scan path is taken
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("collectors.file_collector.WATCHDOG_AVAILABLE", False)

        test_dir = tmp_path / "file_test_dir"
        test_dir.mkdir()
        file1 = test_dir / "test_file_1.txt"
        file2 = test_dir / "test_file_2.log"

        file1.write_text("initial content 1")
        file2.write_text("initial content 2")

        config = {"interval_seconds": 1, "paths": [str(test_dir)]}
        collector = FileCollector(mock_transport, config)
        
        await collector.start()
        await collector.run() # Initial scan
        
        # Two files should have been "created" initially
        assert mock_transport.send_event.call_count == 2
        mock_transport.send_event.reset_mock() # Reset mock for further checks

        # Modify a file
        file1.write_text("modified content 1")
        await collector.run() # Second scan
        
        assert mock_transport.send_event.call_count == 1
        event_payload = mock_transport.send_event.call_args.kwargs['payload']
        assert event_payload['payload']['path'] == str(file1)
        assert event_payload['payload']['operation'] == 'modified'
        mock_transport.send_event.reset_mock()

        # Delete a file
        file2.unlink()
        await collector.run() # Third scan

        assert mock_transport.send_event.call_count == 1
        event_payload = mock_transport.send_event.call_args.kwargs['payload']
        assert event_payload['payload']['path'] == str(file2)
        assert event_payload['payload']['operation'] == 'deleted'
        mock_transport.send_event.reset_mock()

        await collector.stop()


# --- Test NetworkCollector ---
@pytest.mark.asyncio
async def test_network_collector(mock_transport):
    # Mock psutil.net_connections
    mock_net_conn = MagicMock()
    mock_net_conn.laddr = ('127.0.0.1', 50000)
    mock_net_conn.raddr = ('127.0.0.1', 8080)
    mock_net_conn.status = 'ESTABLISHED'
    mock_net_conn.pid = 1234
    mock_net_conn.type = 1 # psutil.SOCK_STREAM

    mock_net_conn_listen = MagicMock()
    mock_net_conn_listen.laddr = ('0.0.0.0', 80)
    mock_net_conn_listen.raddr = () # Listening socket, no raddr
    mock_net_conn_listen.status = 'LISTEN'
    mock_net_conn_listen.pid = 5678
    mock_net_conn_listen.type = 1 # psutil.SOCK_STREAM

    with pytest.MonkeyPatch().context() as mp:
        mp.setattr("collectors.network_collector.psutil.net_connections", MagicMock(return_value=[mock_net_conn, mock_net_conn_listen]))
        mp.setattr("collectors.network_collector.psutil.Process", MagicMock(return_value=MagicMock(pid=1234))) # Mock PIDs

        config = {"interval_seconds": 1}
        collector = NetworkCollector(mock_transport, config)

        await collector.start()
        await collector.run()

        # Only one event should be sent (ESTABLISHED connection, not LISTEN)
        assert mock_transport.send_event.call_count == 1
        event_payload = mock_transport.send_event.call_args.kwargs['payload']
        assert event_payload['payload']['local_port'] == 50000
        assert event_payload['payload']['remote_port'] == 8080
        assert event_payload['payload']['status'] == 'ESTABLISHED'
        assert event_payload['payload']['process_pid'] == 1234

        mock_transport.send_event.reset_mock()

        # Run again, no new events should be sent as connections are known
        await collector.run()
        assert mock_transport.send_event.call_count == 0

        await collector.stop()


# --- Test DnsCollector ---
@pytest.mark.asyncio
async def test_dns_collector(mock_transport, tmp_path):
    test_log_file = tmp_path / "dns.log"
    test_log_file.write_text("Dec  4 10:00:01 host systemd-resolved[123]: query example.com\n")
    test_log_file.write("Dec  4 10:00:02 host dnsmasq[456]: query[A] google.com from 192.168.1.100\n")

    config = {"interval_seconds": 1, "log_files": [str(test_log_file)]}
    collector = DnsCollector(mock_transport, config)

    await collector.start()
    await collector.run()

    assert mock_transport.send_event.call_count == 2
    mock_transport.send_event.reset_mock()

    # Add new entries
    test_log_file.write_text("Dec  4 10:00:05 host systemd-resolved[123]: query www.anothersite.org\n", mode='a')
    await collector.run()

    assert mock_transport.send_event.call_count == 1
    event_payload = mock_transport.send_event.call_args.kwargs['payload']
    assert event_payload['payload']['query_name'] == 'www.anothersite.org'
    mock_transport.send_event.reset_mock()

    await collector.stop()


# --- Test LogCollector ---
@pytest.mark.asyncio
async def test_log_collector(mock_transport, tmp_path):
    test_log_file = tmp_path / "app.log"
    test_log_file.write_text("2023-01-01 10:00:00 INFO App started.\n")

    config = {"interval_seconds": 1, "files": [str(test_log_file)]}
    collector = LogCollector(mock_transport, config)

    await collector.start()
    # Initial run, should read the existing line but not send it if positioned at end
    await collector.run() 
    mock_transport.send_event.assert_not_called() # Should not send old logs
    mock_transport.send_event.reset_mock()

    # Add a new line
    test_log_file.write_text("2023-01-01 10:00:02 DEBUG User logged in.\n", mode='a')
    await collector.run()

    assert mock_transport.send_event.call_count == 1
    event_payload = mock_transport.send_event.call_args.kwargs['payload']
    assert event_payload['payload']['message'] == '2023-01-01 10:00:02 DEBUG User logged in.'
    mock_transport.send_event.reset_mock()

    # Add another new line
    test_log_file.write_text("2023-01-01 10:00:05 ERROR Failed to process request.\n", mode='a')
    await collector.run()

    assert mock_transport.send_event.call_count == 1
    event_payload = mock_transport.send_event.call_args.kwargs['payload']
    assert event_payload['payload']['message'] == '2023-01-01 10:00:05 ERROR Failed to process request.'
    
    await collector.stop()
