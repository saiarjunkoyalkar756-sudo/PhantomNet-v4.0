"""Source-contract regression for retired cognitive-core simulation set."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COGNITIVE_CORE_PACKAGE = ROOT / "features/cognitive_core_intelligence"
COGNITIVE_MEMORY_PACKAGE = ROOT / "features/synthetic_cognitive_memory"
DATABASE_SOURCE = ROOT / "backend_api/shared/database.py"
DEFENSIVE_EVALUATION = ROOT / "backend_api/ai_behavioral_engine/defensive_evaluation.py"


def test_isolated_cognitive_simulation_packages_remain_absent():
    assert not COGNITIVE_CORE_PACKAGE.exists()
    assert not COGNITIVE_MEMORY_PACKAGE.exists()


def test_cognitive_memory_persistence_model_remains_absent():
    source = DATABASE_SOURCE.read_text(encoding="utf-8")

    assert "class CognitiveMemoryDB" not in source
    assert '"cognitive_memory"' not in source


def test_retained_defensive_evaluation_boundary_remains_advisory_only():
    source = DEFENSIVE_EVALUATION.read_text(encoding="utf-8")

    assert "advisory" in source.lower()
    assert "automatic_enforcement" in source
