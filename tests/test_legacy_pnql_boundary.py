from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.pnql_engine import app as legacy_pnql


ROOT = Path(__file__).resolve().parents[1]
PNQL_APP_PATH = ROOT / "backend_api/pnql_engine/app.py"


def test_legacy_pnql_has_no_required_upstream_dependencies():
    assert legacy_pnql.app.state.required_dependencies == ()


def test_legacy_pnql_entrypoint_does_not_import_parser_or_executor():
    source = PNQL_APP_PATH.read_text(encoding="utf-8")

    assert "parse_query" not in source
    assert "execute_query" not in source
    assert "PNQLQuery" not in source


@pytest.mark.asyncio
async def test_legacy_pnql_query_route_fails_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=legacy_pnql.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-pnql.test") as client:
        response = await client.post("/query", json={"query": "search 'failed login'"})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_PNQL_API_RETIRED"
