from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.soc_copilot_service import main as legacy_soc_copilot


ROOT = Path(__file__).resolve().parents[1]
SOC_COPILOT_APP_PATH = ROOT / "backend_api/soc_copilot_service/app.py"
SOC_COPILOT_MAIN_PATH = ROOT / "backend_api/soc_copilot_service/main.py"
SOC_COPILOT_CONTEXT_BUILDER_PATH = ROOT / "backend_api/soc_copilot_service/context_builder/main.py"


def test_legacy_soc_copilot_has_no_required_upstream_dependencies():
    assert legacy_soc_copilot.app.state.required_dependencies == ()


def test_legacy_soc_copilot_sources_do_not_retain_context_or_generation_components():
    source = SOC_COPILOT_APP_PATH.read_text(encoding="utf-8") + SOC_COPILOT_MAIN_PATH.read_text(encoding="utf-8")

    assert "build_alert_context" not in source
    assert "get_siem_db" not in source
    assert "get_vuln_db" not in source
    assert "SOCCopilotService" not in source
    assert "auto_investigate" not in source
    assert "generate_detection_rule" not in source
    assert "generate_threat_report" not in source
    assert not SOC_COPILOT_CONTEXT_BUILDER_PATH.exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/v1/copilot/explain_alert/"),
        ("post", "/api/v1/copilot/generate_detection_rule/"),
        ("post", "/api/v1/copilot/generate_threat_report/"),
    ],
)
async def test_legacy_soc_copilot_routes_fail_closed_at_the_asgi_boundary(method: str, path: str):
    transport = httpx.ASGITransport(app=legacy_soc_copilot.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://legacy-soc-copilot.test") as client:
        response = await client.request(method.upper(), path, json={})

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_SOC_COPILOT_API_RETIRED"
