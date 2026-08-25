"""Source-contract regression for retired behavioral-biometrics simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BIOMETRICS_PACKAGE = ROOT / "features/behavioral_biometrics"
OPERATIONAL_AUDIT = ROOT / "backend_api/shared/operational_audit.py"


def test_behavioral_biometrics_simulation_package_remains_absent():
    assert not BIOMETRICS_PACKAGE.exists()


def test_retained_shared_biometric_audit_boundary_remains_explicit():
    source = OPERATIONAL_AUDIT.read_text(encoding="utf-8")

    assert "from backend_api.shared.bio_fusion_engine import BioFusionEngine" in source
    assert "TEST: Bio-Fusion Behavioral Identity..." in source
