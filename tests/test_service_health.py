import pytest
from fastapi.responses import JSONResponse

from backend_api.shared import health
from backend_api.shared.service_factory import create_phantom_service


async def _healthy_component():
    return {"status": "healthy"}


async def _unhealthy_component():
    return {"status": "unhealthy", "error_code": "TEST_DEPENDENCY_UNAVAILABLE", "error_type": "ConnectionError"}


@pytest.mark.asyncio
async def test_safe_mode_health_explicitly_marks_dependencies_disabled(monkeypatch):
    monkeypatch.setattr(health, "SAFE_MODE", True)

    result = await health.run_standard_health_check(required_dependencies=("database", "kafka"))

    assert result["status"] == "healthy"
    assert result["readiness"] == "safe_mode"
    assert result["mode"] == "safe"
    assert result["components"]["database"]["status"] == "disabled"
    assert result["components"]["database"]["reason"] == "safe_mode"


@pytest.mark.asyncio
async def test_active_mode_reports_ready_only_when_all_declared_dependencies_are_healthy(monkeypatch):
    monkeypatch.setattr(health, "SAFE_MODE", False)
    monkeypatch.setitem(health.HEALTH_CHECKS, "database", _healthy_component)
    monkeypatch.setitem(health.HEALTH_CHECKS, "kafka", _healthy_component)

    result = await health.run_standard_health_check(required_dependencies=("database", "kafka"))

    assert result["status"] == "healthy"
    assert result["readiness"] == "ready"
    assert result["mode"] == "active"


@pytest.mark.asyncio
async def test_active_mode_reports_degraded_without_exposing_dependency_exception_text(monkeypatch):
    monkeypatch.setattr(health, "SAFE_MODE", False)
    monkeypatch.setitem(health.HEALTH_CHECKS, "database", _healthy_component)
    monkeypatch.setitem(health.HEALTH_CHECKS, "kafka", _unhealthy_component)

    result = await health.run_standard_health_check(required_dependencies=("database", "kafka"))

    assert result["status"] == "degraded"
    assert result["readiness"] == "not_ready"
    assert result["components"]["kafka"] == {
        "status": "unhealthy",
        "error_code": "TEST_DEPENDENCY_UNAVAILABLE",
        "error_type": "ConnectionError",
    }


@pytest.mark.asyncio
async def test_standard_service_exposes_liveness_and_failing_readiness_in_safe_mode(monkeypatch):
    monkeypatch.setattr(health, "SAFE_MODE", True)
    app = create_phantom_service("Health Test Service", "Test service", version="9.9.9")
    routes = {route.path: route.endpoint for route in app.routes if hasattr(route, "endpoint")}

    liveness = await routes["/health"]()
    readiness = await routes["/ready"]()

    assert liveness["success"] is True
    assert liveness["data"]["service"] == "Health Test Service"
    assert liveness["data"]["version"] == "9.9.9"
    assert liveness["data"]["readiness"] == "safe_mode"
    assert isinstance(readiness, JSONResponse)
    assert readiness.status_code == 503
