from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.siem_integration_service import app as legacy_siem


ROOT = Path(__file__).resolve().parents[1]
SIEM_APP_PATH = ROOT / "backend_api/siem_integration_service/app.py"


def test_legacy_siem_integration_has_no_required_upstream_dependencies():
    assert legacy_siem.app.state.required_dependencies == ()


def test_legacy_siem_integration_entrypoint_does_not_import_ingest_or_query_components():
    source = SIEM_APP_PATH.read_text(encoding="utf-8")

    assert "SIEMIngestService" not in source
    assert "PhantomQLEngine" not in source
    assert "raw_logs_store" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/siem/ingest"),
        ("post", "/api/siem/query"),
        ("get", "/api/siem/workspaces"),
        ("get", "/api/siem/logs/normalized"),
        ("get", "/api/siem/logs/raw"),
    ],
)
async def test_legacy_siem_integration_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_siem.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-siem.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_SIEM_INTEGRATION_API_RETIRED"
