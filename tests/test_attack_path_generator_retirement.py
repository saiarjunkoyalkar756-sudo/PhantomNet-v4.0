"""Source-contract regression for retired simulated attack-path generation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMULATED_GENERATOR = ROOT / "backend_api/shared/attack_path_generator.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
GOVERNED_ATTACK_PATHS = ROOT / "backend_api/attack_graph_engine/governed_attack_paths.py"
GOVERNED_API = ROOT / "backend_api/attack_graph_engine/governed_api.py"


def test_simulated_attack_path_generator_and_gateway_import_remain_absent():
    assert not SIMULATED_GENERATOR.exists()
    source = GATEWAY_MAIN.read_text(encoding="utf-8")
    assert "attack_path_generator" not in source
    assert "generate_simulated_attack_path" not in source


def test_governed_tenant_scoped_attack_path_analysis_remains_separate():
    service_source = GOVERNED_ATTACK_PATHS.read_text(encoding="utf-8")
    api_source = GOVERNED_API.read_text(encoding="utf-8")

    assert "tenant_id" in service_source
    assert "analyze" in service_source
    assert "analyze_attack_path" in api_source
