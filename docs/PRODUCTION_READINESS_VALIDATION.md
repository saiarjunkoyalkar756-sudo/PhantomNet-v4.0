# Production-Readiness Validation Record

## Scope and evidence boundary

This record distinguishes **validated behavior** from work that requires an external runtime, a provider account, or explicit authorization. It documents the production-readiness validation performed against the repository’s isolated test harnesses on Python 3.12 and Node 22.

> A passing isolated test is evidence for the named invariant. It is not a claim that an unstarted Docker deployment, an unconfigured EDR tenant, or an unapproved external target was exercised.

## Validation summary

| Validation area | Evidence executed | Result | Boundary |
|---|---|---|---|
| Full Python regression | `python3 -m pytest -q -p no:cacheprovider` | **288 passed, 6 skipped** | Skips are Docker/LocalStack/live-topology gated. |
| Governed response stress | 24 request → approval → execution → rollback lifecycles | **Passed** | Deterministic non-live adapter; 96 signed lifecycle records verified as one tenant chain. |
| Authentication and RBAC | Session-binding, tenant-binding, governance, gateway, secret, and agent-command suites | **27 focused tests passed** | Isolated SQLite and mockable broker boundaries. |
| Audit trust model | Tenant integrity, HMAC signature, wrong-key, mutation, deletion, raw-SQL tamper, and agent-signature tests | **12 focused tests passed** | Cryptographic and persistence checks are local and deterministic. |
| Failure injection | Persistence, alert, replication, audit tamper, containment, Compose harness tests | **17 focused tests passed** | Local injected faults; no broker or database container available in this environment. |
| Controlled BAS/red-team fixtures | BAS scenarios, canonical ingestion, controlled pipeline, lateral movement | **12 focused tests passed** | Synthetic, non-destructive fixtures only. |
| Dashboard quality | ESLint and Vite production build | **Passed** | Static/production bundle validation. |
| Portal quality | ESLint and Next.js production build | **Passed** | Static/production route generation validation. |

## Corrected security findings

### JWT tenant and session binding

The strict `TokenData` schema did not accept the tenant claim that `get_current_user` requires, causing real token validation to reject otherwise valid claims. The schema now models `tenant_id` explicitly. The authentication path now also rejects a token when its persisted session belongs to a different user or when the authenticated user’s tenant differs from the signed tenant claim.

The session expiry comparison is normalized to UTC when a database driver returns a naive timestamp. Focused tests prove the valid path succeeds and both session-owner and tenant mismatch paths return `401`.

### Unsupported host isolation no longer reports success

The Linux agent platform adapter had an isolation placeholder that returned a success response without applying or verifying any firewall state. It now fails closed with explicit `enforced: false`, `verified: false`, and `rollback_available: false` evidence until a policy-bound endpoint-management provider is configured. LinuxAdapter also now satisfies its abstract runtime contract using bounded telemetry operations and explicit non-enforcement for generic command execution, direct address blocking, and process termination.

## Governed response assurance

The stress harness executes 24 unique approved containment requests through a deterministic adapter and requires successful verification before rollback. Each lifecycle creates four HMAC-signed records: `containment.requested`, `containment.approved`, `containment.executed`, and `containment.rolled_back`.

The test verifies the adapter call sequence, final rolled-back state, record count, signing key identifier, and complete chain validity. Existing tenant-integrity coverage additionally proves that ORM updates/deletes are blocked, raw SQL mutation invalidates verification, and each tenant’s audit chain verifies independently.

## Docker topology proof

A new isolated Docker proof package is available for a Docker-capable host:

```bash
./scripts/run_docker_topology_validation.sh
```

It starts disposable PostgreSQL, Redis, Redpanda, and Neo4j services, waits for Compose health checks, and runs real internal protocol round trips from the `integration-tests` container. The tests use unique temporary probes, authenticated connections, no published production service, and a cleanup trap that removes volumes and containers. See [Docker Topology Validation](DOCKER_TOPOLOGY_VALIDATION.md).

This sandbox does not have Docker Engine or Docker Compose v2 installed. The live topology proof therefore **was not executed here**; static Compose, shell syntax, and Docker-gated test collection passed. The separate [Docker Recovery Validation](DOCKER_RECOVERY_VALIDATION.md) procedure remains the required broker/PostgreSQL restart and fail-closed outage proof on a Docker-capable host.

## Endpoint and EDR integration status

| Integration | Current validation status | Safety posture |
|---|---|---|
| Local firewall adapter | Unit validated for scoped RFC 5737 test addresses, apply/verify/rollback semantics, and audit logging. | Disabled/dry-run by default; explicit confirmation required for changes. |
| AWS Security Group adapter | Unit validated; LocalStack integration is opt-in and Docker-gated. | Tenant/account/region/security-group/CIDR allowlists with post-change read-back verification. |
| Agent host isolation | Explicitly **not enforced** without a configured provider. | Fails closed; never reports a placeholder success. |
| Vendor EDR | Not configured or live-validated in this repository environment. | Requires an approved EDR provider, service credential, lab endpoint, management-path policy, and a provider-specific verification/rollback contract. |

A real EDR replacement must be validated against an organization-owned or explicitly authorized lab tenant. It must produce an independently verifiable isolation state and a reversible release state; broker acceptance or command publication alone is not sufficient evidence.

## External security testing boundary

No internet-facing or third-party target was scanned, exploited, or attacked. The executed red-team coverage is limited to controlled BAS fixtures owned by the project. A live external red-team engagement requires a written authorization scope that identifies the owned target, permitted techniques, timing, rate limits, data-handling rules, emergency contact, and rollback plan.

## Required next evidence before production claims

1. Run `scripts/run_docker_topology_validation.sh` and `scripts/run_docker_recovery_validation.sh` on a controlled Docker-capable host; retain the generated artifacts.
2. Configure one approved endpoint/EDR provider in a dedicated lab tenant and implement its signed request, observed-state verification, and rollback adapter.
3. Run the LocalStack AWS adapter test and, if cloud containment is enabled, complete a separate least-privilege account review.
4. Perform an authorized, scoped external assessment against organization-owned infrastructure with an approved rules-of-engagement document.
5. Configure CI branch protection to require the `Quality Gate Summary` status before merge.
