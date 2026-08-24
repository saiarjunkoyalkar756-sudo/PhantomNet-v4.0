"""Source-level regressions for retired, unmounted gateway legacy surfaces."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
LEGACY_ALERT_MANAGER = ROOT / "backend_api/gateway_service/alert_manager_api.py"
LEGACY_RAW_PNQL_DASHBOARD = ROOT / "backend_api/gateway_service/dashboard_api.py"
LEGACY_FIXTURE_DASHBOARD = ROOT / "backend_api/gateway_service/routes/dashboard_api.py"
LEGACY_GATEWAY_WEBSOCKET_API = ROOT / "backend_api/gateway_service/websocket_api.py"
LEGACY_GATEWAY_POLICY_API = ROOT / "backend_api/gateway_service/policy_api.py"


def test_orphaned_gateway_policy_router_remains_removed():
    """Do not restore unscoped policy CRUD without authorization and durable governance."""
    assert not LEGACY_GATEWAY_POLICY_API.exists()

    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "policy_api" not in gateway_source
    assert "include_router(policy" not in gateway_source


def test_orphaned_gateway_websocket_router_remains_removed():
    """Do not restore query-token event or log streams without governed scope controls."""
    assert not LEGACY_GATEWAY_WEBSOCKET_API.exists()

    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "websocket_api" not in gateway_source
    assert "include_router(websocket" not in gateway_source


def test_orphaned_gateway_dashboard_modules_remain_removed():
    """Do not restore raw PNQL execution or fixture dashboard reporting by accident."""
    assert not LEGACY_RAW_PNQL_DASHBOARD.exists()
    assert not LEGACY_FIXTURE_DASHBOARD.exists()

    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "dashboard_api" not in gateway_source
    assert "include_router(dashboard" not in gateway_source


def test_orphaned_gateway_alert_manager_remains_removed():
    """Do not restore in-memory alerts, unauthenticated sockets, or alert simulation by accident."""
    assert not LEGACY_ALERT_MANAGER.exists()

    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "alert_manager_api" not in gateway_source
    assert "include_router(alert_manager" not in gateway_source
