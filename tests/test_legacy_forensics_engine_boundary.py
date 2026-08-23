from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.forensics_engine import main as legacy_forensics


ROOT = Path(__file__).resolve().parents[1]
FORENSICS_APP_PATH = ROOT / "backend_api/forensics_engine/main.py"


def test_legacy_forensics_engine_has_no_required_upstream_dependencies():
    assert legacy_forensics.app.state.required_dependencies == ()


def test_legacy_forensics_entrypoint_does_not_retain_jobs_or_evidence_components():
    source = FORENSICS_APP_PATH.read_text(encoding="utf-8")

    assert "get_db" not in source
    assert "BackgroundTasks" not in source
    assert "forensics_vault_logger" not in source
    assert "timeline_router" not in source
    assert "evidence_router" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/jobs/"),
        ("get", "/jobs/"),
        ("post", "/timeline/"),
        ("post", "/evidence/"),
    ],
)
async def test_legacy_forensics_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_forensics.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-forensics.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_FORENSICS_API_RETIRED"
