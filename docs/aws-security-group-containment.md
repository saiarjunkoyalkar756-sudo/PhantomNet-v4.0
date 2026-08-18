# Governed AWS Security Group Containment

## Scope and safety model

PhantomNet’s AWS Security Group adapter is a **fail-closed, human-governed response boundary**. It supports only the canonical `block_indicator` containment action and only by revoking one explicitly named inbound Security Group rule. AWS Security Groups are allow-list firewalls rather than deny-list controls; therefore the adapter does not invent, infer, or add a “block” rule. It removes a reviewed ingress permission whose group, rule ID, source CIDR, protocol, and port range have all been supplied in the approved request.

> A graph result, threat-intelligence finding, BAS scenario, or enrichment result never invokes this adapter. A request must be created, approved by a human, HMAC-audited, executed, verified by AWS read-back, and stored as containment evidence.

The implementation follows AWS’s documented semantics: ingress authorization and revocation operate on Security Group permissions; revocation can use a Security Group rule ID; AWS recommends describing Security Group rules to verify removal; and rule changes may have a short propagation delay. [1] [2] [3]

## Mandatory approval and allowlists

The existing governed containment lifecycle rejects automatic execution and fails closed when the HMAC audit signing key or key ID is unavailable. The AWS adapter adds a second set of controls before it creates an SDK client or performs any cloud mutation.

| Control | Required condition |
|---|---|
| Adapter enablement | `PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED=true` |
| Tenant scope | Request tenant maps to the requested Security Group in `PHANTOMNET_AWS_TENANT_SECURITY_GROUP_ALLOWLIST` |
| Region | Requested AWS region is in `PHANTOMNET_AWS_ALLOWED_REGIONS` |
| Account | `sts:GetCallerIdentity` returns an account in `PHANTOMNET_AWS_ALLOWED_ACCOUNT_IDS` |
| CIDR | Request target and canonical CIDR are exactly equal and included in `PHANTOMNET_AWS_ALLOWED_CIDRS` |
| Rule precondition | `DescribeSecurityGroupRules` proves the supplied rule ID belongs to the approved group and exactly matches the CIDR, protocol, and port range |
| Authorization | A governed request has a recorded human approval |
| Audit | Containment execution has configured HMAC signing material |

No source code contains an AWS access key, secret key, session token, account credential, or Security Group target. When explicitly enabled, the adapter uses the workload’s standard AWS SDK credential provider chain. The configuration file contains only non-secret placeholders and must be replaced with the operator’s own deployment allowlists.

## Request parameters

The standard governed-containment route accepts the canonical request. For an AWS `block_indicator`, its `target` must equal the exact `cidr_ipv4`, and its `asset_id` must equal the exact `security_group_id`.

```json
{
  "action": "block_indicator",
  "target": "203.0.113.0/24",
  "asset_id": "sg-0123456789abcdef0",
  "idempotency_key": "incident-2026-aws-block-0001",
  "parameters": {
    "aws_region": "us-east-1",
    "security_group_id": "sg-0123456789abcdef0",
    "security_group_rule_id": "sgr-0123456789abcdef0",
    "cidr_ipv4": "203.0.113.0/24",
    "protocol": "tcp",
    "from_port": 443,
    "to_port": 443,
    "description": "Reviewed inbound rule"
  }
}
```

The adapter accepts only IPv4 CIDRs and TCP or UDP port ranges. It rejects wildcard protocols, wildcard ports, IPv6 source ranges, Security Group source references, prefix lists, implicit target discovery, unallowlisted resources, and non-approved actions.

## Execution and verification

After all preconditions pass, the adapter calls `RevokeSecurityGroupIngress` with the reviewed group ID and Security Group rule ID. It then calls `DescribeSecurityGroupRules` again. The execution is marked verified only if the exact rule is absent on read-back. Any SDK exception, missing precondition, account mismatch, rule mismatch, or read-back failure returns an unverified failure result and cannot become a verified containment execution.

The containment audit record stores the actual provider name, `aws-security-group`, together with the outcome. The durable execution evidence includes the non-secret AWS scope, account ID, operation name, and verified postcondition. No AWS API response is silently discarded.

## Rollback

Rollback is permitted only for a verified execution with rollback evidence. Before restoring access, the adapter scans a bounded set of Security Group rule pages to ensure that an equivalent permission is not already present. It then calls `AuthorizeSecurityGroupIngress` with the same reviewed permission and applies identifying tags for PhantomNet, request ID, and approval ID. Read-back must prove a matching ingress rule exists before rollback is marked verified.

The AWS documentation states that authorization adds ingress permissions and that a rule source must be one of an IP range, prefix list, or Security Group; the adapter intentionally limits this broader API surface to reviewed IPv4 CIDR permissions. [1]

## Deployment prerequisites

1. Install the backend requirements, including `boto3`.
2. Configure a workload IAM role or equivalent standard SDK credential-provider-chain identity with only the EC2 and STS permissions required for the explicitly allowlisted Security Groups.
3. Set `PHANTOMNET_AWS_SECURITY_GROUP_CONTAINMENT_ENABLED=false` until a lab validation is complete.
4. Configure the tenant-to-Security-Group JSON mapping, account, region, and CIDR allowlists through environment variables.
5. Configure `PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY` and `PHANTOMNET_CONTAINMENT_AUDIT_HMAC_KEY_ID` through environment-managed secrets.
6. Run a separate non-production AWS lab exercise before enabling a production target.

## Validation status and limitations

The adapter is validated with isolated mocked EC2 and STS clients. The test suite proves exact-rule revocation, absence read-back, restore read-back, disabled-by-default behavior, tenant/region/account/CIDR allowlist refusal, rule-precondition refusal, cloud-exception refusal, signed audit lifecycle integration, and preservation of provider-specific evidence.

No live AWS account, IAM role, VPC, Security Group, endpoint, or production workload was accessed during development. A real cloud validation requires operator-provided credentials and a dedicated non-production AWS lab; it is intentionally not attempted from this environment.

## References

[1]: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_AuthorizeSecurityGroupIngress.html "AuthorizeSecurityGroupIngress — Amazon EC2 API Reference"
[2]: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RevokeSecurityGroupIngress.html "RevokeSecurityGroupIngress — Amazon EC2 API Reference"
[3]: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSecurityGroupRules.html "DescribeSecurityGroupRules — Amazon EC2 API Reference"
