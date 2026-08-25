"""Source-contract regression for retired simulated PQC-readiness package."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PQC_READINESS_PACKAGE = ROOT / "features/pqc_readiness"
OPERATIONAL_AUDIT = ROOT / "backend_api/shared/operational_audit.py"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"


def test_simulated_pqc_readiness_package_remains_absent():
    assert not PQC_READINESS_PACKAGE.exists()


def test_retained_pqc_boundaries_remain_explicitly_separate():
    audit_source = OPERATIONAL_AUDIT.read_text(encoding="utf-8")
    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")

    assert "from backend_api.shared.pqc_wrapper import PQCWrapper" in audit_source
    assert "LEGACY_GATEWAY_PQC_API_RETIRED" in gateway_source
