"""Isolated tests for governed AWS Security Group containment; no AWS calls are made."""

from __future__ import annotations

from copy import deepcopy

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend_api.shared.database import Base, ContainmentAuditRecordRow
from backend_api.soar_engine.aws_security_group_adapter import (
    AwsSecurityGroupAdapterConfig,
    AwsSecurityGroupContainmentAdapter,
)
from backend_api.soar_engine.governed_containment import GovernedContainmentService
from backend_api.soar_engine.response_adapter_router import GovernedResponseAdapterRouter
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


TENANT_ID = "00000000-0000-0000-0000-000000000001"
OTHER_TENANT_ID = "00000000-0000-0000-0000-000000000002"
REGION = "us-east-1"
ACCOUNT_ID = "123456789012"
SECURITY_GROUP_ID = "sg-0123456789abcdef0"
SECURITY_GROUP_RULE_ID = "sgr-0123456789abcdef0"
CIDR = "203.0.113.0/24"


class FakeAwsError(Exception):
    def __init__(self, code: str):
        self.response = {"Error": {"Code": code}}
        super().__init__(code)


class FakeStsClient:
    def __init__(self, account_id: str = ACCOUNT_ID, error: Exception | None = None):
        self.account_id = account_id
        self.error = error
        self.calls = 0

    def get_caller_identity(self):
        self.calls += 1
        if self.error:
            raise self.error
        return {"Account": self.account_id}


class FakeEc2Client:
    def __init__(self, rules: dict[str, dict] | None = None, revoke_error: Exception | None = None):
        self.rules = rules if rules is not None else {SECURITY_GROUP_RULE_ID: _matching_rule()}
        self.revoke_error = revoke_error
        self.revoke_calls: list[dict] = []
        self.authorize_calls: list[dict] = []

    def describe_security_group_rules(self, **kwargs):
        rule_ids = kwargs.get("SecurityGroupRuleIds")
        if rule_ids:
            rule_id = rule_ids[0]
            if rule_id not in self.rules:
                raise FakeAwsError("InvalidSecurityGroupRuleId.NotFound")
            return {"SecurityGroupRules": [deepcopy(self.rules[rule_id])]}
        return {"SecurityGroupRules": [deepcopy(rule) for rule in self.rules.values()]}

    def revoke_security_group_ingress(self, **kwargs):
        self.revoke_calls.append(kwargs)
        if self.revoke_error:
            raise self.revoke_error
        for rule_id in kwargs["SecurityGroupRuleIds"]:
            self.rules.pop(rule_id, None)
        return {"Return": True, "ResponseMetadata": {"RequestId": "revoke-request"}}

    def authorize_security_group_ingress(self, **kwargs):
        self.authorize_calls.append(kwargs)
        permission = kwargs["IpPermissions"][0]
        restored_id = "sgr-aaaaaaaaaaaaaaaaa"
        self.rules[restored_id] = {
            "SecurityGroupRuleId": restored_id,
            "GroupId": kwargs["GroupId"],
            "IsEgress": False,
            "IpProtocol": permission["IpProtocol"],
            "FromPort": permission["FromPort"],
            "ToPort": permission["ToPort"],
            "CidrIpv4": permission["IpRanges"][0]["CidrIp"],
        }
        return {"Return": True, "ResponseMetadata": {"RequestId": "authorize-request"}}


def _matching_rule(**overrides):
    rule = {
        "SecurityGroupRuleId": SECURITY_GROUP_RULE_ID,
        "GroupId": SECURITY_GROUP_ID,
        "IsEgress": False,
        "IpProtocol": "tcp",
        "FromPort": 443,
        "ToPort": 443,
        "CidrIpv4": CIDR,
    }
    rule.update(overrides)
    return rule


def _config(**overrides):
    values = {
        "enabled": True,
        "tenant_security_groups": {TENANT_ID: frozenset({SECURITY_GROUP_ID})},
        "allowed_regions": frozenset({REGION}),
        "allowed_accounts": frozenset({ACCOUNT_ID}),
        "allowed_cidrs": frozenset({CIDR}),
        "configuration_error": None,
    }
    values.update(overrides)
    return AwsSecurityGroupAdapterConfig(**values)


def _request(**overrides):
    values = {
        "tenant_id": TENANT_ID,
        "action": "block_indicator",
        "target": CIDR,
        "asset_id": SECURITY_GROUP_ID,
        "requested_by": "cloud-analyst",
        "idempotency_key": "aws-security-group-containment-0001",
        "requires_approval": True,
        "automatic_enforcement": False,
        "parameters": {
            "aws_region": REGION,
            "security_group_id": SECURITY_GROUP_ID,
            "security_group_rule_id": SECURITY_GROUP_RULE_ID,
            "cidr_ipv4": CIDR,
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "description": "approved test ingress permission",
        },
    }
    values.update(overrides)
    return ContainmentRequest(**values)


def _approval(request: ContainmentRequest):
    return ContainmentApproval(
        request_id=request.request_id,
        tenant_id=request.tenant_id,
        decision="approved",
        decided_by="cloud-approver",
        reason="Verified target, account, region, CIDR, and rule scope for controlled test.",
    )


def _adapter(ec2: FakeEc2Client | None = None, sts: FakeStsClient | None = None, **config_overrides):
    return AwsSecurityGroupContainmentAdapter(
        config=_config(**config_overrides),
        ec2_client_factory=lambda region: ec2 or FakeEc2Client(),
        sts_client_factory=lambda region: sts or FakeStsClient(),
    )


def test_aws_security_group_adapter_revokes_exact_approved_rule_verifies_absence_and_restores_it_on_rollback():
    ec2 = FakeEc2Client()
    sts = FakeStsClient()
    adapter = _adapter(ec2, sts)
    request = _request()
    approval = _approval(request)

    execution = adapter.execute(request, approval)
    assert execution["enforced"] is True
    assert execution["verified"] is True
    assert execution["rollback_available"] is True
    assert execution["provider"] == "aws-security-group"
    assert execution["aws"]["postcondition"] == "rule_absent"
    assert ec2.revoke_calls == [{"GroupId": SECURITY_GROUP_ID, "SecurityGroupRuleIds": [SECURITY_GROUP_RULE_ID]}]
    assert SECURITY_GROUP_RULE_ID not in ec2.rules

    rollback = adapter.rollback(request, approval)
    assert rollback["enforced"] is False
    assert rollback["verified"] is True
    assert rollback["aws"]["postcondition"] == "matching_rule_present"
    assert len(ec2.authorize_calls) == 1
    assert ec2.authorize_calls[0]["GroupId"] == SECURITY_GROUP_ID
    assert ec2.authorize_calls[0]["IpPermissions"][0]["IpRanges"][0]["CidrIp"] == CIDR


@pytest.mark.parametrize(
    ("request_overrides", "config_overrides", "sts", "ec2", "expected_detail"),
    [
        ({}, {"enabled": False}, FakeStsClient(), FakeEc2Client(), "disabled by default"),
        ({"tenant_id": OTHER_TENANT_ID}, {}, FakeStsClient(), FakeEc2Client(), "not allowlisted"),
        ({"target": "198.51.100.0/24"}, {}, FakeStsClient(), FakeEc2Client(), "must exactly equal"),
        ({}, {"allowed_cidrs": frozenset({"198.51.100.0/24"})}, FakeStsClient(), FakeEc2Client(), "CIDR is not allowlisted"),
        ({}, {}, FakeStsClient(account_id="999999999999"), FakeEc2Client(), "account is not allowlisted"),
        ({}, {}, FakeStsClient(), FakeEc2Client(rules={SECURITY_GROUP_RULE_ID: _matching_rule(FromPort=22, ToPort=22)}), "did not match"),
    ],
)
def test_aws_security_group_adapter_fails_closed_before_or_without_cloud_mutation(
    request_overrides, config_overrides, sts, ec2, expected_detail
):
    request = _request(**request_overrides)
    result = _adapter(ec2, sts, **config_overrides).execute(request, _approval(request))

    assert result["enforced"] is False
    assert result["verified"] is False
    assert result["rollback_available"] is False
    assert expected_detail in result["detail"]
    assert ec2.revoke_calls == []


def test_aws_security_group_adapter_treats_cloud_exception_or_missing_readback_as_unverified_failure():
    request = _request()
    exception_adapter = _adapter(FakeEc2Client(revoke_error=FakeAwsError("UnauthorizedOperation")), FakeStsClient())
    exception_result = exception_adapter.execute(request, _approval(request))
    assert exception_result["enforced"] is False
    assert exception_result["verified"] is False
    assert "UnauthorizedOperation" in exception_result["detail"]

    missing_rule_adapter = _adapter(FakeEc2Client(rules={}), FakeStsClient())
    missing_rule_result = missing_rule_adapter.execute(request, _approval(request))
    assert missing_rule_result["enforced"] is False
    assert missing_rule_result["verified"] is False
    assert "precondition" in missing_rule_result["detail"]


@pytest.mark.asyncio
async def test_governed_service_routes_approved_cloud_block_through_signed_audit_lifecycle_and_preserves_provider_evidence():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    ec2 = FakeEc2Client()
    aws_adapter = _adapter(ec2, FakeStsClient())
    service = GovernedContainmentService(
        session_factory=sessions,
        adapter=GovernedResponseAdapterRouter(aws_security_group_adapter=aws_adapter),
        audit_signing_key="test-aws-containment-hmac",
        audit_key_id="test-aws-key",
    )
    try:
        request, created = await service.request(_request())
        approval = await service.approve(_approval(request))
        execution = await service.execute(TENANT_ID, request.request_id, approval.decided_by)
        rollback = await service.rollback(TENANT_ID, request.request_id, approval.decided_by)

        assert created is True
        assert execution.adapter == "aws-security-group"
        assert execution.status == "verified"
        assert execution.verification["aws"]["security_group_id"] == SECURITY_GROUP_ID
        assert rollback.status == "rolled_back"
        assert rollback.verification["rollback"]["provider"] == "aws-security-group"
        async with sessions() as session:
            audit_rows = list(await session.scalars(select(ContainmentAuditRecordRow).order_by(ContainmentAuditRecordRow.id)))
        assert [row.action for row in audit_rows] == [
            "containment.requested",
            "containment.approved",
            "containment.executed",
            "containment.rolled_back",
        ]
        assert audit_rows[2].payload["adapter"] == "aws-security-group"
        assert all(row.signature and row.signature_key_id == "test-aws-key" for row in audit_rows)
    finally:
        await engine.dispose()


class StubbornRevokeEc2Client(FakeEc2Client):
    def revoke_security_group_ingress(self, **kwargs):
        self.revoke_calls.append(kwargs)
        return {"Return": True, "ResponseMetadata": {"RequestId": "stubborn-revoke"}}


class NoRestoreEc2Client(FakeEc2Client):
    def authorize_security_group_ingress(self, **kwargs):
        self.authorize_calls.append(kwargs)
        return {"Return": True, "ResponseMetadata": {"RequestId": "no-restore"}}


class EndlessPageEc2Client(FakeEc2Client):
    def describe_security_group_rules(self, **kwargs):
        if kwargs.get("SecurityGroupRuleIds"):
            return super().describe_security_group_rules(**kwargs)
        return {"SecurityGroupRules": [], "NextToken": "still-more"}


def test_aws_config_loader_accepts_explicit_valid_allowlists_and_disables_invalid_mapping(monkeypatch):
    monkeypatch.setenv("PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED", "true")
    monkeypatch.setenv("PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST", f'{{"{TENANT_ID}":["{SECURITY_GROUP_ID}"]}}')
    monkeypatch.setenv("PHANTOMNET_AWS_ALLOWED_REGIONS", REGION)
    monkeypatch.setenv("PHANTOMNET_AWS_ALLOWED_ACCOUNT_IDS", ACCOUNT_ID)
    monkeypatch.setenv("PHANTOMNET_AWS_ALLOWED_CIDRS", "203.0.113.42/24")

    config = AwsSecurityGroupAdapterConfig.from_environment()
    assert config.enabled is True
    assert config.tenant_security_groups[TENANT_ID] == frozenset({SECURITY_GROUP_ID})
    assert config.allowed_cidrs == frozenset({CIDR})
    assert config.configuration_error is None

    monkeypatch.setenv("PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST", "[]")
    invalid = AwsSecurityGroupAdapterConfig.from_environment()
    assert invalid.enabled is False
    assert invalid.configuration_error and "JSON object" in invalid.configuration_error


@pytest.mark.parametrize(
    "parameters",
    [
        {**_request().parameters, "cidr_ipv4": "2001:db8::/64"},
        {**_request().parameters, "from_port": 444, "to_port": 443},
        {**_request().parameters, "protocol": "-1"},
    ],
)
def test_aws_security_group_adapter_rejects_invalid_or_overbroad_parameter_contract_before_mutation(parameters):
    ec2 = FakeEc2Client()
    request = _request(parameters=parameters)
    result = _adapter(ec2, FakeStsClient()).execute(request, _approval(request))

    assert result["enforced"] is False
    assert result["verified"] is False
    assert "Invalid AWS Security Group containment parameters" in result["detail"]
    assert ec2.revoke_calls == []


def test_aws_security_group_adapter_rejects_wrong_action_and_rejected_approval_before_mutation():
    ec2 = FakeEc2Client()
    action_request = _request(action="isolate_endpoint")
    rejected_action = _adapter(ec2, FakeStsClient()).execute(action_request, _approval(action_request))
    assert rejected_action["enforced"] is False
    assert "Unsupported" in rejected_action["detail"]

    request = _request()
    rejected_approval = _approval(request).model_copy(update={"decision": "rejected"})
    rejected = _adapter(ec2, FakeStsClient()).execute(request, rejected_approval)
    assert rejected["enforced"] is False
    assert "explicitly approved" in rejected["detail"]
    assert ec2.revoke_calls == []


def test_aws_security_group_adapter_fails_closed_when_caller_identity_cannot_be_verified_or_revoke_readback_is_still_present():
    request = _request()
    identity_failure = _adapter(FakeEc2Client(), FakeStsClient(error=FakeAwsError("AccessDenied"))).execute(request, _approval(request))
    assert identity_failure["enforced"] is False
    assert identity_failure["verified"] is False
    assert "caller identity verification failed" in identity_failure["detail"]

    stubborn_ec2 = StubbornRevokeEc2Client()
    stubborn = _adapter(stubborn_ec2, FakeStsClient()).execute(request, _approval(request))
    assert stubborn["enforced"] is False
    assert stubborn["verified"] is False
    assert "still present" in stubborn["detail"]
    assert len(stubborn_ec2.revoke_calls) == 1


def test_aws_security_group_rollback_refuses_duplicate_permission_and_unverified_restoration():
    request = _request()
    approval = _approval(request)
    duplicate_ec2 = FakeEc2Client()
    duplicate = _adapter(duplicate_ec2, FakeStsClient()).rollback(request, approval)
    assert duplicate["verified"] is False
    assert "already present" in duplicate["detail"]
    assert duplicate_ec2.authorize_calls == []

    no_restore_ec2 = NoRestoreEc2Client()
    adapter = _adapter(no_restore_ec2, FakeStsClient())
    assert adapter.execute(request, approval)["verified"] is True
    no_restore = adapter.rollback(request, approval)
    assert no_restore["verified"] is False
    assert "could not verify" in no_restore["detail"]
    assert len(no_restore_ec2.authorize_calls) == 1


def test_aws_security_group_rule_lookup_has_a_hard_pagination_bound_and_falls_back_to_exception_class_name():
    adapter = _adapter(EndlessPageEc2Client(), FakeStsClient())
    with pytest.raises(RuntimeError, match="pagination safety bound"):
        adapter._find_matching_rule(EndlessPageEc2Client(), _request().parameters and adapter._parse_and_authorize(_request(), _approval(_request()))[0])

    class OpaqueCloudError(Exception):
        pass

    failure = _adapter(FakeEc2Client(revoke_error=OpaqueCloudError()), FakeStsClient()).execute(_request(), _approval(_request()))
    assert failure["enforced"] is False
    assert "OpaqueCloudError" in failure["detail"]
