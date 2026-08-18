"""Fail-closed AWS Security Group containment adapter.

AWS security groups are allow-list firewalls and do not support deny rules. Therefore this adapter
implements ``block_indicator`` only by revoking one explicitly identified, allowlisted ingress
rule. It verifies the exact precondition and postcondition through AWS reads, and rollback adds
back the same reviewed permission. It never discovers a target, selects a security group, or
executes without explicit allowlists and a human-approved governed request.
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from phantomnet_core.contracts import ContainmentApproval, ContainmentRequest


_SECURITY_GROUP_PATTERN = r"^sg-[0-9a-f]{8,17}$"
_SECURITY_GROUP_RULE_PATTERN = r"^sgr-[0-9a-f]{8,17}$"
_REGION_PATTERN = r"^[a-z]{2}-[a-z]+-\d+$"
_ACCOUNT_PATTERN = r"^\d{12}$"


class AwsSecurityGroupBlockSpec(BaseModel):
    """Exact ingress permission that may be revoked after approval; no wildcard protocol is accepted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    aws_region: str = Field(pattern=_REGION_PATTERN)
    security_group_id: str = Field(pattern=_SECURITY_GROUP_PATTERN)
    security_group_rule_id: str = Field(pattern=_SECURITY_GROUP_RULE_PATTERN)
    cidr_ipv4: str
    protocol: Literal["tcp", "udp"]
    from_port: int = Field(ge=1, le=65535)
    to_port: int = Field(ge=1, le=65535)
    description: str | None = Field(default=None, max_length=255)

    @field_validator("cidr_ipv4")
    @classmethod
    def canonical_ipv4_cidr(cls, value: str) -> str:
        network = ipaddress.ip_network(value, strict=False)
        if network.version != 4:
            raise ValueError("Only IPv4 CIDRs are supported by the AWS Security Group adapter.")
        return str(network)

    @model_validator(mode="after")
    def validate_port_range(self) -> "AwsSecurityGroupBlockSpec":
        if self.from_port > self.to_port:
            raise ValueError("from_port cannot be greater than to_port.")
        return self

    def ip_permission(self) -> dict[str, Any]:
        ip_range: dict[str, str] = {"CidrIp": self.cidr_ipv4}
        if self.description:
            ip_range["Description"] = self.description
        return {
            "IpProtocol": self.protocol,
            "FromPort": self.from_port,
            "ToPort": self.to_port,
            "IpRanges": [ip_range],
        }


@dataclass(frozen=True)
class AwsSecurityGroupAdapterConfig:
    enabled: bool
    tenant_security_groups: dict[str, frozenset[str]]
    allowed_regions: frozenset[str]
    allowed_accounts: frozenset[str]
    allowed_cidrs: frozenset[str]
    configuration_error: str | None = None

    @classmethod
    def from_environment(cls) -> "AwsSecurityGroupAdapterConfig":
        try:
            raw_mapping = json.loads(os.getenv("PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST", "{}"))
            if not isinstance(raw_mapping, dict):
                raise ValueError("PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST must be a JSON object.")
            mapping: dict[str, frozenset[str]] = {}
            for tenant_id, group_ids in raw_mapping.items():
                if not isinstance(tenant_id, str) or not isinstance(group_ids, list) or not all(isinstance(item, str) for item in group_ids):
                    raise ValueError("AWS tenant security-group allowlist entries must map a tenant string to an array of group IDs.")
                mapping[tenant_id] = frozenset(group_ids)
            return cls(
                enabled=os.getenv("PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED", "false").strip().lower() == "true",
                tenant_security_groups=mapping,
                allowed_regions=frozenset(_csv_environment("PHANTOMNET_AWS_ALLOWED_REGIONS")),
                allowed_accounts=frozenset(_csv_environment("PHANTOMNET_AWS_ALLOWED_ACCOUNT_IDS")),
                allowed_cidrs=frozenset(_canonical_cidrs(_csv_environment("PHANTOMNET_AWS_ALLOWED_CIDRS"))),
            )
        except (ValueError, json.JSONDecodeError) as exc:
            return cls(
                enabled=False,
                tenant_security_groups={},
                allowed_regions=frozenset(),
                allowed_accounts=frozenset(),
                allowed_cidrs=frozenset(),
                configuration_error=f"Invalid AWS Security Group containment configuration: {exc}",
            )


def _csv_environment(name: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


def _canonical_cidrs(values: list[str]) -> list[str]:
    return [str(ipaddress.ip_network(value, strict=False)) for value in values]


def _boto3_ec2_client(region: str):
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - exercised only in misconfigured deployments
        raise RuntimeError("AWS Security Group containment requires the boto3 package.") from exc
    return boto3.client("ec2", region_name=region)


def _boto3_sts_client(region: str):
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - exercised only in misconfigured deployments
        raise RuntimeError("AWS Security Group containment requires the boto3 package.") from exc
    return boto3.client("sts", region_name=region)


class AwsSecurityGroupContainmentAdapter:
    """Revoke one reviewed AWS ingress rule and prove both execution and rollback by read-back."""

    name = "aws-security-group"

    def __init__(
        self,
        *,
        config: AwsSecurityGroupAdapterConfig | None = None,
        ec2_client_factory: Callable[[str], Any] | None = None,
        sts_client_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self._config = config or AwsSecurityGroupAdapterConfig.from_environment()
        self._ec2_client_factory = ec2_client_factory or _boto3_ec2_client
        self._sts_client_factory = sts_client_factory or _boto3_sts_client

    def _reject(self, detail: str, *, spec: AwsSecurityGroupBlockSpec | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "enforced": False,
            "verified": False,
            "rollback_available": False,
            "detail": detail,
            "provider": self.name,
        }
        if spec is not None:
            result["aws"] = self._public_spec(spec)
        return result

    def _public_spec(self, spec: AwsSecurityGroupBlockSpec) -> dict[str, Any]:
        return {
            "region": spec.aws_region,
            "security_group_id": spec.security_group_id,
            "security_group_rule_id": spec.security_group_rule_id,
            "cidr_ipv4": spec.cidr_ipv4,
            "protocol": spec.protocol,
            "from_port": spec.from_port,
            "to_port": spec.to_port,
        }

    def _parse_and_authorize(self, request: ContainmentRequest, approval: ContainmentApproval) -> tuple[AwsSecurityGroupBlockSpec | None, str | None]:
        if not self._config.enabled:
            return None, "AWS Security Group containment adapter is disabled by default."
        if self._config.configuration_error:
            return None, self._config.configuration_error
        if request.action != "block_indicator":
            return None, f"Unsupported AWS Security Group containment action: {request.action}."
        if not request.requires_approval or request.automatic_enforcement or approval.decision != "approved":
            return None, "AWS Security Group containment requires an explicitly approved, non-automatic request."
        try:
            spec = AwsSecurityGroupBlockSpec.model_validate(request.parameters)
        except ValidationError as exc:
            return None, f"Invalid AWS Security Group containment parameters: {exc.errors()[0]['msg']}"
        if request.target != spec.cidr_ipv4:
            return None, "Containment target must exactly equal the canonical allowlisted CIDR in request parameters."
        if request.asset_id != spec.security_group_id:
            return None, "Containment asset_id must exactly equal the requested AWS Security Group ID."
        allowed_groups = self._config.tenant_security_groups.get(request.tenant_id, frozenset())
        if spec.security_group_id not in allowed_groups:
            return None, "Tenant is not allowlisted for the requested AWS Security Group."
        if spec.aws_region not in self._config.allowed_regions:
            return None, "AWS region is not allowlisted for cloud containment."
        if spec.cidr_ipv4 not in self._config.allowed_cidrs:
            return None, "CIDR is not allowlisted for cloud containment."
        return spec, None

    def _verify_account(self, sts_client: Any) -> tuple[str | None, str | None]:
        try:
            identity = sts_client.get_caller_identity()
        except Exception as exc:
            return None, f"AWS caller identity verification failed: {_aws_error_code(exc)}"
        account_id = str(identity.get("Account", ""))
        if not re.fullmatch(_ACCOUNT_PATTERN, account_id) or account_id not in self._config.allowed_accounts:
            return None, "AWS caller account is not allowlisted for cloud containment."
        return account_id, None

    def execute(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        spec, denial = self._parse_and_authorize(request, approval)
        if denial:
            return self._reject(denial, spec=spec)
        assert spec is not None
        try:
            ec2_client = self._ec2_client_factory(spec.aws_region)
            sts_client = self._sts_client_factory(spec.aws_region)
            account_id, denial = self._verify_account(sts_client)
            if denial:
                return self._reject(denial, spec=spec)
            before = self._describe_rule(ec2_client, spec.security_group_rule_id)
            if not before or not self._matches_spec(before, spec):
                return self._reject("AWS Security Group rule did not match the approved group, source, protocol, and port precondition.", spec=spec)
            ec2_client.revoke_security_group_ingress(
                GroupId=spec.security_group_id,
                SecurityGroupRuleIds=[spec.security_group_rule_id],
            )
            after = self._describe_rule(ec2_client, spec.security_group_rule_id)
            if after:
                return self._reject("AWS revoke call returned but read-back shows the ingress rule is still present.", spec=spec)
            return {
                "enforced": True,
                "verified": True,
                "rollback_available": True,
                "detail": "Approved AWS Security Group ingress rule was revoked and absence was verified by read-back.",
                "provider": self.name,
                "aws": {**self._public_spec(spec), "account_id": account_id, "operation": "revoke_security_group_ingress", "postcondition": "rule_absent"},
            }
        except Exception as exc:
            return self._reject(f"AWS ingress revocation failed without verified enforcement: {_aws_error_code(exc)}", spec=spec)

    def rollback(self, request: ContainmentRequest, approval: ContainmentApproval) -> dict[str, Any]:
        spec, denial = self._parse_and_authorize(request, approval)
        if denial:
            return self._reject(denial, spec=spec)
        assert spec is not None
        try:
            ec2_client = self._ec2_client_factory(spec.aws_region)
            sts_client = self._sts_client_factory(spec.aws_region)
            account_id, denial = self._verify_account(sts_client)
            if denial:
                return self._reject(denial, spec=spec)
            if self._find_matching_rule(ec2_client, spec) is not None:
                return self._reject("AWS ingress rule is already present; rollback refuses to create a duplicate permission.", spec=spec)
            response = ec2_client.authorize_security_group_ingress(
                GroupId=spec.security_group_id,
                IpPermissions=[spec.ip_permission()],
                TagSpecifications=[
                    {
                        "ResourceType": "security-group-rule",
                        "Tags": [
                            {"Key": "ManagedBy", "Value": "PhantomNet"},
                            {"Key": "ContainmentRequestId", "Value": request.request_id},
                            {"Key": "ContainmentApprovalId", "Value": approval.approval_id},
                        ],
                    }
                ],
            )
            restored = self._find_matching_rule(ec2_client, spec)
            if restored is None:
                return self._reject("AWS authorization returned but read-back could not verify the restored ingress rule.", spec=spec)
            return {
                "enforced": False,
                "verified": True,
                "rollback_available": False,
                "detail": "AWS Security Group ingress permission was restored and presence was verified by read-back.",
                "provider": self.name,
                "aws": {
                    **self._public_spec(spec),
                    "account_id": account_id,
                    "operation": "authorize_security_group_ingress",
                    "restored_security_group_rule_id": restored.get("SecurityGroupRuleId"),
                    "request_id": response.get("ResponseMetadata", {}).get("RequestId"),
                    "postcondition": "matching_rule_present",
                },
            }
        except Exception as exc:
            return self._reject(f"AWS ingress rollback failed without verified restoration: {_aws_error_code(exc)}", spec=spec)

    @staticmethod
    def _describe_rule(ec2_client: Any, rule_id: str) -> dict[str, Any] | None:
        try:
            response = ec2_client.describe_security_group_rules(SecurityGroupRuleIds=[rule_id])
        except Exception as exc:
            if _is_not_found(exc):
                return None
            raise
        rules = response.get("SecurityGroupRules", [])
        return dict(rules[0]) if rules else None

    @staticmethod
    def _matches_spec(rule: Mapping[str, Any], spec: AwsSecurityGroupBlockSpec) -> bool:
        return (
            rule.get("GroupId") == spec.security_group_id
            and rule.get("IsEgress") is False
            and rule.get("IpProtocol") == spec.protocol
            and rule.get("FromPort") == spec.from_port
            and rule.get("ToPort") == spec.to_port
            and rule.get("CidrIpv4") == spec.cidr_ipv4
        )

    def _find_matching_rule(self, ec2_client: Any, spec: AwsSecurityGroupBlockSpec) -> dict[str, Any] | None:
        next_token: str | None = None
        pages = 0
        while pages < 10:
            request: dict[str, Any] = {
                "Filters": [{"Name": "group-id", "Values": [spec.security_group_id]}],
                "MaxResults": 1000,
            }
            if next_token:
                request["NextToken"] = next_token
            response = ec2_client.describe_security_group_rules(**request)
            for rule in response.get("SecurityGroupRules", []):
                if self._matches_spec(rule, spec):
                    return dict(rule)
            next_token = response.get("NextToken")
            if not next_token:
                return None
            pages += 1
        raise RuntimeError("AWS Security Group rule verification exceeded the configured pagination safety bound.")


def _aws_error_code(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if isinstance(response, Mapping):
        error = response.get("Error")
        if isinstance(error, Mapping) and error.get("Code"):
            return str(error["Code"])
    return type(exc).__name__


def _is_not_found(exc: Exception) -> bool:
    return _aws_error_code(exc) in {"InvalidSecurityGroupRuleId.NotFound", "InvalidPermission.NotFound"}
