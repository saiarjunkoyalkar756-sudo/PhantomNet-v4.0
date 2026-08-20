from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.shared.database import Base
from backend_api.shared.runtime_posture import assess_runtime_posture
from backend_api.soar_engine.aws_security_group_adapter import (
    AwsSecurityGroupAdapterConfig,
    AwsSecurityGroupContainmentAdapter,
)
from backend_api.soar_engine.endpoint_containment_adapter import EndpointContainmentAdapter
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.wazuh_active_response_adapter import (
    WazuhActiveResponseConfig,
    WazuhActiveResponseContainmentAdapter,
)
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _endpoint_request() -> ContainmentRequest:
    return ContainmentRequest(
        tenant_id=TENANT_ID,
        action="isolate_endpoint",
        target="endpoint-preflight-001",
        asset_id="endpoint-preflight-001",
        requested_by="analyst-preflight",
        idempotency_key="phase6-endpoint-preflight-001",
        parameters={"reason": "reviewed evidence"},
        requires_approval=True,
        automatic_enforcement=False,
    )


def _aws_request() -> ContainmentRequest:
    return ContainmentRequest(
        tenant_id=TENANT_ID,
        action="block_indicator",
        target="198.51.100.0/24",
        asset_id="sg-0123456789abcdef0",
        requested_by="analyst-preflight",
        idempotency_key="phase6-aws-preflight-00001",
        parameters={
            "aws_region": "us-east-1",
            "security_group_id": "sg-0123456789abcdef0",
            "security_group_rule_id": "sgr-0123456789abcdef0",
            "cidr_ipv4": "198.51.100.0/24",
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
        },
        requires_approval=True,
        automatic_enforcement=False,
    )


def _wazuh_request() -> ContainmentRequest:
    return ContainmentRequest(
        tenant_id=TENANT_ID,
        action="isolate_endpoint",
        target="007",
        asset_id="007",
        requested_by="analyst-preflight",
        idempotency_key="phase6-wazuh-preflight-001",
        parameters={
            "wazuh_agent_id": "007",
            "response_profile": "lab-network-isolation-v1",
            "management_cidr": "192.0.2.0/24",
        },
        requires_approval=True,
        automatic_enforcement=False,
    )


def test_adapter_preflights_are_configuration_only_and_make_no_external_calls():
    endpoint_calls: list[dict] = []
    endpoint = EndpointContainmentAdapter(
        enabled=True,
        allowed_tenants={TENANT_ID},
        allowed_assets={"endpoint-preflight-001"},
        dispatcher=lambda command: endpoint_calls.append(command) or {"enforced": True, "verified": True},
    )
    endpoint_result = endpoint.preflight(_endpoint_request())
    assert endpoint_result["eligible"] is True
    assert endpoint_result["rollback_available"] is True
    assert endpoint_result["external_calls"] is False
    assert endpoint_calls == []

    aws_factory_calls: list[str] = []
    aws = AwsSecurityGroupContainmentAdapter(
        config=AwsSecurityGroupAdapterConfig(
            enabled=True,
            tenant_security_groups={TENANT_ID: frozenset({"sg-0123456789abcdef0"})},
            allowed_regions=frozenset({"us-east-1"}),
            allowed_accounts=frozenset({"123456789012"}),
            allowed_cidrs=frozenset({"198.51.100.0/24"}),
        ),
        ec2_client_factory=lambda region: aws_factory_calls.append(f"ec2:{region}"),
        sts_client_factory=lambda region: aws_factory_calls.append(f"sts:{region}"),
    )
    aws_result = aws.preflight(_aws_request())
    assert aws_result["eligible"] is True
    assert aws_result["verification_mode"] == "aws_readback_required"
    assert aws_factory_calls == []

    wazuh_dispatches: list[dict] = []
    wazuh = WazuhActiveResponseContainmentAdapter(
        config=WazuhActiveResponseConfig(
            enabled=True,
            api_base_url="https://wazuh.preflight.test:55000",
            username="phase6-service",
            password="phase6-password",
            command_hmac_key="phase6-command-key",
            command_hmac_key_id="phase6-key-id",
            tenant_agent_allowlist={TENANT_ID: frozenset({"007"})},
            allowed_profiles=frozenset({"lab-network-isolation-v1"}),
        ),
        client=type("NoDispatch", (), {"dispatch": lambda self, **kwargs: wazuh_dispatches.append(kwargs)})(),
    )
    wazuh_result = wazuh.preflight(_wazuh_request())
    assert wazuh_result["eligible"] is True
    assert wazuh_result["verification_mode"] == "fresh_signed_endpoint_receipt_required"
    assert wazuh_result["external_calls"] is False
    assert wazuh_dispatches == []


class PreflightVerifiedAdapter:
    name = "phase6-preflight-verified"

    def __init__(self) -> None:
        self.execute_calls = 0
        self.rollback_calls = 0

    def preflight(self, request):
        return {
            "eligible": True,
            "provider": self.name,
            "detail": "Exact local scope is ready.",
            "rollback_available": request.action == "isolate_endpoint",
            "verification_mode": "signed_test_receipt_required",
            "external_calls": False,
            "automatic_enforcement": False,
        }

    def execute(self, request, approval):
        self.execute_calls += 1
        return {"enforced": True, "verified": True, "rollback_available": True, "detail": "Verified containment."}

    def rollback(self, request, approval):
        self.rollback_calls += 1
        return {"enforced": False, "verified": True, "detail": "Verified release."}


@pytest.mark.asyncio
async def test_governed_preflight_requires_signed_audit_and_approval_then_reports_rollback_readiness_without_dispatch():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    adapter = PreflightVerifiedAdapter()
    service = GovernedContainmentService(
        session_factory=sessions,
        adapter=adapter,
        audit_signing_key="phase6-audit-key",
        audit_key_id="phase6-audit-key-id",
    )
    try:
        request, created = await service.request(_endpoint_request())
        pending = await service.preflight(TENANT_ID, request.request_id)
        assert created is True
        assert pending["eligible_to_execute"] is False
        assert pending["approval_status"] == "pending"
        assert pending["execution_blockers"] == ["request_not_approved"]
        assert pending["external_calls"] is False
        assert adapter.execute_calls == 0

        await service.approve(
            ContainmentApproval(
                request_id=request.request_id,
                tenant_id=TENANT_ID,
                decision="approved",
                decided_by="phase6-approver",
                reason="Reviewed target, scope, and rollback plan.",
            )
        )
        ready = await service.preflight(TENANT_ID, request.request_id)
        assert ready["eligible_to_execute"] is True
        assert ready["adapter"]["eligible"] is True
        assert ready["adapter"]["rollback_available"] is True
        assert adapter.execute_calls == 0

        await service.execute(TENANT_ID, request.request_id, "phase6-approver")
        rollback_ready = await service.preflight(TENANT_ID, request.request_id)
        assert rollback_ready["eligible_to_execute"] is False
        assert rollback_ready["rollback_ready"] is True
        assert "execution_already_recorded" in rollback_ready["execution_blockers"]
        assert adapter.rollback_calls == 0

        await service.rollback(TENANT_ID, request.request_id, "phase6-approver")
        rolled_back = await service.preflight(TENANT_ID, request.request_id)
        assert rolled_back["rollback_ready"] is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_unsigned_service_refuses_high_impact_request_before_persistence():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    service = GovernedContainmentService(session_factory=sessions, adapter=PreflightVerifiedAdapter())
    try:
        with pytest.raises(PermissionError, match="HMAC-signed"):
            await service.request(_endpoint_request())
    finally:
        await engine.dispose()


def test_runtime_posture_reports_wazuh_readiness_without_exposing_secret_values():
    environment = {
        "ENVIRONMENT": "production",
        "PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY": "audit-key",
        "PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID": "audit-key-id",
        "PHANTOMNET_WAZUH_RESPONSE_ENABLED": "true",
        "PHANTOMNET_WAZUH_RESPONSE_API_BASE_URL": "https://wazuh.production.test:55000",
        "PHANTOMNET_WAZUH_RESPONSE_API_USERNAME": "operator",
        "PHANTOMNET_WAZUH_RESPONSE_API_PASSWORD": "never-returned",
        "PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY": "never-returned",
        "PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY_ID": "command-key-id",
        "PHANTOMNET_WAZUH_RESPONSE_TENANT_AGENT_ALLOWLIST": '{"00000000-0000-0000-0000-000000000001":["007"]}',
        "PHANTOMNET_WAZUH_RESPONSE_ALLOWED_PROFILES": "lab-network-isolation-v1",
    }
    posture = assess_runtime_posture(safe_mode=False, environment=environment)
    control = posture["controls"]["wazuh_active_response"]
    assert control == {
        "status": "ready",
        "reason": "https_command_transport_configured",
        "allowed_tenant_count": 1,
        "allowed_profile_count": 1,
        "transport": "https",
    }
    assert "never-returned" not in str(posture)


def test_preflight_route_is_authenticated_read_only_and_excludes_dispatch():
    from backend_api.soar_engine.governed_api import router

    paths = {route.path for route in router.routes}
    assert "/governed-containment/requests/{request_id}/preflight" in paths
    assert not any("execute" in route.path or "rollback" in route.path for route in router.routes if route.path.endswith("/preflight"))
