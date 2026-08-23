from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend_api.gateway_service.main import app


ROOT = Path(__file__).resolve().parents[1]
AGENT_API_SOURCE = ROOT / "backend_api/gateway_service/agent_api.py"
RETIRED_CODE = "LEGACY_GATEWAY_AGENT_API_RETIRED"


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


def test_legacy_gateway_agent_api_removes_unsafe_enrollment_and_management_components():
    source = AGENT_API_SOURCE.read_text(encoding="utf-8")

    for unsafe_component in (
        "bootstrap_tokens",
        "generate_self_signed_ca",
        "sign_certificate",
        "TelemetryIngestService",
        "get_db",
        "AgentCredential",
        "message_bus",
        "get_current_user",
        "require_capability",
    ):
        assert unsafe_component not in source

    ast.parse(source, filename=str(AGENT_API_SOURCE))


def test_legacy_gateway_agent_http_routes_fail_closed_at_the_asgi_boundary():
    client = _client_with_gateway_middleware_bypassed()
    try:
        responses = [
            client.post("/agents/bootstrap-token"),
            client.post("/agents/register", json={}),
            client.post("/agents/9/heartbeat", json={}),
            client.get("/agents/9/config"),
            client.get("/agents"),
            client.post("/agents/9/approve"),
        ]
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert [response.status_code for response in responses] == [410, 410, 410, 410, 410, 410]
    assert all(response.json()["error"]["code"] == RETIRED_CODE for response in responses)


def test_legacy_gateway_agent_event_websocket_is_rejected_without_accepting_a_subscription():
    client = _client_with_gateway_middleware_bypassed()
    try:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/agent-events"):
                pass
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert exc_info.value.code == 1008
