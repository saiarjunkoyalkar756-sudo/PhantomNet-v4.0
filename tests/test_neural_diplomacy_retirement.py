"""Source-contract regression for retired neural-diplomacy simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIPLOMACY_PACKAGE = ROOT / "features/neural_diplomacy_protocols"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_neural_diplomacy_simulation_package_remains_absent():
    assert not DIPLOMACY_PACKAGE.exists()


def test_governed_containment_remains_approval_and_audit_bound():
    source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")

    assert "Containment execution requires configured HMAC-signed audit evidence." in source
    assert 'request_row.status == "approved"' in source
    assert 'approval_state == "approved"' in source
    assert 'execution_row.status == "verified"' in source
