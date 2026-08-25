"""Source-contract regression for retired neural-federation council simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEDERATION_PACKAGE = ROOT / "features/neural_federation_council"
AGENT_BRAIN = ROOT / "backend_api/ai_agent_orchestrator/agent_brain.py"


def test_neural_federation_council_simulation_package_remains_absent():
    assert not FEDERATION_PACKAGE.exists()


def test_retained_shared_consensus_boundary_remains_explicit():
    source = AGENT_BRAIN.read_text(encoding="utf-8")

    assert "from backend_api.shared.consensus_engine import ConsensusEngine" in source
    assert "self.consensus_engine = ConsensusEngine(quorum_threshold=0.66)" in source
