"""Regressions for the retired ungoverned dashboard aggregation service."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from backend_api.dashboard_service import main as dashboard_service


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_MAIN = ROOT / "backend_api/dashboard_service/main.py"
DASHBOARD_API = ROOT / "backend_api/dashboard_service/api.py"


def test_legacy_dashboard_service_has_no_required_upstream_dependencies_or_router_module():
    assert dashboard_service.app.state.required_dependencies == ()
    assert not DASHBOARD_API.exists()


def test_retirement_boundary_has_no_fabricated_metrics_or_direct_downstream_calls():
    source = DASHBOARD_MAIN.read_text(encoding="utf-8")

    for retired_marker in (
        "httpx.AsyncClient",
        "ALERT_SERVICE_URL",
        "ATTACK_GRAPH_URL",
        "ASSET_SERVICE_URL",
        "AUTO_EXECUTE",
        "automated_remediations_count_24h",
        "overall_risk_score",
        "include_router",
    ):
        assert retired_marker not in source


@pytest.mark.asyncio
async def test_legacy_dashboard_paths_fail_closed_at_the_asgi_boundary():
    transport = httpx.ASGITransport(app=dashboard_service.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://dashboard.test") as client:
        responses = [
            await client.get("/api/dashboard/executive-summary"),
            await client.get("/api/dashboard/incident/example/details"),
        ]

    assert [response.status_code for response in responses] == [410, 410]
    assert all(json.loads(response.content)["error"]["code"] == "LEGACY_DASHBOARD_API_RETIRED" for response in responses)
