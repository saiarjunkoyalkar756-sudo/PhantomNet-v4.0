from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend_api.gateway_service.main import app


ROOT = Path(__file__).resolve().parents[1]
ECOSYSTEM_SOURCE = ROOT / "backend_api/gateway_service/api_ecosystem.py"
RETIRED_CODE = "LEGACY_GATEWAY_ECOSYSTEM_API_RETIRED"


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


def test_ecosystem_source_does_not_retain_conceptual_data_or_filesystem_components():
    source = ECOSYSTEM_SOURCE.read_text(encoding="utf-8")

    assert "AttackLog" not in source
    assert "get_current_user" not in source
    assert "generate_sdk_python" not in source
    assert "phantomnet_sdk_python" not in source
    assert "graphql_endpoint" not in source
    ast.parse(source, filename=str(ECOSYSTEM_SOURCE))


def test_legacy_gateway_ecosystem_routes_fail_closed_at_the_asgi_boundary():
    client = _client_with_gateway_middleware_bypassed()
    try:
        responses = [
            client.get("/analytics/threat_summary"),
            client.get("/reports/daily_digest"),
            client.post("/graphql", json={"query": "{ alerts }"}),
        ]
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert [response.status_code for response in responses] == [410, 410, 410]
    assert all(response.json()["error"]["code"] == RETIRED_CODE for response in responses)
