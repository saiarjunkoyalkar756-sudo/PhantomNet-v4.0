"""Source-contract regression for retired silent-remediation simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAMLESS_DEFENSE_PACKAGE = ROOT / "features/invisible_security_experience"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_silent_remediation_simulation_package_remains_absent():
    assert not SEAMLESS_DEFENSE_PACKAGE.exists()


def test_governed_containment_remains_approval_and_verification_bound():
    source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")

    assert "Human-governed containment lifecycle" in source
    assert "HMAC-signed audit evidence" in source
    assert "Containment rollback requires a verified execution with rollback evidence." in source
