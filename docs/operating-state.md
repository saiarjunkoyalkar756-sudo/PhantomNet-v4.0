# PhantomNet Operating State and Control Boundaries

PhantomNet is currently a **development and controlled-test platform**. The source tree now contains versioned telemetry contracts, bounded local enforcement, a provider-response boundary, read-only intelligence enrichment, centralized capability checks, and a verifiable audit-chain utility. These components improve the trustworthiness of test results but do not by themselves establish production readiness.

| Capability | Current state | Operational boundary |
|---|---|---|
| Local firewall test adapter | Verified in a local sandbox | It is disabled by default and accepts only RFC 5737 documentation addresses. It must not be used as a production perimeter control. |
| External response provider | Implemented and unit-tested | It remains disabled until an operator configures a provider endpoint, credentials, a tenant allowlist, a test-lab target allowlist, and approval workflow. |
| Host isolation and process termination | Provider-gated | PhantomNet returns a failure when no configured provider supplies verified evidence. It must not claim containment without provider verification. |
| World Intel context | Read-only adapter and tests | The transport remains unconfigured. Its output is evidence for human review and is prohibited from triggering automatic enforcement. |
| RBAC | Central policy and tests | Existing API role dependencies should be migrated to this policy incrementally. High-impact provider requests enforce the central policy now. |
| Audit integrity | Hash-chain utility and tests | The chain detects export tampering. Independent anchoring or object-lock storage is still required for stronger immutability guarantees. |
| Full microservice integration | Compose configuration prepared | The current sandbox does not include Docker, so the dependency stack and container-level E2E tests have not been run here. |

## Required Deployment Safeguards

Any real provider integration must be constrained to a dedicated test tenant and non-production target group. It must require an approver with `response:approve`, preserve an idempotency key, record provider request evidence, and report success only after a provider confirms both enforcement and verification.

World Intel evidence must retain source/provenance fields and remain outside automated response decision paths. Analysts may use it to prioritize triage, but it must not independently alter enforcement status.

## Integration Stack Execution

The repository includes `docker-compose.integration.yml` for a temporary Postgres, Redis, Redpanda, and Neo4j test stack. Execute it only in an isolated environment with Docker available. The test configuration uses non-production credentials and ephemeral data storage, but it is not a production deployment definition.
