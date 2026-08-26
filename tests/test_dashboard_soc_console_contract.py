"""Source contracts for the evidence-first PhantomNet SOC console rebuild."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard_frontend/src/pages/Dashboard.jsx"
SIDEBAR = ROOT / "dashboard_frontend/src/components/shared/Sidebar.jsx"
ROUTER = ROOT / "dashboard_frontend/src/router/index.jsx"
PROTECTED_ROUTE = ROOT / "dashboard_frontend/src/router/ProtectedRoute.jsx"
APP_CSS = ROOT / "dashboard_frontend/src/App.css"


def test_soc_console_preserves_evidence_first_empty_states_and_governed_response_language():
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "SOC command center" in source
    assert "No governed technique evidence available" in source
    assert "It does not synthesize telemetry or AI findings." in source
    assert "approval → signed audit → adapter → verification → rollback" in source
    assert "ADVISORY ONLY" in source
    assert "DEPLOYMENT-GATED" in source


def test_dashboard_shell_has_a_default_route_and_operator_navigation():
    router_source = ROUTER.read_text(encoding="utf-8")
    sidebar_source = SIDEBAR.read_text(encoding="utf-8")

    assert 'element: <Navigate to="/dashboard" replace />' in router_source
    assert "Command center" in sidebar_source
    assert "Case management" in sidebar_source
    assert "Governed response" in sidebar_source
    assert "Evidence-first mode" in sidebar_source


def test_dashboard_removes_vite_starter_root_constraint_and_uses_stable_auth_subscriptions():
    css_source = APP_CSS.read_text(encoding="utf-8")
    protected_route_source = PROTECTED_ROUTE.read_text(encoding="utf-8")

    assert "max-width: 1280px" not in css_source
    assert "min-height: 100vh" in css_source
    assert "const accessToken = useAuthStore((state) => state.accessToken);" in protected_route_source
    assert "const loading = useAuthStore((state) => state.loading);" in protected_route_source
    assert "accessToken: state.accessToken" not in protected_route_source
