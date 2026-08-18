import pytest

from backend_api.audit_log_collector.integrity import append_record, verify_chain
from backend_api.iam_service.policy import authorize, require_authorized


def test_central_rbac_enforces_privileged_capabilities():
    assert authorize("viewer", "alerts:read").allowed is True
    assert authorize("analyst", "response:request").allowed is True
    assert authorize("analyst", "response:approve").allowed is False
    assert authorize("admin", "response:approve").allowed is True
    with pytest.raises(PermissionError):
        require_authorized("viewer", "config:write")


def test_audit_chain_detects_payload_and_link_tampering():
    first = append_record("audit-001", "analyst-1", "response:request", {"case_id": "CASE-001"})
    second = append_record("audit-002", "admin-1", "response:approve", {"approval_id": "APR-001"}, first.record_hash)
    records = [first.as_dict(), second.as_dict()]
    assert verify_chain(records) is True

    records[1]["payload"]["approval_id"] = "APR-TAMPERED"
    assert verify_chain(records) is False
