from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.correlation_engine import app as correlation_app


ROOT = Path(__file__).resolve().parents[1]
CORRELATION_DOCKERFILE = ROOT / "backend_api/correlation_engine/Dockerfile"


def test_correlation_engine_declares_actual_database_and_kafka_dependencies():
    assert correlation_app.app.state.required_dependencies == ("database", "kafka")
    assert '"app:app"' in CORRELATION_DOCKERFILE.read_text(encoding="utf-8")


def test_governed_rule_routes_remain_capability_protected_after_legacy_retirement():
    routes = {
        route.path: route
        for route in correlation_app.app.routes
        if getattr(route, "path", "") in {"/governed-rules", "/governed-rules/quality"}
    }

    assert set(routes) == {"/governed-rules", "/governed-rules/quality"}
    for route in routes.values():
        assert route.dependant.dependencies


@pytest.mark.asyncio
async def test_legacy_rule_api_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=correlation_app.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://correlation.test") as client:
        response = await client.post(
            "/rules",
            json={"name": "legacy-bypass", "logic": {}, "action": "alert", "severity": "critical"},
        )

    payload = json.loads(response.content)
    assert response.status_code == 410
    assert payload["error"]["code"] == "LEGACY_RULE_API_RETIRED"
    assert "/governed-rules" in payload["error"]["message"]


def test_correlation_engine_no_longer_imports_the_legacy_rule_store_from_its_api_entrypoint():
    source = (ROOT / "backend_api/correlation_engine/app.py").read_text(encoding="utf-8")

    assert "get_all_rules" not in source
    assert "upsert_rule" not in source
    assert "class Rule(" not in source
