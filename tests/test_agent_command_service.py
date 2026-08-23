from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from backend_api.agent_command_service.main import app


ROOT = Path(__file__).resolve().parents[1]
COMMAND_API_SOURCE = ROOT / "backend_api/agent_command_service/api.py"
RETIRED_CODE = "LEGACY_DIRECT_AGENT_COMMAND_API_RETIRED"


def test_direct_agent_command_source_removes_dispatch_and_broker_components():
    source = COMMAND_API_SOURCE.read_text(encoding="utf-8")

    for unsafe_component in (
        "KafkaProducer",
        "sign_command",
        "get_kafka_producer",
        "_publish_required_audit",
        "_publish_command",
        "_dispatch_authorized_command",
        "require_capability",
        "COMMAND_SIGNING_PRIVATE_KEY_ENV",
    ):
        assert unsafe_component not in source

    ast.parse(source, filename=str(COMMAND_API_SOURCE))


def test_direct_agent_command_routes_fail_closed_at_the_asgi_boundary():
    client = TestClient(app)

    responses = [
        client.post(
            "/api/v1/agents/agent-009/command",
            json={"command_type": "collect_processes", "arguments": {"include_hashes": True}},
        ),
        client.post(
            "/api/v1/agents/network/action",
            json={"action": "isolate_endpoint", "agent_id": "agent-009"},
        ),
    ]

    assert [response.status_code for response in responses] == [410, 410]
    assert all(response.json()["error"]["code"] == RETIRED_CODE for response in responses)
