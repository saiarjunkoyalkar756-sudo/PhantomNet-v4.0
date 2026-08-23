from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.sandbox_service import app as legacy_sandbox


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_APP_PATH = ROOT / "backend_api/sandbox_service/app.py"


def test_legacy_sandbox_has_no_required_upstream_dependencies():
    assert legacy_sandbox.app.state.required_dependencies == ()


def test_legacy_sandbox_entrypoint_does_not_retain_upload_or_execution_components():
    source = SANDBOX_APP_PATH.read_text(encoding="utf-8")

    assert "SandboxRunner" not in source
    assert "UploadFile" not in source
    assert "run_plugin_in_sandbox" not in source
    assert "sandbox_runner" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/health_detailed"),
        ("post", "/analyze"),
    ],
)
async def test_legacy_sandbox_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_sandbox.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-sandbox.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_SANDBOX_API_RETIRED"
