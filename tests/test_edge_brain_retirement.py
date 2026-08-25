"""Source-contract regression for retired pseudo-enforcement edge-brain package."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EDGE_BRAIN_PACKAGE = ROOT / "features/phantom_os"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"


def test_pseudo_enforcement_edge_brain_package_remains_absent():
    assert not EDGE_BRAIN_PACKAGE.exists()


def test_governed_containment_lifecycle_remains_approval_and_rollback_bound():
    source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")

    assert "Human-governed containment lifecycle" in source
    assert "HMAC-signed audit evidence" in source
    assert "Containment rollback requires a verified execution with rollback evidence." in source
