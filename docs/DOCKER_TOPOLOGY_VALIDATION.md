# Docker Topology Validation

## Purpose

This runbook proves the **isolated non-production dependency topology** used by PhantomNet integration validation. It starts PostgreSQL, Redis, Redpanda, and Neo4j in disposable containers, then runs actual protocol round trips from a dedicated integration-test container.

> This procedure does not touch a production database, broker, cloud account, endpoint, or external network target. It is a host-side proof for the Compose dependency topology, not a production capacity or deployment certification.

## What is verified

| Service | Live check | Passing evidence |
|---|---|---|
| PostgreSQL | Authenticated table creation, insert, and parameterized read-back. | The exact unique probe value is returned. |
| Redis | Authenticated-in-network `PING`, scoped key write, and read-back. | `PING` succeeds and the temporary key contains `verified`. |
| Redpanda | Produce and consume a unique message on an auto-created internal topic. | The consumer receives the exact sent payload. |
| Neo4j | Authenticated transactional HTTP `RETURN` query. | The API returns no errors and the expected result value. |

The integration-test container waits on Compose health checks for all four services before it starts. PostgreSQL data is stored on `tmpfs`, every probe key/topic/value is uniquely generated, and the runner removes containers, volumes, and orphan resources after completion.

## Prerequisites

Run this procedure only on a Docker-capable host with Docker Compose v2 available to the invoking user. The test Compose file contains only explicitly named test credentials and does not consume production environment values.

| Requirement | Reason |
|---|---|
| Docker Engine | Runs the disposable dependency services and integration test container. |
| Docker Compose v2 | Applies health-gated service startup and automatic cleanup. |
| Network access to container image registries | Pulls the declared Postgres, Redis, Redpanda, Neo4j, and Python images when not cached. |
| Write access to `artifacts/` | Stores the timestamped runner log. |

## Execute the proof

```bash
cd /path/to/PhantomNet-v4.0
chmod +x scripts/run_docker_topology_validation.sh
./scripts/run_docker_topology_validation.sh
```

The runner writes a timestamped log to `artifacts/docker_topology_validation_<timestamp>.log`. A successful run ends with `status=passed`; a non-zero exit status is a validation failure and must not be treated as an end-to-end proof.

## Failure handling

Preserve the generated log and inspect only resources belonging to the timestamped `phantomnet-topology-` Compose project. The cleanup trap runs even after an error and removes temporary containers, volumes, and orphans.

| Failure | Meaning | Safe next action |
|---|---|---|
| Docker or Compose unavailable | The host cannot run the topology proof. | Use a Docker-capable local machine or controlled CI runner. |
| Service health gate fails | A declared dependency did not reach its expected ready state. | Inspect the retained runner log; do not bypass the health gate. |
| PostgreSQL/Redis/Redpanda/Neo4j probe fails | The internal service connection or protocol round trip is broken. | Treat as an integration defect; preserve evidence and investigate the named service. |
| Integration test fails | The topology did not meet the required end-to-end proof. | Do not claim a successful Docker validation; repair and rerun in the same isolated topology. |

## Relationship to recovery validation

This topology proof establishes healthy service reachability and protocol behavior. Recovery behavior is tested separately by the [Docker Recovery Validation](DOCKER_RECOVERY_VALIDATION.md) runner, which injects broker and PostgreSQL outages and verifies fail-closed probes plus HMAC-backed audit evidence.
