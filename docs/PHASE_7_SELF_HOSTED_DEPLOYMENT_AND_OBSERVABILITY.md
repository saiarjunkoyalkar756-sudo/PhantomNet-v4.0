# Phase 7: Self-Hosted Deployment and Observability

## Objective

Phase 7 establishes a **safe reference architecture** for operating PhantomNet on a Docker-capable self-hosted lab or production host. It narrows the initial deployment to the platform control plane and its required stateful dependencies, exposes only deliberate loopback ingress, and makes dependency health, runtime security posture, bounded process metrics, recovery evidence, and upgrade checks operational requirements.

> **Phase 7 is deployment readiness, not a claim of a live production deployment.** The reference topology must be validated on a Docker-capable host with operator-provided secrets, persistent storage, backups, and an external ingress control before it can be treated as operational evidence.

## Deliverables

| Deliverable | Location | Purpose |
|---|---|---|
| Reference Compose topology | `deploy/self-hosted/docker-compose.yml` | Starts the control-plane gateway, PostgreSQL, Redis, Redpanda, Neo4j, and internal Prometheus with health-gated dependencies. |
| Environment template | `deploy/self-hosted/env/.env.example` | Lists every required self-hosted secret and leaves all governed response adapters disabled by default. |
| Metrics scrape configuration | `deploy/self-hosted/monitoring/prometheus.yml` | Scrapes only the gateway metrics endpoint over the internal observability network. |
| Container readiness helper | `backend_api/shared/container_healthcheck.py` | Runs a bounded local `/ready` check without printing endpoint, credential, or exception detail. |
| Standard process metrics | `backend_api/shared/service_factory.py` | Exposes bounded Prometheus-compatible request, error, and total-duration counters at `/metrics`. |
| Focused regression coverage | `tests/test_phase7_self_hosted_deployment.py` | Enforces topology, ingress, secret-template, metrics, and health-helper safety boundaries. |

## Deployment architecture

```text
                     Operator-controlled reverse proxy / VPN / bastion
                                      │
                         loopback-only gateway ingress
                         127.0.0.1:${PHANTOMNET_GATEWAY_PORT}
                                      │
                               gateway-service
                     ┌────────────────┼────────────────┐
                     │                │                │
              platform_internal  observability_internal  operator_ingress
               (internal only)     (internal only)       (loopback only)
                     │                │
        ┌────────────┼───────┐        │
        │            │       │        │
   PostgreSQL      Redis  Redpanda  Prometheus
        │                            │
      Neo4j              scrapes gateway-service:8000/metrics
```

The reference topology deliberately omits broad published ports. PostgreSQL, Redis, Redpanda, and Neo4j are reachable only on `platform_internal`, which is marked `internal: true`. Prometheus runs on the separate `observability_internal` network and is published only to the local host. An operator must place a separately managed TLS-terminating reverse proxy, VPN, bastion, or private network control in front of the loopback gateway port; the Compose manifest does not expose an unauthenticated public listener.

| Component | Role | Storage | Network boundary | Readiness contract |
|---|---|---|---|---|
| `gateway-service` | Authenticated control-plane API and standard service health surface. | Stateless; read-only root filesystem with `/tmp` tmpfs. | Operator ingress, platform internal, observability internal. | Waits for every stateful dependency; `/ready` must return 2xx. |
| PostgreSQL | Durable operational, detection, case, audit, and governance data. | `postgres_data` named volume. | Platform internal only. | `pg_isready` against the configured service user and database. |
| Redis | Cache and coordination dependency. | `redis_data` named volume with append-only persistence. | Platform internal only. | Authenticated `redis-cli ping`. |
| Redpanda | Canonical event transport. | `redpanda_data` named volume. | Platform internal only. | `rpk cluster health`. |
| Neo4j | Optional durable graph context backend. | `neo4j_data` named volume. | Platform internal only. | Local HTTP availability check. |
| Prometheus | Internal metrics retention and operator troubleshooting. | `prometheus_data` named volume. | Observability internal; loopback-only operator port. | Starts only when the gateway is healthy. |

All pinned images avoid floating `latest` tags. The gateway and Prometheus use `no-new-privileges`, drop all Linux capabilities, use a read-only root filesystem, and receive only a temporary writable `/tmp`. Stateful databases retain their necessary writable data volume and still run with no-new-privileges. This distinction is intentional: making a stateful database read-only would break durability rather than improve security.

## Runtime and secret requirements

The reference environment file contains names and placeholders only. Operators must copy it to a protected `.env` file or inject equivalent values through a secret manager outside version control.

| Required setting | Operational role | Exposure rule |
|---|---|---|
| PostgreSQL, Redis, and Neo4j passwords | Protect stateful dependencies. | Never commit; never print in health, metrics, logs, or support artifacts. |
| JWT signing secret | Protect authenticated API tokens. | At least 32 characters when active mode is used. |
| Containment audit HMAC key and key ID | Sign governed containment audit evidence. | Required before a high-impact request can be persisted. The key value is never returned. |
| `PHANTOMNET_SAFE_MODE` | Controls whether integrations are actively exercised. | The reference topology sets it to `false` only because the dependencies are local and health-gated; response adapters remain explicitly disabled. |
| Endpoint, AWS, and Wazuh adapter flags | Prevent live containment until an adapter-specific lab runbook is completed. | All remain `false` in the template. |

## Health, readiness, and metrics requirements

PhantomNet distinguishes **liveness** from **readiness**. `/health` reports service and dependency diagnostics. `/ready` returns success only when the declared upstream dependencies and runtime security posture are ready; otherwise it returns HTTP 503. This makes Compose health gating dependent on operational capability rather than on a process merely remaining alive.

The standard service factory now exposes `/metrics` for an internal Prometheus scraper. The endpoint intentionally has no tenant, user, request path, event payload, case identifier, secret, or exception-message labels. It reports only the following bounded process counters:

| Metric | Meaning | Alerting use |
|---|---|---|
| `phantomnet_http_requests_total` | Total HTTP requests handled by a process. | Baseline traffic and process restart gaps. |
| `phantomnet_http_requests_4xx_total` | Client-error responses. | Unexpected operator or client failures. |
| `phantomnet_http_requests_5xx_total` | Server-error responses. | Service or dependency failure correlation. |
| `phantomnet_http_request_duration_seconds_sum` | Aggregate request wall-clock duration. | Latency trend when paired with request totals. |

Prometheus receives no public target discovery and scrapes only `gateway-service:8000/metrics` through `observability_internal`. The Phase 7 contract requires operators to keep Prometheus ingress loopback-only or protected by their own authenticated monitoring network.

## Recovery, backup, and upgrade requirements

The existing Docker recovery harness remains the minimum disposable proof for Redpanda round-trip, PostgreSQL write/read, and HMAC audit-chain append/verification. It is a recovery **exercise**, not a substitute for backups.

| Area | Requirement before operational use | Evidence to retain |
|---|---|---|
| PostgreSQL | Scheduled logical or physical backup, encrypted at rest, with a documented restore test. | Backup job status, restore timestamp, and row-level recovery verification. |
| Redis | Decide whether cache/coordinator data is recoverable or disposable; preserve append-only data only when required by the deployment design. | Recovery decision and restart behavior. |
| Redpanda | Define topic retention, replication, and backup/export policy appropriate to the host topology. A single-node lab does not provide broker fault tolerance. | Topic configuration and replay proof. |
| Neo4j | Back up graph data using an operator-approved procedure and rehearse restore before relying on graph context. | Backup and restore artifact. |
| Audit chain | Verify the tenant audit chain after restore, using the expected HMAC key identifier. | Chain-verification result and record count. |
| Upgrade | Render Compose configuration, verify image tags, back up stateful volumes, apply migration checks, then run health, readiness, smoke, and recovery checks. | Versioned preflight, migration, and post-upgrade validation report. |

## Deployment procedure for a controlled host

1. Use a Docker-capable host that is under the operator’s administrative control. Do not use the ephemeral development sandbox as a long-running service host.
2. Copy `deploy/self-hosted/env/.env.example` to a protected local `.env` file and replace every placeholder with high-entropy values. Confirm the file is excluded from version control.
3. Keep endpoint, AWS, and Wazuh response adapters disabled. Enable an adapter only through its separate non-production runbook and governed approval workflow.
4. Run the secret-safe release preflight before rendering or starting services. It requires a protected environment file, rejects placeholders and enabled response adapters, requires the documented JWT and containment-audit key lengths, and performs a quiet Compose render without printing configuration values:

```bash
cp deploy/self-hosted/env/.env.example deploy/self-hosted/.env
chmod 0600 deploy/self-hosted/.env
# Edit deploy/self-hosted/.env outside version control.
./scripts/preflight_self_hosted_release.sh deploy/self-hosted/.env
```

5. Render and inspect the composed configuration before starting services:

```bash
docker compose --env-file deploy/self-hosted/.env \
  -f deploy/self-hosted/docker-compose.yml config
```

6. Start the internal topology, then wait for every health check to become healthy:

```bash
docker compose --env-file deploy/self-hosted/.env \
  -f deploy/self-hosted/docker-compose.yml up -d --build

docker compose --env-file deploy/self-hosted/.env \
  -f deploy/self-hosted/docker-compose.yml ps
```

7. From the controlled host, validate the gateway readiness endpoint, metrics endpoint, dependency health, audit-chain verification, recovery harness, and benchmark workload. Publish only through an operator-managed TLS boundary.
8. Record the secret-free preflight result, exact image tags, a redacted Compose render or digest, migration revision, metrics snapshot, recovery artifact, and benchmark result before treating the host as a validated lab deployment.

## Validation boundary

Phase 7 adds static and isolated regression proof for the reference topology, health, metrics, and secret-safe release-preflight contracts. This development environment does not provide Docker, so it cannot claim a live Compose start, a successful preflight against a real protected environment file, persistent-volume test, or network topology proof. The repository’s Docker-dependent checks remain explicitly environment-gated; a Docker-capable lab host must execute them using non-production credentials and disposable or rehearsed data.

## Explicit limits

Phase 7 does not expose a public database, permit unauthenticated metrics access, enable response adapters, convert a safe preflight into an action, validate a production cloud account, or treat a successful `docker compose up` as a substitute for recovery, threat-model, and operator acceptance testing.
