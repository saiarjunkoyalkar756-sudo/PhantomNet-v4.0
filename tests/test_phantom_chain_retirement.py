"""Source-contract regression for retired phantom-chain simulation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHANTOM_CHAIN_PACKAGE = ROOT / "features/phantom_chain"
DATABASE_SOURCE = ROOT / "backend_api/shared/database.py"
AUDIT_INTEGRITY = ROOT / "backend_api/audit_log_collector/integrity.py"


def test_phantom_chain_simulation_package_remains_absent():
    assert not PHANTOM_CHAIN_PACKAGE.exists()


def test_phantom_chain_persistence_model_remains_absent():
    source = DATABASE_SOURCE.read_text(encoding="utf-8")

    assert "class PhantomChainDB" not in source
    assert '"phantom_chain"' not in source


def test_signed_audit_integrity_boundary_remains_explicit():
    source = AUDIT_INTEGRITY.read_text(encoding="utf-8")

    assert "Tamper-evident and optionally HMAC-signed audit records." in source
    assert "verify_chain" in source
