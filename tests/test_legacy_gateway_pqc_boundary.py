from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend_api.gateway_service.main import app


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_SOURCE = ROOT / "backend_api/gateway_service/main.py"


def _client_with_gateway_middleware_bypassed() -> TestClient:
    mock_redis = MagicMock()
    mock_redis.pipeline.return_value.execute.return_value = [1, True]
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    rate_limit_patch = patch("backend_api.gateway_service.main.redis_client", mock_redis)
    session_patch = patch("backend_api.gateway_service.main.SessionLocal", return_value=mock_session)
    rate_limit_patch.start()
    session_patch.start()
    client = TestClient(app)
    client._phantomnet_rate_limit_patch = rate_limit_patch  # type: ignore[attr-defined]
    client._phantomnet_session_patch = session_patch  # type: ignore[attr-defined]
    return client


def test_gateway_source_does_not_retain_legacy_pqc_wrapper_or_simulated_audit_calls():
    source = GATEWAY_SOURCE.read_text(encoding="utf-8")

    assert "from backend_api.shared.pqc_wrapper import PQCWrapper" not in source
    assert "encapsulate_key" not in source
    assert "apply_cryptographic_agility_check" not in source
    ast.parse(source, filename=str(GATEWAY_SOURCE))


def test_active_gateway_health_remains_available_while_legacy_pqc_routes_fail_closed():
    client = _client_with_gateway_middleware_bypassed()
    try:
        health_response = client.get("/health")
        handshake_response = client.post("/api/security/pqc-handshake", json={"public_key_id": "example"})
        audit_response = client.get("/api/security/audit-crypto-agility")
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert health_response.status_code == 200
    assert handshake_response.status_code == 410
    assert handshake_response.json()["code"] == "LEGACY_GATEWAY_PQC_API_RETIRED"
    assert audit_response.status_code == 410
    assert audit_response.json()["code"] == "LEGACY_GATEWAY_PQC_API_RETIRED"
