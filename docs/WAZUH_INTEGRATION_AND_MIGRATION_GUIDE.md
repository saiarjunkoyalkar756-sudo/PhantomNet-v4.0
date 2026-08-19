# Pairing PhantomNet with Wazuh

**Document purpose:** A production-safe integration and migration outline for teams that want to retain Wazuh endpoint visibility while adding PhantomNet’s governed correlation, case workflow, graph context, and audit-backed response controls.

**Recommended strategy:** **Integrate first; migrate only after evidence.** Do not remove Wazuh agents, disable Wazuh detections, or route endpoint actions through PhantomNet until each handoff has been tested in an authorized lab and approved by the security owner.

## Executive design

Wazuh remains the **endpoint telemetry and native-agent system of record** during the initial adoption period. PhantomNet becomes the **cross-source correlation, governed case-management, and approval/evidence control plane**. The current PhantomNet Wazuh forwarder intentionally accepts telemetry only: it cannot trigger automatic containment or request any response action.

> **Non-negotiable control:** A Wazuh alert forwarded into PhantomNet must never become an unreviewed endpoint action. High-impact response stays disabled on the forwarding path until a dedicated, authorized, independently verified adapter is available.

Wazuh documents a manager, indexer, dashboard, and multi-platform agent model, along with agent enrollment, API control, and alert-driven Active Response.[1] [2] [3] PhantomNet’s current forwarder adds per-tenant registration, a token shown once at registration, ordered batch sequencing, replay protection, tenant binding, canonical asset/integrity ingestion, and an explicit telemetry-only response boundary. [PhantomNet Wazuh Forwarder Tests](../tests/test_wazuh_forwarder_streaming.py)

## Target operating model

| Responsibility | Wazuh owns initially | PhantomNet owns initially | Shared control |
|---|---|---|---|
| Endpoint agent enrollment, configuration, FIM, inventory, and vulnerabilities | **Yes** | No | PhantomNet may consume selected evidence only. |
| Endpoint alert generation and local rule execution | **Yes** | No | Retain established Wazuh alert routing during parallel operation. |
| Canonical event normalization and cross-source correlation | Source events only | **Yes** | Map Wazuh identifiers and severity into the canonical schema. |
| Asset and integrity evidence | Produces the evidence | Stores normalized asset/integrity records | Use agent ID and hostname mapping with tenant-scoped forwarders. |
| Case management, analyst workflow, graph context | Optional Wazuh workflow | **Yes** | Link Wazuh alert IDs as external evidence. |
| High-impact response | Keep existing Wazuh Active Response disabled for the selected pilot scope, or retain it under a separately documented owner | **Approval-gated only** | Never permit two systems to issue the same containment action automatically. |
| Audit evidence | Wazuh logs actions/alerts | **HMAC-backed containment audit chain** | Preserve both records and correlate them with immutable external IDs. |

## Reference architecture

```text
Wazuh agents
     │
     ▼
Wazuh manager / indexer / dashboard
     │  selected alerts and asset evidence
     ▼
Read-only integration sidecar
  - transforms Wazuh alert JSON
  - batches and sequences records
  - sends only to one tenant-bound forwarder
     │  HTTPS + X-PhantomNet-Forwarder-Token
     ▼
PhantomNet endpoint-inventory service
  - token and sequence validation
  - canonical telemetry and integrity records
  - correlation, cases, graph context
     │
     ├── analyst investigation
     └── governed containment request
             │
             ▼
       human approval → authorized adapter → independent verification → rollback evidence
```

The sidecar is deliberately a **new integration component** rather than an implied built-in Wazuh manager plugin. PhantomNet’s repository currently provides the receiving service and contract; it does not claim a production Wazuh manager plugin or a verified live EDR bridge. Treat the sidecar as a small, separately versioned deployment with its own tests, secrets, logs, and rollback procedure.

## Phase 0 — governance and preflight

Begin with one tenant, one non-production Wazuh group, and a written change record. Name an operations owner for Wazuh, a platform owner for PhantomNet, and an approver for any future containment change.

| Preflight requirement | Acceptance criterion |
|---|---|
| Scope | A written list of Wazuh agent groups, host classes, alert categories, and excluded production systems exists. |
| Identity | Wazuh agent enrollment continues to use secure identity controls; no PhantomNet credential is installed on endpoints. Wazuh documents agent enrollment and manager/agent identity-verification options.[1] |
| Tenant model | Each PhantomNet forwarder maps to exactly one tenant. The tenant is assigned at registration, **not supplied by the Wazuh alert payload**. |
| Network path | The sidecar has egress only to the PhantomNet endpoint-inventory service over TLS. PhantomNet does not require inbound access to Wazuh agents. |
| Secrets | Forwarder tokens, Wazuh API credentials, and TLS material are stored in the deployment’s secret manager or environment injection mechanism; never in source control, alert payloads, or dashboard variables. |
| Response ownership | For the pilot hosts, either disable overlapping Wazuh Active Response rules or explicitly retain them under Wazuh-only ownership. Do not configure duplicate automatic isolation paths. |
| Recovery | Confirm that revoking a PhantomNet forwarder stops ingestion without modifying Wazuh manager or agent configuration. |

## Phase 1 — telemetry-only pilot

Register a forwarder from an authenticated PhantomNet account with the `config:write` capability:

```http
POST /wazuh/forwarders
Content-Type: application/json
Authorization: Bearer <phantomnet-user-jwt>

{"name":"wazuh-lab-tenant-a"}
```

The response includes a `forwarder_id` and a `forwarder_token`; the token is shown once. Store it in the sidecar’s secret store and retain only the token prefix in operator notes. The receiving service stores a SHA-256 digest, not the plaintext token. [Forwarder implementation](../backend_api/endpoint_inventory_service/forwarders.py)

The sidecar sends an ordered `WazuhTelemetryBatch` to the registered route:

```http
POST /wazuh/forwarders/<forwarder_id>/stream
Content-Type: application/json
X-PhantomNet-Forwarder-Token: <stored-forwarder-token>

{
  "batch_id": "wazuh-lab-20260819-000001",
  "sequence": 1,
  "alerts": [
    {
      "id": "wazuh-alert-123",
      "timestamp": "2026-08-19T10:00:00Z",
      "agent": {
        "id": "007",
        "name": "lab-linux-01",
        "ip": "10.0.0.20",
        "os": {"name": "Ubuntu", "version": "24.04"}
      },
      "rule": {
        "id": "550",
        "level": 10,
        "description": "Integrity checksum changed",
        "groups": ["syscheck"]
      },
      "syscheck": {
        "event": "modified",
        "path": "/etc/passwd",
        "sha256_before": "<previous>",
        "sha256_after": "<current>"
      }
    }
  ]
}
```

This endpoint returns `202` only for an authenticated, active forwarder with the exact next sequence and a previously unseen `batch_id`. Invalid tokens receive `401`; replayed or out-of-order batches receive `409`. A successful result must show `adapter_mode: "read_only_streaming"` and `automatic_enforcement: false`. [Forwarder API](../backend_api/endpoint_inventory_service/main.py) [Forwarder streaming tests](../tests/test_wazuh_forwarder_streaming.py)

### Minimal mapping contract

| Wazuh field | PhantomNet use | Required transformation rule |
|---|---|---|
| `id` | External evidence identifier | Preserve unchanged and attach to canonical event evidence. |
| `timestamp` | Event occurrence time | Require ISO 8601 UTC; reject or quarantine malformed timestamps. |
| `agent.id`, `agent.name`, `agent.ip`, `agent.os` | Tenant-scoped asset inventory | Do not use a Wazuh agent ID as a globally unique tenant identifier. |
| `rule.id`, `rule.level`, `rule.description`, `rule.groups` | Detection context and priority | Preserve raw values; map priority in a versioned mapping table, not in ad hoc code. |
| `syscheck.*` | Integrity observation | Create integrity evidence only when required fields are present; retain the raw source fragment. |
| Wazuh manager/group metadata | Provenance and routing | Add as source metadata; never use it to override the tenant registered to the forwarder. |

### Pilot exit criteria

The pilot is ready to expand only when all of the following are demonstrated in an isolated tenant:

1. A valid batch creates the expected asset, canonical event, and integrity evidence.
2. Invalid token, revoked token, duplicate `batch_id`, and skipped sequence tests fail closed.
3. One Wazuh alert can be located in both systems by its preserved external identifier.
4. Wazuh remains fully functional if the sidecar is stopped or PhantomNet becomes unavailable.
5. No forwarded event triggers a containment request or an endpoint command.

## Phase 2 — parallel detection and case workflow

Keep Wazuh rules and alerts active. Use PhantomNet to correlate Wazuh endpoint observations with identity, cloud, network, or application telemetry already flowing through PhantomNet. Begin with analyst-facing use cases rather than automated actions:

| Use case | Wazuh contribution | PhantomNet contribution | Exit evidence |
|---|---|---|---|
| File-integrity modification | FIM alert with agent/path/hash data | Asset context, tenant-safe case, related identity/network events | Analyst can reconstruct the event path without endpoint action. |
| Suspicious process or configuration event | Endpoint rule and agent metadata | Cross-source correlation and MITRE-aligned evidence | Case includes source alert ID, asset, owner, severity, and disposition. |
| Vulnerable asset prioritization | Inventory and vulnerability observation | Graph context and case priority | The same asset can be prioritized using business/context signals. |
| Repeated endpoint anomalies | Multiple Wazuh alerts | Deduplication/correlation and playbook tasks | Alert volume is reduced without losing source evidence. |

At this stage, analysts should resolve cases in PhantomNet while treating the Wazuh dashboard as the authoritative source for raw agent diagnosis and host-native context.

## Phase 3 — governed-response bridge in an authorized lab

Do **not** connect PhantomNet directly to Wazuh’s `/active-response` API endpoint as a first production step. Wazuh’s API can authenticate via JWT and can send an Active Response command to selected agents.[3] A successful API response means a command was sent; it is not by itself independent evidence that the endpoint’s network or host state changed.

Instead, build a narrow bridge with these boundaries:

| Control | Required implementation |
|---|---|
| Adapter scope | One allow-listed command on lab agents only, such as collecting a read-only diagnostic. Do not start with host isolation. |
| Authorization | A dedicated Wazuh API service account with the least privileges needed for the selected route and agent group. No broad Wazuh administrator credentials in PhantomNet. |
| PhantomNet gate | A containment request is created first; a human with the required approval capability approves it; HMAC audit evidence is written before dispatch. |
| Target binding | Map PhantomNet asset ID to a Wazuh agent ID through a tenant-scoped, reviewed inventory binding. Refuse ambiguous or stale mappings. |
| Verification | Independently observe the desired state via a later telemetry report, a read-only query, or a provider API—not merely the “command sent” result. |
| Rollback | Use a separately authorized, tested reversal command; record reversal verification and audit evidence. |
| Failure policy | If audit signing, approval, target binding, dispatch, or verification fails, the request remains failed or pending; it must not be reported as enforced. |

This phase is complete only after a lab scenario proves the full lifecycle: **request → approval → auditable dispatch → independently observed result → rollback → independently observed restoration**. The existing PhantomNet Linux adapter intentionally fails closed for unsupported host isolation; do not replace this behavior with a simulated success. [Production-Readiness Validation](PRODUCTION_READINESS_VALIDATION.md)

## Phase 4 — controlled production expansion

Expand by Wazuh agent group, one telemetry class at a time. Keep a defined soak period after each increase. Recommended progression:

| Order | Production capability | Condition to enable |
|---|---|---|
| 1 | Read-only alert forwarding | Pilot exit criteria are met and the operations team can replay/recover batches. |
| 2 | Asset and integrity evidence | Identity/hostname collisions and tenant mapping are understood. |
| 3 | Cases and analyst playbooks | Analysts use PhantomNet for triage without losing Wazuh raw-event access. |
| 4 | Read-only Wazuh API enrichment | Dedicated scoped credential, API audit logs, throttling, and failure handling are validated. |
| 5 | One low-impact governed action | Authorized lab proof is repeated in a limited production group with a tested reversal. |
| 6 | High-impact containment | Only after a documented change review, independent verification, rollback exercise, and explicit owner approval. |

## Operational monitoring

Monitor the bridge as a security-critical data pipeline.

| Signal | Alert condition | First action |
|---|---|---|
| Forwarder authentication failures | Any sustained `401`, unexpected token prefix, or unauthorized source | Revoke and rotate the forwarder token; inspect source logs. |
| Replay or sequence conflict | Any `409` caused by duplicate/incorrect sequence | Stop the sidecar; reconcile its persisted checkpoint with PhantomNet’s `last_sequence`. |
| Ingestion lag | Wazuh event timestamp exceeds the agreed telemetry SLO | Check sidecar queue, PhantomNet broker, and endpoint-inventory service health. |
| Tenant mismatch or mapping ambiguity | Any asset binding collision | Quarantine the batch and require manual mapping approval. |
| Wazuh API errors | 401/403/429 or unexpected response volume | Disable the enrichment/bridge path; preserve telemetry forwarding. |
| Containment verification failure | Command sent but state cannot be independently observed | Mark the request failed; trigger rollback only if its safety conditions are met; open a case. |

## Rollback procedure

Rollback must restore a known safe **integration state**, not delete evidence.

1. Disable the sidecar’s outbound stream worker or remove its egress route.
2. Revoke the affected PhantomNet forwarder using the tenant-scoped forwarder endpoint. A revoked forwarder cannot ingest more batches.
3. Leave Wazuh agents, manager rules, indexer data, and dashboard configuration unchanged unless the Wazuh owner separately approves a Wazuh rollback.
4. If an API enrichment or response bridge exists, disable its credential and revoke its Wazuh JWT/session. Do not reuse an emergency administrator token.
5. Keep PhantomNet cases, canonical events, forwarder-batch records, and audit records for investigation and reconciliation.
6. Re-enable only after identifying root cause, rotating compromised secrets if applicable, and passing the pilot acceptance tests again.

## Delivery checklist

| Deliverable | Owner | Required before next phase |
|---|---|---|
| Tenant and agent-group inventory | Wazuh operator | Phase 1 |
| Sidecar source, SBOM, deployment manifest, and secret references | Platform engineer | Phase 1 |
| Versioned mapping table and sample event corpus | Detection engineer | Phase 2 |
| Replay/sequence/token negative tests | Platform engineer | Phase 1 |
| Case-playbook exercises with Wazuh alert IDs | SOC lead | Phase 2 |
| Authorized lab report for any response bridge | Security engineering + approver | Phase 3 |
| Docker-host topology and recovery evidence | Platform operations | Before broad production expansion |

## What this guide does not claim

This guide does **not** claim that PhantomNet currently replaces Wazuh, ships a complete Wazuh manager plugin, provides a validated production EDR integration, or has proven live Docker topology on this sandbox. It supplies the safest route to combine the systems while preserving Wazuh’s endpoint strengths and PhantomNet’s governance model.

## References

[1]: https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/index.html "Wazuh agent enrollment"
[2]: https://documentation.wazuh.com/current/user-manual/capabilities/active-response/index.html "Wazuh Active Response"
[3]: https://documentation.wazuh.com/current/user-manual/api/reference.html "Wazuh REST API reference"
