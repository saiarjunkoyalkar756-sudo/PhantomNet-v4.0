from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.dfir_toolkit import app as legacy_dfir


ROOT = Path(__file__).resolve().parents[1]
DFIR_APP_PATH = ROOT / "backend_api/dfir_toolkit/app.py"


def test_legacy_dfir_toolkit_has_no_required_upstream_dependencies():
    assert legacy_dfir.app.state.required_dependencies == ()


def test_legacy_dfir_toolkit_entrypoint_does_not_import_tools_or_upload_handling():
    source = DFIR_APP_PATH.read_text(encoding="utf-8")

    assert "run_yara_scan" not in source
    assert "analyze_memory_dump" not in source
    assert "analyze_pcap" not in source
    assert "reconstruct_timeline" not in source
    assert "UploadFile" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/yara_scan",
        "/memory_analysis",
        "/pcap_analysis",
        "/timeline_reconstruction",
        "/upload_for_analysis",
    ],
)
async def test_legacy_dfir_toolkit_routes_fail_closed_at_the_asgi_boundary(path: str):
    transport = httpx.ASGITransport(app=legacy_dfir.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-dfir.test") as client:
        response = await client.post(path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_DFIR_API_RETIRED"
