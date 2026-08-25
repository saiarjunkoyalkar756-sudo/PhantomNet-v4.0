"""Regression coverage for deterministic side-effect-free gateway readiness monitoring."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEALTH_MONITOR = ROOT / "backend_api/shared/health_monitor.py"
STRUCTURED_HEALTH = ROOT / "backend_api/shared/health.py"
SERVICE_FACTORY = ROOT / "backend_api/shared/service_factory.py"


def test_gateway_health_monitor_delegates_to_structured_readiness_without_side_effects():
    source = HEALTH_MONITOR.read_text(encoding="utf-8")

    assert "run_standard_health_check(GATEWAY_REQUIRED_DEPENDENCIES)" in source
    assert "health-monitor interval must be positive" in source
    assert "random." not in source
    assert "http://localhost" not in source
    assert "gossip" not in source
    assert "rotate-key" not in source
    assert "AttackLog" not in source


def test_structured_liveness_and_readiness_paths_remain_separate():
    health_source = STRUCTURED_HEALTH.read_text(encoding="utf-8")
    factory_source = SERVICE_FACTORY.read_text(encoding="utf-8")

    assert "run_standard_health_check" in health_source
    assert '"/health"' in factory_source
    assert '"/ready"' in factory_source
