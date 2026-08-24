"""Source-contract regression for retired shared BlueTeamAI simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLUE_TEAM_AI = ROOT / "backend_api/shared/blue_team_ai.py"
SHARED_SERVICES = ROOT / "backend_api/shared/services.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_shared_blue_team_ai_simulation_and_startup_wiring_remain_absent():
    assert not BLUE_TEAM_AI.exists()

    shared_services = SHARED_SERVICES.read_text(encoding="utf-8")
    gateway = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "blue_team_ai" not in shared_services
    assert "BlueTeamAI" not in gateway
    assert "run_defense_cycle" not in shared_services


def test_governed_containment_remains_the_separate_response_boundary():
    containment_source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")

    assert "approval" in containment_source.lower()
    assert "rollback" in containment_source.lower()
