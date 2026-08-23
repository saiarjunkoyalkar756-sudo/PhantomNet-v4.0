from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.api_gateway import app as legacy_gateway


ROOT = Path(__file__).resolve().parents[1]
LEGACY_GATEWAY_PATH = ROOT / "backend_api/api_gateway/app.py"


def test_legacy_gateway_has_no_required_upstream_dependencies():
    assert legacy_gateway.app.state.required_dependencies == ()


def test_legacy_gateway_does_not_import_or_register_legacy_router_surfaces():
    source = LEGACY_GATEWAY_PATH.read_text(encoding="utf-8")

    assert "admin_router" not in source
    assert "agent_router" not in source
    assert "orchestrator_router" not in source
    assert "auth_router" not in source
    assert "include_router" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/admin/blacklist/add"),
        ("post", "/agents/register"),
        ("get", "/agents"),
        ("post", "/auth/login"),
        ("post", "/orchestrator/honeypot/control"),
    ],
)
async def test_legacy_gateway_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_gateway.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-gateway.test") as client:
        response = await client.request(method.upper(), path, json={})

    body = json.loads(response.content)
    assert response.status_code == 410
    assert body["error"]["code"] == "LEGACY_API_GATEWAY_RETIRED"


@pytest.mark.asyncio
async def test_legacy_gateway_keeps_standard_health_and_readiness_routes():
    transport = httpx.ASGITransport(app=legacy_gateway.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-gateway.test") as client:
        health = await client.get("/health")
        compatibility_health = await client.get("/health_status")

    assert health.status_code == 200
    assert compatibility_health.status_code == 200
    assert json.loads(compatibility_health.content)["data"]["legacy_gateway"] == "retired"
