from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.compliance_reporting_service import app as legacy_compliance_reporting


ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE_REPORTING_APP_PATH = ROOT / "backend_api/compliance_reporting_service/app.py"


def test_legacy_compliance_reporting_has_no_required_upstream_dependencies():
    assert legacy_compliance_reporting.app.state.required_dependencies == ()


def test_legacy_compliance_reporting_entrypoint_does_not_retain_fixture_reporting_components():
    source = COMPLIANCE_REPORTING_APP_PATH.read_text(encoding="utf-8")

    assert "generate_pdf_report" not in source
    assert "reports_store" not in source
    assert "FileResponse" not in source
    assert "generated_reports" not in source


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/reports/generate"),
        ("get", "/reports"),
        ("get", "/reports/example/download"),
    ],
)
async def test_legacy_compliance_reporting_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_compliance_reporting.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-compliance-reporting.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_COMPLIANCE_REPORTING_API_RETIRED"
