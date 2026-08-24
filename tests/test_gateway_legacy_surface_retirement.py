"""Source-level regressions for retired, unmounted gateway legacy surfaces."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
LEGACY_ALERT_MANAGER = ROOT / "backend_api/gateway_service/alert_manager_api.py"


def test_orphaned_gateway_alert_manager_remains_removed():
    """Do not restore in-memory alerts, unauthenticated sockets, or alert simulation by accident."""
    assert not LEGACY_ALERT_MANAGER.exists()

    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "alert_manager_api" not in gateway_source
    assert "include_router(alert_manager" not in gateway_source
