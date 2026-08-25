"""Source-contract regression for retired emotional incident-assistant simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_PACKAGE = ROOT / "features/emotionally_aware_incident_assistant"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_emotional_incident_assistant_simulation_package_remains_absent():
    assert not ASSISTANT_PACKAGE.exists()


def test_governed_containment_remains_human_approval_and_rollback_bound():
    source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")

    assert "Human-governed containment lifecycle" in source
    assert "HMAC-signed audit evidence" in source
    assert "Containment rollback requires a verified execution with rollback evidence." in source
