"""Source-contract regression for retired fabricated BAS simulation modules."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_SIMULATOR = ROOT / "backend_api/shared/bas_simulator.py"
SIMULATION_MODULES = ROOT / "backend_api/bas_engine/simulation_modules.py"
SHARED_SERVICES = ROOT / "backend_api/shared/services.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
BASELINE_SCENARIOS = ROOT / "backend_api/bas_engine/baseline_scenarios.py"
DETECTION_PIPELINE = ROOT / "backend_api/bas_engine/detection_pipeline.py"


def test_fabricated_bas_simulator_modules_and_imports_remain_absent():
    assert not SHARED_SIMULATOR.exists()
    assert not SIMULATION_MODULES.exists()
    assert "bas_simulator" not in SHARED_SERVICES.read_text(encoding="utf-8")
    assert "BASSimulator" not in GATEWAY_MAIN.read_text(encoding="utf-8")


def test_controlled_baseline_fixture_pipeline_remains_separate():
    assert "def emit_baseline_events" in BASELINE_SCENARIOS.read_text(encoding="utf-8")
    assert "emit_baseline_events" in DETECTION_PIPELINE.read_text(encoding="utf-8")
