from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.asset_inventory_service import main as legacy_asset_relationship


ROOT = Path(__file__).resolve().parents[1]
ASSET_RELATIONSHIP_APP_PATH = ROOT / "backend_api/asset_inventory_service/main.py"


def test_legacy_asset_relationship_service_has_no_required_upstream_dependencies():
    assert legacy_asset_relationship.app.state.required_dependencies == ()


def test_legacy_asset_relationship_entrypoint_does_not_initialize_fixture_graph():
    source = ASSET_RELATIONSHIP_APP_PATH.read_text(encoding="utf-8")

    assert "load_mock_data" not in source
    assert "get_asset_by_id" not in source
    assert "get_asset_dependencies" not in source
    assert "get_asset_dependents" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/assets/prod-db-01",
        "/assets/prod-db-01/dependencies",
        "/assets/prod-db-01/dependents",
    ],
)
async def test_legacy_asset_relationship_routes_fail_closed_at_the_asgi_boundary(path: str):
    transport = httpx.ASGITransport(app=legacy_asset_relationship.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-asset-relationship.test") as client:
        response = await client.get(path)

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_ASSET_RELATIONSHIP_API_RETIRED"
