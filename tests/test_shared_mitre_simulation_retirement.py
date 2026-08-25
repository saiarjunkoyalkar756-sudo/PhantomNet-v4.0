"""Source-contract regression for retired randomized shared MITRE simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED_MITRE_SIMULATION = ROOT / "backend_api/shared/mitre_attack_integration.py"
GOVERNED_CORRELATION = ROOT / "backend_api/correlation_engine/governed_correlation.py"
THREAT_HUNTING = ROOT / "backend_api/threat_hunting_service/service.py"


def test_randomized_shared_mitre_simulation_remains_absent():
    assert not SHARED_MITRE_SIMULATION.exists()


def test_governed_mitre_evidence_paths_remain_separate():
    correlation_source = GOVERNED_CORRELATION.read_text(encoding="utf-8")
    hunting_source = THREAT_HUNTING.read_text(encoding="utf-8")

    assert "mitre" in correlation_source.lower()
    assert "mitre" in hunting_source.lower()
