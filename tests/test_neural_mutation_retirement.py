"""Source-contract regression for retired randomized signature-mutation simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MUTATION_PACKAGE = ROOT / "features/self_evolving_threat_brain"
EVENT_STREAM_PROCESSOR = ROOT / "backend_api/shared/event_stream_processor.py"


def test_randomized_signature_mutation_package_remains_absent():
    assert not MUTATION_PACKAGE.exists()


def test_event_processor_retains_deterministic_rule_fallback():
    source = EVENT_STREAM_PROCESSOR.read_text(encoding="utf-8")

    assert "AI correlation plugin is unavailable; retaining deterministic rule," in source
    assert "threat-intelligence, and UEBA analysis without an advisory anomaly result." in source
