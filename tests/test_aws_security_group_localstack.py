"""Docker-gated LocalStack integration coverage for the AWS Security Group containment adapter.

Run with:
  docker compose -f docker-compose.localstack.yml up -d
  PHANTOMNET_LOCALSTACK_ENDPOINT_URL=http://127.0.0.1:4566 \
  AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_EC2_METADATA_DISABLED=true \
  python3 -m pytest tests/test_aws_security_group_localstack.py -m localstack -vv
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

from backend_api.soar_engine.aws_security_group_adapter import (
    AwsSecurityGroupAdapterConfig,
    AwsSecurityGroupContainmentAdapter,
)
from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


pytestmark = pytest.mark.localstack

TENANT_ID = "00000000-0000-0000-0000-000000000001"
REGION = "us-east-1"
CIDR = "203.0.113.0/24"


def _endpoint_or_skip() -> str:
    endpoint_url = os.getenv("PHANTOMNET_LOCALSTACK_ENDPOINT_URL", "").strip()
    if not endpoint_url:
        pytest.skip(
            "LocalStack is opt-in: set PHANTOMNET_LOCALSTACK_ENDPOINT_URL after starting "
            "docker compose -f docker-compose.localstack.yml up -d."
        )
    return endpoint_url.rstrip("/")


def _boto3(endpoint_url: str):
    return pytest.importorskip("boto3", reason="LocalStack integration requires boto3 declared in backend_api/requirements.txt").client


def _find_rule_id(ec2_client, security_group_id: str) -> str:
    response = ec2_client.describe_security_group_rules(
        Filters=[{"Name": "group-id", "Values": [security_group_id]}],
        MaxResults=1000,
    )
    for rule in response.get("SecurityGroupRules", []):
        if (
            rule.get("GroupId") == security_group_id
            and rule.get("IsEgress") is False
            and rule.get("IpProtocol") == "tcp"
            and rule.get("FromPort") == 443
            and rule.get("ToPort") == 443
            and rule.get("CidrIpv4") == CIDR
        ):
            return rule["SecurityGroupRuleId"]
    raise AssertionError("LocalStack did not create the expected ingress rule.")


def _delete_security_group(ec2_client, security_group_id: str) -> None:
    rules = ec2_client.describe_security_group_rules(
        Filters=[{"Name": "group-id", "Values": [security_group_id]}],
        MaxResults=1000,
    ).get("SecurityGroupRules", [])
    ingress_rule_ids = [rule["SecurityGroupRuleId"] for rule in rules if rule.get("IsEgress") is False]
    if ingress_rule_ids:
        ec2_client.revoke_security_group_ingress(
            GroupId=security_group_id,
            SecurityGroupRuleIds=ingress_rule_ids,
        )
    ec2_client.delete_security_group(GroupId=security_group_id)


def test_localstack_boto3_adapter_revokes_and_restores_exact_security_group_ingress_rule(monkeypatch):
    endpoint_url = _endpoint_or_skip()
    boto3_client = _boto3(endpoint_url)
    monkeypatch.setenv("PHANTOMNET_AWS_ENDPOINT_URL", endpoint_url)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", "test"))
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", "test"))
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")

    ec2 = boto3_client("ec2", region_name=REGION, endpoint_url=endpoint_url)
    sts = boto3_client("sts", region_name=REGION, endpoint_url=endpoint_url)
    account_id = str(sts.get_caller_identity()["Account"])
    group = ec2.create_security_group(
        GroupName=f"phantomnet-localstack-{uuid4().hex[:12]}",
        Description="Ephemeral PhantomNet LocalStack containment integration test",
    )
    security_group_id = group["GroupId"]
    try:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 443,
                    "ToPort": 443,
                    "IpRanges": [{"CidrIp": CIDR, "Description": "LocalStack containment test"}],
                }
            ],
        )
        security_group_rule_id = _find_rule_id(ec2, security_group_id)
        config = AwsSecurityGroupAdapterConfig(
            enabled=True,
            tenant_security_groups={TENANT_ID: frozenset({security_group_id})},
            allowed_regions=frozenset({REGION}),
            allowed_accounts=frozenset({account_id}),
            allowed_cidrs=frozenset({CIDR}),
        )
        request = ContainmentRequest(
            tenant_id=TENANT_ID,
            action="block_indicator",
            target=CIDR,
            asset_id=security_group_id,
            requested_by="localstack-analyst",
            idempotency_key=f"localstack-security-group-{uuid4().hex}",
            parameters={
                "aws_region": REGION,
                "security_group_id": security_group_id,
                "security_group_rule_id": security_group_rule_id,
                "cidr_ipv4": CIDR,
                "protocol": "tcp",
                "from_port": 443,
                "to_port": 443,
                "description": "LocalStack containment test",
            },
        )
        approval = ContainmentApproval(
            request_id=request.request_id,
            tenant_id=TENANT_ID,
            decision="approved",
            decided_by="localstack-approver",
            reason="Approved isolated LocalStack containment validation.",
        )
        adapter = AwsSecurityGroupContainmentAdapter(config=config)

        execution = adapter.execute(request, approval)
        assert execution["enforced"] is True
        assert execution["verified"] is True
        assert execution["aws"]["operation"] == "revoke_security_group_ingress"
        assert execution["aws"]["postcondition"] == "rule_absent"
        remaining_rule_ids = {
            rule["SecurityGroupRuleId"]
            for rule in ec2.describe_security_group_rules(
                Filters=[{"Name": "group-id", "Values": [security_group_id]}],
                MaxResults=1000,
            ).get("SecurityGroupRules", [])
        }
        assert security_group_rule_id not in remaining_rule_ids

        rollback = adapter.rollback(request, approval)
        assert rollback["verified"] is True
        assert rollback["aws"]["operation"] == "authorize_security_group_ingress"
        assert rollback["aws"]["postcondition"] == "matching_rule_present"
        assert _find_rule_id(ec2, security_group_id)
    finally:
        _delete_security_group(ec2, security_group_id)
