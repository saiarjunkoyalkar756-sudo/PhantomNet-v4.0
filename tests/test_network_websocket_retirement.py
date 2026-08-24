"""Source-contract regressions for retired legacy network WebSocket ingestion."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NETWORK_WS_SERVER = ROOT / "backend_api/networking/ws_server.py"
GOVERNED_SOAR_API = ROOT / "backend_api/soar_engine/governed_api.py"


def test_legacy_network_websocket_fails_closed_without_placeholder_attestation():
    source = NETWORK_WS_SERVER.read_text(encoding="utf-8")

    assert '@router.websocket("/ws/network")' in source
    assert "WS_1008_POLICY_VIOLATION" in source
    assert "Legacy network telemetry streaming is retired" in source
    assert "REGISTERED_AGENTS" not in source
    assert "platform_id_hash" not in source
    assert "KafkaProducer" not in source
    assert "producer.send" not in source
    assert "websocket.receive_text" not in source
    assert "websocket.accept" not in source


def test_retired_network_websocket_and_governed_signed_telemetry_are_distinct():
    legacy_source = NETWORK_WS_SERVER.read_text(encoding="utf-8")
    governed_source = GOVERNED_SOAR_API.read_text(encoding="utf-8")

    assert '"status": "legacy-network-websocket-retired"' in legacy_source
    assert "TelemetrySigningCredential" in governed_source
    assert 'require_capability("agents:approve")' in governed_source
