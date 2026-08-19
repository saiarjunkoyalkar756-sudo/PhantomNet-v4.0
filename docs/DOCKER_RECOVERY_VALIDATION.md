# Docker Recovery Validation

## Purpose

This runbook validates that the **non-production** PhantomNet recovery topology fails closed while its broker or database is unavailable, then resumes its controlled health probes after the dependency returns. It is an operational validation of the isolated Compose harness; it is **not** a production deployment guide, capacity test, or authorization to exercise a production stack.

> The recovery runner creates a timestamped Compose project, uses an internal-only network, and tears down containers and volumes when it exits. Do not point it at an existing environment or reuse production credentials.

## Preconditions

Run the validation from the repository root on a Docker-capable host. The host must have a running Docker daemon and Docker Compose v2. The validation runner checks both conditions before it starts.

| Requirement | Required value or condition | Reason |
|---|---|---|
| Docker Engine | Available to the invoking user | Starts the isolated Redpanda, PostgreSQL, and probe containers. |
| Docker Compose | Version 2 command available | Namespaces, builds, starts, stops, and destroys the temporary validation project. |
| `RECOVERY_DB_PASSWORD` | A newly generated, non-production database password | Authenticates only the temporary `recovery_validator` PostgreSQL user. |
| `RECOVERY_AUDIT_HMAC_KEY` | A newly generated, non-production HMAC key | Signs and verifies the probe’s audit evidence. |
| `RECOVERY_AUDIT_HMAC_KEY_ID` | A non-production identifier for that key | Binds generated evidence to the intended ephemeral signing key. |
| Disk access | Write access to `artifacts/` or `PHANTOMNET_RECOVERY_ARTIFACT_DIR` | Stores the timestamped JSONL validation evidence. |

The Compose topology publishes **no host ports**. All containers communicate only over the `recovery_internal` network, which is marked `internal: true`. The probe container is read-only, receives a temporary `/tmp` filesystem, and runs with `no-new-privileges`.

## Safe execution

Generate fresh values in the terminal session that will execute the test. Do not place these values in source control, shell history shared with other users, or a production secret manager entry.

```bash
cd /path/to/PhantomNet-v4.0
export RECOVERY_DB_PASSWORD="$(openssl rand -hex 24)"
export RECOVERY_AUDIT_HMAC_KEY="$(openssl rand -hex 32)"
export RECOVERY_AUDIT_HMAC_KEY_ID="recovery-validation-$(date -u +%Y%m%dT%H%M%SZ)"

./scripts/run_docker_recovery_validation.sh
```

If artifact output must be placed elsewhere, set `PHANTOMNET_RECOVERY_ARTIFACT_DIR` to a writable **non-production** directory before invoking the runner.

## What the runner verifies

| Phase | Controlled action | Passing condition |
|---|---|---|
| Startup | Builds the recovery probe and starts Redpanda plus PostgreSQL. | Broker and database health checks pass; the combined probe completes. |
| Broker restart | Stops Redpanda, executes a broker probe, restarts Redpanda, and waits for health. | The probe fails while Redpanda is stopped, then succeeds after recovery. |
| PostgreSQL restart | Stops PostgreSQL, executes a database probe, restarts PostgreSQL, and waits for readiness. | The probe fails while PostgreSQL is stopped, then succeeds after recovery. |
| Audit checks | Runs audit probes before, during, and after outage scenarios. | Each successful probe emits HMAC-verifiable audit evidence. |
| Cleanup | Handles process exit through a shell trap. | The timestamped project is removed with its temporary volumes and orphan containers. |

A passing run ends with a JSONL record containing `{"phase":"complete","status":"passed"}` and prints the evidence path. The artifact file contains line-oriented records from each probe and explicit pass records for the fail-closed outage checks.

## Failure handling

A non-zero exit status is a validation failure. Preserve the generated JSONL artifact and terminal output, then investigate the first failed phase. Do **not** rerun against a production environment to diagnose a test failure. The runner’s cleanup trap attempts to remove the temporary project even on failure; manually inspect Docker resources only after confirming their names begin with the timestamped `phantomnet-recovery-` project prefix.

| Symptom | Interpretation | Safe next action |
|---|---|---|
| Exit code `2` before startup | Docker Engine or Docker Compose v2 is unavailable. | Install or start the required local Docker tooling, then rerun on a non-production host. |
| Missing-secret failure | An ephemeral recovery secret was not provided. | Export fresh non-production values and rerun. |
| Redpanda or PostgreSQL readiness timeout | The isolated service did not become healthy within the runner’s bounded retry window. | Retain evidence, inspect only the temporary project logs, then correct host resource or image-pull issues. |
| Outage probe succeeds | The dependency outage did not fail closed. | Treat as a security defect; preserve artifacts and do not mark the recovery validation as passed. |
| Audit verification fails | Evidence integrity is invalid or key configuration is inconsistent. | Treat as a security defect; rotate the ephemeral test key and investigate before another run. |

## Current sandbox limitation

This development sandbox does not have Docker installed. The repository’s Docker-gated tests therefore skip explicitly, and this runbook records the required host-side verification rather than claiming that it ran here.

## Related implementation

The procedure is implemented by `scripts/run_docker_recovery_validation.sh`, the isolated `docker-compose.recovery-validation.yml` topology, and `scripts/run_docker_recovery_validation.py`. The non-Docker regression suite includes an explicit Docker-gated test so environments without Docker do not produce a false failure.
