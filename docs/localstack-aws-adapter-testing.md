# LocalStack AWS Adapter Integration Testing

## Purpose

This Docker-gated integration suite validates PhantomNet’s AWS Security Group containment adapter against an isolated LocalStack EC2 and STS emulator. It uses explicit test-only credentials and a local endpoint. It never contacts an AWS account or uses production credentials.

The suite exercises real `boto3` client construction, Security Group creation, ingress-rule enumeration, approved-rule revocation, AWS-style read-back verification, and restoration through the adapter’s rollback flow.

> The integration test is skipped unless `PHANTOMNET_LOCALSTACK_ENDPOINT_URL` is explicitly configured. It should normally be run through the repository’s dedicated LocalStack Compose file.

## Execution boundary

LocalStack exposes its services through a configured endpoint URL, which is passed to `boto3` clients for this test. LocalStack’s EC2 service provides the API family required for Security Group resources, while STS provides caller identity emulation. [1] [2] [3]

The adapter’s verification behavior follows AWS EC2 API semantics: ingress authorization adds a reviewed permission, revocation removes one specified rule, and Security Group rule description is the source of read-back confirmation. [4] [5] [6]

## References

[1]: https://docs.localstack.cloud/aws/customization/networking/accessing-endpoint-url/ "Accessing LocalStack via the endpoint URL"
[2]: https://docs.localstack.cloud/aws/services/ec2/ "Elastic Compute Cloud (EC2) — LocalStack Docs"
[3]: https://docs.localstack.cloud/aws/services/ "Local AWS Services — LocalStack Docs"
[4]: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_AuthorizeSecurityGroupIngress.html "AuthorizeSecurityGroupIngress — Amazon EC2 API Reference"
[5]: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_RevokeSecurityGroupIngress.html "RevokeSecurityGroupIngress — Amazon EC2 API Reference"
[6]: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSecurityGroupRules.html "DescribeSecurityGroupRules — Amazon EC2 API Reference"

## Running the integration suite

On a Docker-capable host, start the isolated EC2 and STS emulator from the repository root:

```bash
docker compose -f docker-compose.localstack.yml up -d
curl --fail --retry 30 --retry-delay 1 http://127.0.0.1:4566/_localstack/health
export PHANTOMNET_LOCALSTACK_ENDPOINT_URL=http://127.0.0.1:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_EC2_METADATA_DISABLED=true
python3 -m pytest tests/test_aws_security_group_localstack.py -m localstack -vv -p no:cacheprovider
docker compose -f docker-compose.localstack.yml down -v
```

The suite creates an ephemeral Security Group and a single TCP/443 ingress rule for `203.0.113.0/24`, invokes the adapter without injected client factories, confirms that the approved rule was revoked, restores it through rollback, confirms the matching restored rule, and deletes the ephemeral Security Group. The test is intentionally skipped when `PHANTOMNET_LOCALSTACK_ENDPOINT_URL` is absent, including in environments where Docker is not available.

## Current environment status

The current development sandbox does not provide Docker, so LocalStack cannot be started or exercised here. The test’s skip behavior has been validated, and the complete non-Docker regression suite passes with the LocalStack case reported as one expected skip. Live AWS remains out of scope for this suite.
