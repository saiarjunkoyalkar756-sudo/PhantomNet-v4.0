"""Source-contract regression for retired speculative cross-domain fusion simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FUSION_PACKAGE = ROOT / "features/cross_domain_fusion_intelligence"
OPERATIONAL_AUDIT = ROOT / "backend_api/shared/operational_audit.py"


def test_speculative_cross_domain_fusion_package_remains_absent():
    assert not FUSION_PACKAGE.exists()


def test_retained_shared_biometric_audit_boundary_remains_explicit():
    source = OPERATIONAL_AUDIT.read_text(encoding="utf-8")

    assert "from backend_api.shared.bio_fusion_engine import BioFusionEngine" in source
    assert "TEST: Bio-Fusion Behavioral Identity..." in source
