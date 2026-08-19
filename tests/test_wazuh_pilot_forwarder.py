from __future__ import annotations

from pathlib import Path

import pytest

from integrations.wazuh_pilot_forwarder.forwarder import (
    ConfigurationError,
    DeliveryError,
    DeliveryResult,
    PilotConfig,
    ReadOnlyTailer,
    SpoolForwarder,
)


class CapturingTransport:
    def __init__(self) -> None:
        self.batches: list[dict] = []

    def deliver(self, batch: dict) -> DeliveryResult:
        self.batches.append(batch)
        return DeliveryResult(status=202, body={"data": {"automatic_enforcement": False}})


class FailingTransport:
    def deliver(self, _batch: dict) -> DeliveryResult:
        raise DeliveryError("controlled delivery outage")


def _config(tmp_path: Path) -> PilotConfig:
    return PilotConfig(
        endpoint_url="https://phantomnet.lab.example/wazuh/forwarders/forwarder-lab-001/stream",
        token_path=tmp_path / "forwarder.token",
        state_path=tmp_path / "state.json",
        spool_directory=tmp_path / "spool",
        min_rule_level=7,
        allowed_groups=("syscheck",),
        batch_size=10,
        poll_interval_seconds=0.01,
    )


def _alert(alert_id: str = "wazuh-001", level: int = 10, group: str = "syscheck") -> dict:
    return {
        "id": alert_id,
        "timestamp": "2026-08-19T10:00:00Z",
        "agent": {"id": "007", "name": "wazuh-lab-host"},
        "rule": {"id": "550", "level": level, "groups": [group]},
        "syscheck": {"event": "modified", "path": "/etc/passwd"},
    }


def test_config_refuses_non_tls_delivery_except_explicit_lab_override(tmp_path: Path) -> None:
    config = _config(tmp_path)
    object.__setattr__(config, "endpoint_url", "http://phantomnet.lab/wazuh/forwarders/fwd/stream")
    with pytest.raises(ConfigurationError, match="requires HTTPS"):
        config.validate()

    object.__setattr__(config, "allow_insecure_http", True)
    config.validate()


def test_read_only_tailer_forwards_only_allowlisted_alerts_and_advances_sequence_after_acceptance(tmp_path: Path) -> None:
    config = _config(tmp_path)
    alert_file = tmp_path / "alerts.json"
    alert_file.write_text(
        "\n".join([
            __import__("json").dumps(_alert("wazuh-accepted")),
            __import__("json").dumps(_alert("wazuh-filtered", level=3)),
        ]) + "\n",
        encoding="utf-8",
    )
    transport = CapturingTransport()

    delivered = ReadOnlyTailer(config, alert_file, transport).run_once()

    assert delivered == 1
    assert transport.batches == [
        {
            "batch_id": transport.batches[0]["batch_id"],
            "sequence": 1,
            "alerts": [_alert("wazuh-accepted")],
        }
    ]
    assert set(transport.batches[0]) == {"batch_id", "sequence", "alerts"}
    assert ReadOnlyTailer(config, alert_file, transport).run_once() == 0
    assert len(transport.batches) == 1


def test_tailer_delivery_failure_does_not_advance_state_or_skip_sequence(tmp_path: Path) -> None:
    config = _config(tmp_path)
    alert_file = tmp_path / "alerts.json"
    alert_file.write_text(__import__("json").dumps(_alert()) + "\n", encoding="utf-8")

    with pytest.raises(DeliveryError, match="controlled delivery outage"):
        ReadOnlyTailer(config, alert_file, FailingTransport()).run_once()
    assert not config.state_path.exists()

    recovered_transport = CapturingTransport()
    assert ReadOnlyTailer(config, alert_file, recovered_transport).run_once() == 1
    assert recovered_transport.batches[0]["sequence"] == 1


def test_manager_spool_deduplicates_alert_file_and_drains_as_telemetry_only_batch(tmp_path: Path) -> None:
    config = _config(tmp_path)
    source = tmp_path / "wazuh-alert.json"
    source.write_text(__import__("json").dumps(_alert()), encoding="utf-8")
    transport = CapturingTransport()
    spool = SpoolForwarder(config, transport)

    first = spool.enqueue_file(source)
    second = spool.enqueue_file(source)
    assert first == second
    assert len(list(spool.pending_directory.glob("*.json"))) == 1

    assert spool.drain_once() == 1
    assert transport.batches[0]["sequence"] == 1
    assert transport.batches[0]["alerts"] == [_alert()]
    assert list(spool.pending_directory.glob("*.json")) == []
