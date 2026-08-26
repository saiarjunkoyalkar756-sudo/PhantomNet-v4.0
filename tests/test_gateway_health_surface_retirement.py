"""Regression contract for retirement of the gateway's unsound legacy health router."""
from __future__ import annotations

from pathlib import Path

from backend_api.gateway_service.main import app


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_SOURCE = ROOT / "backend_api/gateway_service/main.py"
LEGACY_HEALTH_ROUTER = ROOT / "backend_api/gateway_service/routes/health.py"


def test_placeholder_gateway_health_router_remains_absent():
    assert not LEGACY_HEALTH_ROUTER.exists()


def test_gateway_retains_only_standard_factory_health_surfaces():
    source = GATEWAY_SOURCE.read_text(encoding="utf-8")
    paths = {route.path for route in app.routes}

    assert "backend_api.gateway_service.routes.health" not in source
    assert "/health" in paths
    assert "/ready" in paths
    assert "/metrics" in paths
    assert "/health/" not in paths
