from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.phantomql_engine import main as legacy_phantomql


ROOT = Path(__file__).resolve().parents[1]
PHANTOMQL_MAIN_PATH = ROOT / "backend_api/phantomql_engine/main.py"
PHANTOMQL_DOCKERFILE_PATH = ROOT / "backend_api/phantomql_engine/Dockerfile"


def test_legacy_phantomql_has_no_required_upstream_dependencies():
    assert legacy_phantomql.app.state.required_dependencies == ()


def test_legacy_phantomql_entrypoint_does_not_import_query_or_database_components():
    source = PHANTOMQL_MAIN_PATH.read_text(encoding="utf-8")

    assert "SessionLocal" not in source
    assert "get_normalized_events" not in source
    assert "_parse_phantomql_query" not in source
    assert '"main:app"' in PHANTOMQL_DOCKERFILE_PATH.read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/query/"),
        ("get", "/analytics/severity_counts"),
        ("get", "/analytics/event_type_counts"),
    ],
)
async def test_legacy_phantomql_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_phantomql.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-phantomql.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_PHANTOMQL_API_RETIRED"
