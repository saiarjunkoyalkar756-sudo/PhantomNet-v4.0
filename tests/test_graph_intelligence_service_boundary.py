from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import yaml

from backend_api.graph_intelligence_service import main as graph_main


ROOT = Path(__file__).resolve().parents[1]
GRAPH_DOCKERFILE = ROOT / "backend_api/graph_intelligence_service/Dockerfile"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


def test_graph_intelligence_declares_neo4j_only_readiness_and_real_container_entrypoint():
    assert graph_main.app.state.required_dependencies == ("neo4j",)
    assert '"main:app"' in GRAPH_DOCKERFILE.read_text(encoding="utf-8")


def test_graph_intelligence_compose_healthcheck_uses_ready_route():
    compose = yaml.safe_load(ROOT_COMPOSE_PATH.read_text(encoding="utf-8"))
    healthcheck = compose["services"]["graph-intelligence-service"]["healthcheck"]

    assert healthcheck["test"][0] == "CMD-SHELL"
    assert "/ready" in healthcheck["test"][1]
    assert healthcheck["timeout"] == "5s"
    assert healthcheck["retries"] == 3


@pytest.mark.asyncio
async def test_graph_startup_verifies_and_shutdown_closes_the_owned_connection(monkeypatch):
    calls: list[str] = []

    class FakeConnection:
        def query(self, query: str):
            calls.append(query)
            return [{"ready": 1}]

        def close(self):
            calls.append("close")

    connection = FakeConnection()
    monkeypatch.setattr(graph_main, "get_db_connection", lambda: connection)
    monkeypatch.setattr(graph_main, "Neo4jConnection", FakeConnection)

    await graph_main.graph_startup(graph_main.app)
    await graph_main.graph_shutdown(graph_main.app)

    assert calls == ["RETURN 1 AS ready", "close"]


@pytest.mark.asyncio
async def test_raw_graph_query_route_is_retired_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=graph_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://graph.test") as client:
        response = await client.post("/graph", json={"query": "MATCH (n) DETACH DELETE n"})

    payload = json.loads(response.content)
    assert response.status_code == 410
    assert payload["error"]["code"] == "RAW_GRAPH_API_RETIRED"
    assert "governed graph investigation" in payload["error"]["message"]
