from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.plugin_marketplace import app as legacy_marketplace


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_APP_PATH = ROOT / "backend_api/plugin_marketplace/app.py"


def test_legacy_plugin_marketplace_has_no_required_upstream_dependencies():
    assert legacy_marketplace.app.state.required_dependencies == ()


def test_legacy_plugin_marketplace_entrypoint_does_not_import_artifact_manager():
    source = MARKETPLACE_APP_PATH.read_text(encoding="utf-8")

    assert "PluginManager" not in source
    assert "UploadFile" not in source
    assert "plugin_manager" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/plugins/upload"),
        ("get", "/plugins"),
        ("get", "/plugins/example"),
        ("post", "/plugins/example/enable"),
        ("post", "/plugins/example/disable"),
    ],
)
async def test_legacy_plugin_marketplace_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_marketplace.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-marketplace.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_PLUGIN_MARKETPLACE_API_RETIRED"
