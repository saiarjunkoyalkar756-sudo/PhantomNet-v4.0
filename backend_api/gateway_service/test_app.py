import pytest
from pydantic import ValidationError

from backend_api.gateway_service.main import LogEntryData


def test_log_entry_payload_accepts_valid_network_event_fields():
    entry = LogEntryData(ip="127.0.0.1", port=443, data="tls handshake metadata")

    assert entry.ip == "127.0.0.1"
    assert entry.port == 443
    assert entry.data == "tls handshake metadata"


def test_log_entry_payload_rejects_invalid_port_and_empty_data():
    with pytest.raises(ValidationError):
        LogEntryData(ip="127.0.0.1", port=70000, data="event")

    with pytest.raises(ValidationError):
        LogEntryData(ip="127.0.0.1", port=443, data="")
