from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.honeypot_service import main as legacy_honeypot


ROOT = Path(__file__).resolve().parents[1]
HONEYPOT_MAIN_PATH = ROOT / "backend_api/honeypot_service/main.py"


def test_legacy_honeypot_service_has_no_required_upstream_dependencies():
    assert legacy_honeypot.app.state.required_dependencies == ()


def test_legacy_honeypot_entrypoint_does_not_import_process_lifecycle_components():
    source = HONEYPOT_MAIN_PATH.read_text(encoding="utf-8")

    assert "honeypot_manager" not in source
    assert "ProcessHoneypotRunner" not in source
    assert "uvicorn.run" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/honeypots"),
        ("get", "/honeypots"),
        ("post", "/honeypots/example/stop"),
        ("get", "/honeypots/example/events"),
    ],
)
async def test_legacy_honeypot_lifecycle_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_honeypot.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-honeypot.test") as client:
        response = await client.request(method.upper(), path, json={})

    body = json.loads(response.content)
    assert response.status_code == 410
    assert body["error"]["code"] == "LEGACY_HONEYPOT_API_RETIRED"
