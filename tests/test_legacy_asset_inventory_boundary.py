from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.asset_inventory import app as legacy_asset_inventory


ROOT = Path(__file__).resolve().parents[1]
ASSET_INVENTORY_APP_PATH = ROOT / "backend_api/asset_inventory/app.py"


def test_legacy_asset_inventory_has_no_required_upstream_dependencies():
    assert legacy_asset_inventory.app.state.required_dependencies == ()


def test_legacy_asset_inventory_entrypoint_does_not_import_scanner_or_asset_store():
    source = ASSET_INVENTORY_APP_PATH.read_text(encoding="utf-8")

    assert "run_scan" not in source
    assert "get_all_assets" not in source
    assert "create_assets_table" not in source
    assert "background_tasks.add_task" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/scan"),
        ("get", "/assets"),
    ],
)
async def test_legacy_asset_inventory_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_asset_inventory.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-assets.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_ASSET_INVENTORY_API_RETIRED"
