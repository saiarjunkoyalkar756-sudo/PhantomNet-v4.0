# Governed Response Proposals and Regional Telemetry Replication

## Scope

This capability adds two related but strictly separated operating controls. First, a response automation policy can create an **approval-required containment request** from a governed detection. Second, a regional transport can replicate **canonical telemetry envelopes only** to an explicitly configured regional stream. Neither capability grants automatic containment, response execution, rollback, or command delivery.

> A policy may propose a high-impact action; it may never approve, execute, verify, or roll back it. A replication target may receive canonical telemetry; it may never receive containment commands, audit commands, playbook commands, or adapter credentials.

## Response proposal lifecycle

| Stage | Control | Result |
|---|---|---|
| Detection match | Tenant policy matches rule ID and minimum severity | Candidate proposal only |
| Proposal precondition | Containment HMAC key and key ID must be configured | Failure closes the proposal path without creating a request |
| Request creation | Existing governed containment service creates the request | Request is signed-audit recorded and always requires approval |
| Approval | Human analyst performs the existing approval decision | No automatic approval path exists |
| Execution and rollback | Existing governed containment lifecycle handles adapter execution | Requires signed audit, configured adapter, verification, and rollback evidence |

Policies have literal bounded targets and administrator-managed parameters. They cannot evaluate arbitrary expressions, dynamically build action payloads from enrichment, or set `automatic_enforcement=true`. Repeated delivery of the same source detection maps to a deterministic idempotency key, so it returns the existing containment request rather than generating duplicates.

## Cross-region telemetry replication

The regional replication service observes validated canonical events after local processing. For each enabled tenant-owned target, it creates or updates a receipt keyed by **tenant, target, and event**. The receipt binds a SHA-256 hash of the canonical event payload, records attempts and delivery status, and detects unsafe reuse of an event ID with a different payload.

| Receipt status | Meaning | Retry behavior |
|---|---|---|
| `pending` | Delivery has been reserved and is in progress | A later identical canonical delivery may retry it |
| `delivered` | The regional transport acknowledged the canonical envelope | Replays return the existing receipt without another transport call |
| `failed` | The transport failed with a bounded error type | A later identical canonical delivery increments attempts and retries |

The default transport is disabled. It becomes available only when operators explicitly set `PHANTOMNET_TELEMETRY_REPLICATION_ENABLED=true` and provide a regional Kafka bootstrap configuration. The transport publishes only `EventEnvelope` JSON to the configured stream. It supports deployment-managed TLS and mutual TLS file paths; certificate and private-key contents never enter code, APIs, receipts, or logs.

## Operator configuration

```bash
PHANTOMNET_REGION=us-east-1
PHANTOMNET_TELEMETRY_REPLICATION_ENABLED=true
PHANTOMNET_REPLICATION_KAFKA_BOOTSTRAP_SERVERS=regional-broker.example:9093
PHANTOMNET_REPLICATION_KAFKA_SECURITY_PROTOCOL=SSL
PHANTOMNET_REPLICATION_KAFKA_SSL_CAFILE=/run/secrets/replication-ca.pem
PHANTOMNET_REPLICATION_KAFKA_SSL_CERTFILE=/run/secrets/replication-client.pem
PHANTOMNET_REPLICATION_KAFKA_SSL_KEYFILE=/run/secrets/replication-client-key.pem
```

Readiness reports the replication transport as disabled by default, not ready when explicitly enabled without a broker, and not ready in staging or production if TLS is not selected. It reports only protocol and TLS configuration state, never broker endpoints or certificate paths.

## Operations APIs

| Route | Capability | Behavior |
|---|---|---|
| `GET /response-policies` | `alerts:read` | Lists tenant-owned proposal policies |
| `POST /response-policies` | `config:write` | Creates or updates an approval-only tenant policy |
| `GET /telemetry-replication/targets` | `alerts:read` | Lists tenant-owned telemetry-only targets |
| `POST /telemetry-replication/targets` | `config:write` | Creates or updates a telemetry-only target |
| `GET /telemetry-replication/receipts` | `alerts:read` | Lists tenant-owned delivery receipts |

## Deployment limits

The code includes a Kafka transport boundary but this sandbox has no Docker, Redpanda, regional network, or operator TLS material. The actual broker-to-broker regional route, mutual TLS handshake, regional failover, retention, disaster recovery, and latency characteristics must be validated on a Docker-capable non-production environment before enabling the transport in staging or production.
