from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend_api.gateway_service.main import app


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR_SOURCE = ROOT / "backend_api/gateway_service/orchestrator_api.py"
RETIRED_CODE = "LEGACY_GATEWAY_ORCHESTRATOR_MUTATION_RETIRED"
BLOCKCHAIN_RETIRED_CODE = "LEGACY_GATEWAY_BLOCKCHAIN_API_RETIRED"


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


def test_orchestrator_source_does_not_retain_legacy_mutation_or_blockchain_components():
    source = ORCHESTRATOR_SOURCE.read_text(encoding="utf-8")

    for unsafe_component in (
        "CommandDispatcher",
        "httpx.AsyncClient",
        "TELEMETRY_INGESTOR_URL",
        ".mine_block(",
        "from backend_api.blockchain_service.blockchain import Blockchain",
        "from backend_api.shared.database import get_db, Block, Transaction, User",
        "is_chain_valid()",
        "block.to_dict()",
    ):
        assert unsafe_component not in source
    ast.parse(source, filename=str(ORCHESTRATOR_SOURCE))


def test_legacy_gateway_orchestrator_mutations_fail_closed_at_the_asgi_boundary():
    client = _client_with_gateway_middleware_bypassed()
    try:
        responses = [
            client.post("/orchestrator/blockchain/add_transaction", json={"ip": "198.51.100.7", "data": "x"}),
            client.post("/orchestrator/honeypot/control", json={"action": "start", "port": 22}),
            client.post("/orchestrator/honeypot/simulate_attack", json={"ip": "198.51.100.8", "port": 443, "data": "probe"}),
        ]
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert [response.status_code for response in responses] == [410, 410, 410]
    assert all(response.json()["error"]["code"] == RETIRED_CODE for response in responses)


def test_legacy_gateway_blockchain_routes_fail_closed_at_the_asgi_boundary():
    client = _client_with_gateway_middleware_bypassed()
    try:
        responses = [
            client.get("/orchestrator/blockchain"),
            client.post("/orchestrator/blockchain/verify"),
        ]
    finally:
        client._phantomnet_rate_limit_patch.stop()  # type: ignore[attr-defined]
        client._phantomnet_session_patch.stop()  # type: ignore[attr-defined]

    assert [response.status_code for response in responses] == [410, 410]
    assert all(response.json()["error"]["code"] == BLOCKCHAIN_RETIRED_CODE for response in responses)
