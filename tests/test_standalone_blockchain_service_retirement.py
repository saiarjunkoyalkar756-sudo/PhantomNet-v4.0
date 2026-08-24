"""Source-contract regressions for the retired standalone blockchain service process."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOCKCHAIN_DIR = ROOT / "backend_api/blockchain_service"
GATEWAY_MAIN = ROOT / "backend_api/gateway_service/main.py"
GOVERNED_CONTAINMENT = ROOT / "backend_api/soar_engine/governed_containment.py"
GOVERNED_API = ROOT / "backend_api/soar_engine/governed_api.py"


def test_unmounted_blockchain_service_process_and_claim_artifacts_remain_absent():
    assert not (BLOCKCHAIN_DIR / "app.py").exists()
    assert not (BLOCKCHAIN_DIR / "consumer.py").exists()
    assert not (BLOCKCHAIN_DIR / "Dockerfile").exists()
    assert not (BLOCKCHAIN_DIR / "AuditTrail.sol").exists()


def test_gateway_no_longer_imports_direct_blockchain_and_governed_audit_path_remains_distinct():
    gateway_source = GATEWAY_MAIN.read_text(encoding="utf-8")
    containment_source = GOVERNED_CONTAINMENT.read_text(encoding="utf-8")
    governed_api_source = GOVERNED_API.read_text(encoding="utf-8")

    assert "from backend_api.blockchain_service.blockchain import Blockchain" not in gateway_source
    assert "from backend_api.audit_log_collector.integrity import GENESIS_HASH, append_record" in containment_source
    assert "from backend_api.audit_log_collector.verification import ContainmentAuditVerifier" in governed_api_source
