from unittest.mock import MagicMock

from backend_api.soar_engine.response_providers import HttpResponseProvider, ResponseRequest


def _request(**overrides):
    values = {
        "action": "block_ip",
        "target": "198.51.100.42",
        "tenant_id": "tenant-lab",
        "requested_by": "analyst@example.test",
        "approval_id": "APR-001",
        "idempotency_key": "case-001:block-ip",
        "metadata": {"case_id": "CASE-001", "requester_role": "analyst"},
    }
    values.update(overrides)
    return ResponseRequest(**values)


def test_provider_refuses_unconfigured_or_unapproved_requests():
    provider = HttpResponseProvider(endpoint="", api_token="", allowed_tenants={"tenant-lab"}, allowed_targets={"198.51.100.42"})
    assert provider.execute(_request())["enforced"] is False

    configured = HttpResponseProvider(
        endpoint="https://response-lab.invalid/actions",
        api_token="test-token",
        allowed_tenants={"tenant-lab"},
        allowed_targets={"198.51.100.42"},
    )
    refused = configured.execute(_request(approval_id=None))
    assert refused["status"] == "failure"
    assert "approval" in refused["detail"].lower()


def test_provider_reports_success_only_with_verified_evidence():
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "enforced": True,
        "verified": True,
        "provider": "test-lab-edr",
        "request_id": "REQ-001",
        "detail": "Isolated in test lab.",
    }
    requester = MagicMock(return_value=response)
    provider = HttpResponseProvider(
        endpoint="https://response-lab.invalid/actions",
        api_token="test-token",
        allowed_tenants={"tenant-lab"},
        allowed_targets={"198.51.100.42"},
        requester=requester,
    )

    result = provider.execute(_request())
    assert result["status"] == "success"
    assert result["enforced"] is True
    assert result["verified"] is True
    assert result["idempotency_key"] == "case-001:block-ip"
    assert requester.call_args.kwargs["headers"]["Idempotency-Key"] == "case-001:block-ip"


def test_provider_enforces_rbac_before_external_execution():
    provider = HttpResponseProvider(
        endpoint="https://response-lab.invalid/actions",
        api_token="test-token",
        allowed_tenants={"tenant-lab"},
        allowed_targets={"198.51.100.42"},
    )
    result = provider.execute(_request(metadata={"requester_role": "viewer"}))
    assert result["status"] == "failure"
    assert "RBAC denied" in result["detail"]


def test_provider_refuses_targets_outside_the_lab_allowlist():
    provider = HttpResponseProvider(
        endpoint="https://response-lab.invalid/actions",
        api_token="test-token",
        allowed_tenants={"tenant-lab"},
        allowed_targets={"198.51.100.42"},
    )
    result = provider.execute(_request(target="8.8.8.8"))
    assert result["status"] == "failure"
    assert result["enforced"] is False
