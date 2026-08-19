# Docker Recovery Validation

**PhantomNet’s Docker recovery validation** is an isolated, non-production harness that validates whether a Redpanda restart and a PostgreSQL restart can be followed by fresh successful broker, persistence, and HMAC-signed audit-chain operations. It is intentionally separate from the project’s main Compose topology, never publishes host ports, and destroys its short-lived PostgreSQL volume during cleanup.

> This harness is a **dependency recovery validation**, not a production approval for a deployment. It does not execute response adapters, contact cloud providers, alter endpoint state, or use production credentials.

## Scope and Safety Boundary

| Control | Implementation | Operator consequence |
|---|---|---|
| Isolated topology | `docker-compose.recovery-validation.yml` has an internal-only `recovery_internal` network and no `ports` mappings. | The test dependencies are not reachable from the host network or the public internet. |
| Non-production credentials | The runner requires caller-provided `RECOVERY_DB_PASSWORD`, `RECOVERY_AUDIT_HMAC_KEY`, and `RECOVERY_AUDIT_HMAC_KEY_ID`. | Do not reuse production database or containment-audit values. Generate temporary values for each run. |
| Ephemeral storage | The cleanup trap executes `docker compose down --volumes --remove-orphans`. | PostgreSQL test data is removed when the runner completes, fails, or is interrupted. |
| No containment path | The probe is limited to Kafka, PostgreSQL, and the canonical audit-integrity implementation. | No endpoint, AWS Security Group, Wazuh, SOAR, or response adapter action occurs. |
| Secret-safe evidence | The probe writes only check names, statuses, offsets, durations, and audit record counts. | Neither database passwords nor HMAC key material is written to JSONL evidence. |

## Host Prerequisites

The validation must be run on a Docker-capable non-production host with Docker Engine and Docker Compose v2 available to the invoking account. The host needs sufficient capacity to build a small Python probe image and run one Redpanda broker plus one PostgreSQL 16 container. It should have network access to pull the pinned Redpanda, PostgreSQL, and Python base images if they are not already present locally.

| Requirement | Verification | Reason |
|---|---|---|
| Docker Engine | `docker --version` exits successfully. | The runner starts and restarts isolated containers. |
| Docker Compose v2 | `docker compose version` exits successfully. | The runner uses Compose health checks, restart commands, and deterministic teardown. |
| Ephemeral secret values | Export all three `RECOVERY_*` variables before execution. | PostgreSQL and signed audit verification fail closed without their required inputs. |
| Non-production execution context | Confirm the working tree is the intended test checkout. | The runner must not be aimed at a production Compose project or production secret store. |

## Execution

From the repository root, export new temporary values through the approved local secret mechanism, then run the validation script. The following variable names are required; values must be generated uniquely for the test environment and must not be committed:

```bash
export RECOVERY_DB_PASSWORD='<temporary non-production database password>'
export RECOVERY_AUDIT_HMAC_KEY='<temporary non-production audit HMAC key>'
export RECOVERY_AUDIT_HMAC_KEY_ID='<temporary non-production audit key identifier>'
bash scripts/run_docker_recovery_validation.sh
```

The runner creates a time-scoped Compose project, waits for Redpanda and PostgreSQL health checks, writes evidence under `artifacts/`, and always attempts cleanup. For CI or pytest-driven execution, enable the Docker-only suite explicitly:

```bash
export PHANTOMNET_DOCKER_AVAILABLE=true
pytest tests/test_docker_recovery.py -m docker -q
```

The pytest suite creates fresh ephemeral database and HMAC values for the subprocess, directs evidence to pytest’s temporary directory, and verifies that cleanup is handled by the runner. Setting `PHANTOMNET_DOCKER_AVAILABLE` is deliberately opt-in; without it, the test reports a skip rather than attempting Docker access.

## Scenario Sequence and Required Invariants

| Stage | Induced condition | Required evidence | Failure condition |
|---|---|---|---|
| Baseline | Healthy Redpanda and PostgreSQL. | A broker marker is produced, consumed, and committed; a PostgreSQL receipt is written and read; the signed audit chain verifies. | Any dependency probe or audit verification fails. |
| Broker restart | The isolated `redpanda` service is stopped after an audit-chain pre-check, then started again. | The probe must fail while the broker is down; audit verification remains valid during the outage; Redpanda then becomes healthy and a fresh marker round-trip succeeds. | A broker probe succeeds during the outage, startup health fails, delivery/commit fails after recovery, or audit verification fails. |
| PostgreSQL restart | The isolated `postgres` service is stopped after an audit-chain pre-check, then started again. | The probe must fail while PostgreSQL is down; PostgreSQL then becomes healthy, a fresh idempotent receipt write/read succeeds, and the persisted audit chain remains valid afterward. | A PostgreSQL probe succeeds during the outage, startup health fails, receipt persistence fails after recovery, or audit verification fails. |
| Teardown | All checks complete or a command fails. | Compose volumes and orphaned containers are removed. | Cleanup failure is reported but does not hide the primary validation failure. |

The audit check imports PhantomNet’s `append_record` and `verify_chain` implementations directly. Every audit validation record is HMAC-signed, links to the preceding record, and is verified with `require_signature=True` and the expected key identifier. The Docker-gated pytest asserts audit evidence counts `[1, 2, 3, 4, 5, 6]`, representing baseline, broker pre-check, broker-outage check, broker post-recovery, PostgreSQL pre-check, and PostgreSQL post-recovery.

## Evidence and Interpretation

The runner writes a JSON Lines file named `artifacts/docker_recovery_validation_<UTC timestamp>.jsonl`. The evidence includes phase-start records, successful broker offsets, successful PostgreSQL receipt checks, audit-chain verification record counts, and one final completion record. The validation passes only when its final JSON record is exactly `{"phase":"complete","status":"passed"}`.

| Evidence field | Meaning | Sensitive data policy |
|---|---|---|
| `check` and `status` | Probe operation and outcome. | Safe to retain in test artifacts. |
| `produced_offset` and `consumed_offset` | Redpanda validation-marker delivery evidence. | Safe; no telemetry content is retained. |
| `record_count` | Number of persisted HMAC-signed audit records verified in sequence. | Safe; no HMAC key or signature body is emitted. |
| `error_type` | Exception class when a probe fails. | Safe; the probe avoids emitting DSNs, passwords, and HMAC values. |

## Current Validation Status and Limits

| Capability | Status in the current sandbox | What a Docker-capable host must still validate |
|---|---|---|
| Static harness checks | Implemented and executed. The shell syntax, isolation declarations, required secret gates, restart sequence, cleanup trap, and no-Docker fail-fast behavior are tested. | None. |
| Redpanda restart recovery | Implemented but not executed here because Docker is unavailable. | Run the script or Docker-marked pytest test and preserve the emitted JSONL evidence. |
| PostgreSQL restart recovery | Implemented but not executed here because Docker is unavailable. | Run the script or Docker-marked pytest test and preserve the emitted JSONL evidence. |
| Signed audit-chain continuity | Implemented with PhantomNet’s canonical integrity functions but not Docker-executed here. | Confirm all six audit checks pass around both restarts. |
| Full multi-service recovery | Out of scope for this focused harness. | Validate the canonical consumer, migrations, Redis, Neo4j, and all service retry/backoff behavior in a subsequent end-to-end deployment exercise. |
| Mid-transaction failure replay | Out of scope for this focused harness. | Add a deterministic application-level fault-injection scenario that interrupts a canonical consumer between persistence and offset commit. |

The sandbox’s Docker absence is an explicit environmental limitation, not a passing Docker result. The test suite preserves this distinction through a marker and an opt-in `PHANTOMNET_DOCKER_AVAILABLE=true` guard. [1]

## References

[1]: https://docs.docker.com/compose/ "Docker Compose documentation"
