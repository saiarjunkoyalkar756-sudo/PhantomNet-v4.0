import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from phantomnet_agent.bus.base import Transport
from phantomnet_agent.collectors.dns_collector import DnsCollector
from phantomnet_agent.collectors.file_collector import FileCollector
from phantomnet_agent.collectors.log_collector import LogCollector
from phantomnet_agent.collectors.network_collector import NetworkCollector
from phantomnet_agent.collectors.process_collector import ProcessCollector


class MockTransport(Transport):
    """Concrete transport test double retained for transport-contract coverage."""

    def __init__(self):
        self.connected = False
        self.sent_events = []

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def send_event(self, event_data):
        self.sent_events.append(event_data)

    async def receive_commands(self, commands_topic):
        if False:
            yield None


class RecordingOrchestrator:
    """Small collector dependency that records ingested events without network access."""

    def __init__(self):
        self.events = []

    async def ingest_event(self, event):
        self.events.append(event)


class AdapterStub:
    def __init__(self):
        self.get_process_list = AsyncMock(return_value=[])
        self.get_netstat_info = AsyncMock(return_value=[])


@pytest.fixture
def mock_transport():
    return MockTransport()


@pytest.fixture
def recording_orchestrator():
    return RecordingOrchestrator()


@pytest.fixture
def adapter_stub():
    return AdapterStub()


async def _stop_after_one_cycle(collector, _seconds):
    collector.running = False


@pytest.mark.asyncio
async def test_process_collector(recording_orchestrator, adapter_stub, monkeypatch):
    adapter_stub.get_process_list.return_value = [
        {
            "pid": 1,
            "name": "systemd",
            "exe": "/usr/lib/systemd/systemd",
            "cmdline": ["/usr/lib/systemd/systemd"],
            "username": "root",
            "status": "running",
            "ppid": 0,
        },
        {
            "pid": 100,
            "name": "python",
            "exe": "/usr/bin/python",
            "cmdline": ["/usr/bin/python", "agent.py"],
            "username": "user",
            "status": "running",
            "ppid": 1,
        },
    ]
    collector = ProcessCollector(recording_orchestrator, adapter_stub, {"interval_seconds": 1})

    async def stop_loop(_seconds):
        await _stop_after_one_cycle(collector, _seconds)

    monkeypatch.setattr(asyncio, "sleep", stop_loop)
    await collector.start()

    assert len(recording_orchestrator.events) == 2
    assert {event["payload"]["name"] for event in recording_orchestrator.events} == {"systemd", "python"}


@pytest.mark.asyncio
async def test_file_collector_periodic_scan(recording_orchestrator, adapter_stub, tmp_path, monkeypatch):
    monkeypatch.setattr("phantomnet_agent.collectors.file_collector.WATCHDOG_AVAILABLE", False)
    test_dir = tmp_path / "file_test_dir"
    test_dir.mkdir()
    file1 = test_dir / "test_file_1.txt"
    file2 = test_dir / "test_file_2.log"
    file1.write_text("initial content 1")
    file2.write_text("initial content 2")

    collector = FileCollector(
        recording_orchestrator,
        adapter_stub,
        {"interval_seconds": 1, "paths": [str(test_dir)]},
    )
    await collector._periodic_scan()
    assert len(recording_orchestrator.events) == 2

    recording_orchestrator.events.clear()
    file1.write_text("modified content 1")
    await collector._periodic_scan()
    assert len(recording_orchestrator.events) == 1
    assert recording_orchestrator.events[0]["payload"]["path"] == str(file1)
    assert recording_orchestrator.events[0]["payload"]["operation"] == "modified"

    recording_orchestrator.events.clear()
    file2.unlink()
    await collector._periodic_scan()
    assert len(recording_orchestrator.events) == 1
    assert recording_orchestrator.events[0]["payload"]["path"] == str(file2)
    assert recording_orchestrator.events[0]["payload"]["operation"] == "deleted"


@pytest.mark.asyncio
async def test_network_collector(recording_orchestrator, adapter_stub):
    adapter_stub.get_netstat_info.return_value = [
        {
            "local_address": "127.0.0.1",
            "local_port": 50000,
            "remote_address": "127.0.0.1",
            "remote_port": 8080,
            "protocol": "tcp",
            "status": "ESTABLISHED",
            "process_pid": 1234,
        }
    ]
    collector = NetworkCollector(recording_orchestrator, adapter_stub, {"interval_seconds": 1})

    await collector.collect()
    assert len(recording_orchestrator.events) == 1
    payload = recording_orchestrator.events[0]["payload"]
    assert payload["local_port"] == 50000
    assert payload["remote_port"] == 8080
    assert payload["status"] == "ESTABLISHED"
    assert payload["process_pid"] == 1234

    await collector.collect()
    assert len(recording_orchestrator.events) == 1


@pytest.mark.asyncio
async def test_dns_collector(recording_orchestrator, adapter_stub, tmp_path):
    test_log_file = tmp_path / "dns.log"
    test_log_file.write_text(
        "Dec  4 10:00:01 host systemd-resolved[123]: query example.com\n"
        "Dec  4 10:00:02 host dnsmasq[456]: query[A] google.com from 192.168.1.100\n"
    )
    collector = DnsCollector(
        recording_orchestrator,
        adapter_stub,
        {"interval_seconds": 1, "log_files": [str(test_log_file)]},
    )

    await collector._process_log_file(str(test_log_file))
    assert len(recording_orchestrator.events) == 2

    recording_orchestrator.events.clear()
    with test_log_file.open("a") as handle:
        handle.write("Dec  4 10:00:05 host systemd-resolved[123]: query www.anothersite.org\n")
    await collector._process_log_file(str(test_log_file))

    assert len(recording_orchestrator.events) == 1
    assert recording_orchestrator.events[0]["payload"]["query_name"] == "www.anothersite.org"


@pytest.mark.asyncio
async def test_log_collector(recording_orchestrator, adapter_stub, tmp_path):
    test_log_file = tmp_path / "app.log"
    test_log_file.write_text("2023-01-01 10:00:00 INFO App started.\n")
    collector = LogCollector(
        recording_orchestrator,
        adapter_stub,
        {"agent_id": "test-agent", "interval_seconds": 1, "files": [str(test_log_file)]},
    )
    collector.last_read_positions[str(test_log_file)] = test_log_file.stat().st_size

    with test_log_file.open("a") as handle:
        handle.write("2023-01-01 10:00:02 DEBUG User logged in.\n")
    await collector._tail_log_file(str(test_log_file))

    assert len(recording_orchestrator.events) == 1
    assert recording_orchestrator.events[0]["message"] == "2023-01-01 10:00:02 DEBUG User logged in."

    recording_orchestrator.events.clear()
    with test_log_file.open("a") as handle:
        handle.write("2023-01-01 10:00:05 ERROR Failed to process request.\n")
    await collector._tail_log_file(str(test_log_file))

    assert len(recording_orchestrator.events) == 1
    assert recording_orchestrator.events[0]["message"] == "2023-01-01 10:00:05 ERROR Failed to process request."
