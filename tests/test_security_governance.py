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


def test_hmac_signed_audit_chain_requires_matching_key_and_key_id():
    signing_key = "test-audit-signing-key"
    first = append_record(
        "audit-signed-001",
        "analyst-1",
        "response:request",
        {"case_id": "CASE-001"},
        signing_key=signing_key,
        signature_key_id="audit-key-v1",
    )
    second = append_record(
        "audit-signed-002",
        "admin-1",
        "response:approve",
        {"approval_id": "APR-001"},
        previous_hash=first.record_hash,
        signing_key=signing_key,
        signature_key_id="audit-key-v1",
    )
    records = [first.as_dict(), second.as_dict()]

    assert verify_chain(records, signing_key=signing_key, require_signature=True, expected_key_id="audit-key-v1") is True
    assert verify_chain(records, signing_key="wrong-key", require_signature=True) is False
    assert verify_chain(records, signing_key=signing_key, require_signature=True, expected_key_id="audit-key-v2") is False


def test_hmac_audit_chain_rejects_unsigned_records_and_tampered_signatures():
    unsigned = append_record("audit-unsigned-001", "viewer-1", "alerts:read", {})
    assert verify_chain([unsigned.as_dict()], require_signature=True) is False

    signed = append_record(
        "audit-signed-003",
        "admin-1",
        "response:approve",
        {"approval_id": "APR-002"},
        signing_key="test-audit-signing-key",
        signature_key_id="audit-key-v1",
    ).as_dict()
    signed["signature"] = "0" * 64
    assert verify_chain([signed], signing_key="test-audit-signing-key", require_signature=True) is False


def test_signing_requires_an_explicit_key_identifier():
    with pytest.raises(ValueError, match="signature_key_id"):
        append_record("audit-invalid-001", "admin-1", "config:write", {}, signing_key="test-audit-signing-key")
