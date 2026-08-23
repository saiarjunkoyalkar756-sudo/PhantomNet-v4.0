# Gate 1 — Self-Hosted Topology and Observability Evidence Template

## Scope declaration

| Field | Operator-recorded value |
|---|---|
| Run identifier | `<lab-topology-run-id>` |
| Operator / approval reference | `<owner-and-approval-reference>` |
| Code identity | `<commit-sha>`, `<branch>`, `<migration-head>` |
| Docker host identity | `<sanitized-host-profile-and-os>` |
| Deployment manifest | `deploy/self-hosted/docker-compose.yml` |
| Secret source | `<protected-lab-environment-file-or-secret-manager-identifier>` |
| Production data, production credential, customer endpoint, or public target used | **No** — stop and record a failed preflight if this cannot be truthfully stated. |
| Response adapters enabled | **No** — record a stop result if any response path is active. |

> This template captures proof from an operator-controlled Docker host. It does not authorize public ingress, production deployment, live containment, external cloud actions, or storage of secret values.

## Rendered topology and ingress

| Check | Expected safe result | Observation |
|---|---|---|
| Compose render | Render succeeds with no secret values retained in evidence | `<pass/fail-and-redacted-digest>` |
| PostgreSQL, Redis, Redpanda, Neo4j | No host-published ports; attached to `platform_internal` | `<pass/fail>` |
| Gateway ingress | Loopback binding only | `<resolved-loopback-binding>` |
| Prometheus ingress | Loopback binding only | `<resolved-loopback-binding>` |
| Internal networks | `platform_internal` and `observability_internal` remain internal | `<pass/fail>` |
| Stateless service hardening | Gateway uses read-only filesystem, dropped capabilities, and no-new-privileges | `<pass/fail>` |

## Health and readiness observations

| Service | Expected probe | Expected result | Sanitized observation |
|---|---|---|---|
| PostgreSQL | `pg_isready` container healthcheck | Healthy before gateway starts | `<status-and-time>` |
| Redis | authenticated internal `PING` healthcheck | Healthy before gateway starts | `<status-and-time>` |
| Redpanda | `rpk cluster health` | Healthy before gateway starts | `<status-and-time>` |
| Neo4j | internal HTTP healthcheck | Healthy before gateway starts | `<status-and-time>` |
| Gateway | `/health` | Diagnostic, secret-safe status | `<status-and-component-names-only>` |
| Gateway | `/ready` | 503 while a required dependency is unavailable; 200 only after all declared dependencies recover | `<negative-and-positive-observations>` |
| Gateway | `/metrics` | Bounded process counters, no tenant/user/request/secret labels | `<metric-names-and-sanitized-snapshot>` |
| Prometheus | `/-/healthy`, `/-/ready` | Healthy and scraping only internal gateway target | `<status-and-target-count>` |

## Restart and cleanup

| Field | Sanitized value |
|---|---|
| Stop/start result | `<service-health-and-volume-observation>` |
| Persistent volume expectation | `<declared-postgres-redis-redpanda-neo4j-prometheus-result>` |
| Unexpected outbound traffic or scope expansion | `<none-or-stop-result>` |
| Response adapter confirmation after test | `<all-disabled>` |
| Ephemeral environment and credential cleanup | `<completed-or-incomplete>` |
| Limits and unsupported conclusions | `<explicit-list>` |

## Conclusion

State only what the controlled run proves. A successful Gate 1 run can support an isolated Docker-host topology and observability statement for the recorded environment. It does not prove production availability, backup recovery, scale, Wazuh/AWS integration, endpoint enforcement, model efficacy, or broader deployment readiness.
