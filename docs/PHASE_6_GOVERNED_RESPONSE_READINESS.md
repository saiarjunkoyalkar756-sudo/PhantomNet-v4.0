# Phase 6: Governed Response Readiness

## Objective

Phase 6 makes the existing governed response lifecycle safer to operate. It adds a **read-only readiness checkpoint** between a proposed containment request and execution, while strengthening the invariant that no high-impact containment request may exist without configured HMAC-signed audit capability.

> **Phase 6 does not automate containment.** The lifecycle remains: request → human approval → preflight → explicit execution → adapter verification → governed rollback → HMAC audit-chain verification. A readiness result has no authority to dispatch, approve, mutate a request, contact an external provider, or bypass an existing approval requirement.

## Core objectives and deliverables

| Objective | Phase 6 deliverable | Security result |
|---|---|---|
| Signed audit at request time | `GovernedContainmentService.request()` now requires containment HMAC key and key ID before persisting a high-impact request. | Unsigned requests fail closed before approval or adapter routing can occur. |
| Side-effect-free readiness | `GovernedContainmentService.preflight()` provides tenant-scoped request, approval, audit, adapter, execution, and rollback readiness. | Operators can find blockers before execution without creating audit noise or triggering an external call. |
| Consistent adapter scope checks | Endpoint, AWS Security Group, and Wazuh adapters implement local preflight checks through the deterministic adapter router. | The same canonical action routing selects the same adapter for preflight and execution. |
| Least-privilege validation | Preflight checks only declared local configuration, exact request shape, allowlists, target binding, and prospective rollback semantics. | It never constructs an AWS client, authenticates to Wazuh, contacts an endpoint dispatcher, or discovers a new target. |
| Explicit verification expectations | Every adapter preflight reports its verification mode. | Operators know before execution whether verification needs dispatcher evidence, AWS read-back, or a fresh signed endpoint receipt. |
| Rollback readiness | Preflight distinguishes prospective rollback availability from actual rollback readiness after verified execution. | Rollback remains impossible until a verified execution records rollback evidence. |
| Wazuh readiness posture | Runtime posture reports Wazuh Active Response as disabled, not ready, ready, or isolated-lab degraded without exposing credentials or HMAC material. | Production and staging require HTTPS, signed audit, credentials, command HMAC, tenant-agent allowlists, and response-profile allowlists. |

## Readiness flow

```text
Approved containment request
          │
          ▼
  Read-only Phase 6 preflight
          │
          ├── HMAC audit configured?
          ├── Human approval recorded?
          ├── Exact local adapter scope allowlisted?
          ├── Existing execution already recorded?
          └── Verification and rollback expectations visible?
          │
          ▼
eligible_to_execute = true only when every required condition holds
          │
          ▼
Explicit operator execution request
          │
          ▼
Live adapter verification and HMAC audit evidence
          │
          ▼
rollback_ready = true only after verified execution with rollback evidence
```

Preflight is intentionally local and bounded. It can prove that a request is structurally eligible, but it cannot prove the live target’s state. Live assertions remain at execution time: AWS verifies caller identity and the precise security-group rule by read-back; Wazuh requires an exact, fresh HMAC-signed endpoint receipt after command acknowledgement; endpoint adapters require verified dispatcher evidence.

## Adapter readiness contract

| Adapter | Preflight validates | Live verification remains at execution | Prospective rollback |
|---|---|---|---|
| Endpoint containment | Adapter enabled, tenant and asset allowlists, approved action type, dispatcher configured. | Dispatcher returns enforcement and verification evidence. | Available for `isolate_endpoint` only. |
| AWS Security Group | Adapter enabled, request structure, target/security-group binding, tenant group, region, and CIDR allowlists. | STS account allowlist, exact ingress-rule precondition, revoke result, and postcondition read-back. | Available when the reviewed revoke path is eligible. |
| Wazuh Active Response | Adapter configuration, HTTPS or explicit isolated-lab HTTP, credentials, command HMAC, tenant-agent allowlist, profile allowlist, and target binding. | Exact Wazuh acknowledgement plus fresh endpoint receipt signed and bound to tenant, request, approval, agent, action, state, and command fingerprint. | Available for verified endpoint isolation only. |

## Preflight response semantics

`GET /governed-containment/requests/{request_id}/preflight` requires `response:approve` and returns a tenant-owned, non-secret record with the following fields.

| Field | Meaning |
|---|---|
| `audit_ready` | Both containment audit key and key ID are configured; no key value is returned. |
| `request_status` / `approval_status` | Current persisted workflow state. |
| `adapter` | Selected provider, local eligibility, non-secret detail, verification mode, prospective rollback availability, and `external_calls=false`. |
| `eligible_to_execute` | True only for an approved, unexecuted request with ready audit capability and an eligible adapter preflight. |
| `execution_status` | `not_executed` or the durable execution status. |
| `rollback_ready` | True only after a verified execution has durable rollback availability and has not already been rolled back. |
| `execution_blockers` | A bounded list including missing audit, missing approval, ineligible adapter preflight, or an existing execution. |

The endpoint is read-only. It cannot approve, execute, rollback, submit a Wazuh receipt, create a request, modify a case, or call an adapter provider.

## Wazuh runtime posture

The standard runtime posture adds `wazuh_active_response`. It returns only state and counts; it never returns API credentials, endpoint URLs, HMAC values, or token material.

| State | Meaning |
|---|---|
| `disabled` | The adapter is intentionally disabled by default. |
| `not_ready` | One or more required audit, HTTPS, credential, command-HMAC, tenant-agent, or profile controls are missing or unsafe. |
| `ready` | HTTPS transport and all non-secret readiness prerequisites are configured. |
| `degraded` | HTTP is explicitly allowed only for an isolated non-strict lab; production and staging fail closed. |

## Operator sequence

1. Confirm platform readiness and that the required response adapter is intentionally enabled for a non-production or reviewed scope.
2. Create an approval-bound containment request. If signed audit material is not configured, request creation returns service unavailable and persists nothing.
3. Review preflight output. Resolve each `execution_blocker`; do not treat a structurally eligible preflight as evidence that a live action has occurred.
4. Obtain and record human approval through the governed approval endpoint.
5. Re-run preflight to confirm `eligible_to_execute=true` and inspect the adapter’s verification and rollback requirements.
6. Execute explicitly through the existing approval-gated execution endpoint.
7. Review adapter verification evidence and HMAC audit chain. For Wazuh, an API acknowledgement alone is insufficient; wait for the fresh signed endpoint receipt.
8. Use rollback only when `rollback_ready=true`, then verify the rollback result and re-check the audit chain.

## Validation

Phase 6 focused tests prove that preflight does not invoke endpoint dispatch, construct AWS clients, authenticate to Wazuh, or call a Wazuh command transport. They also prove request-time signed-audit gating, approval-dependent execution readiness, verified-execution rollback readiness, secret-safe Wazuh posture, and the absence of dispatch operations on the preflight route.

```bash
python3 -m pytest -q -p no:cacheprovider \
  tests/test_governed_response_preflight.py \
  tests/test_governed_containment.py \
  tests/test_aws_security_group_containment.py \
  tests/test_wazuh_active_response_bridge.py \
  tests/test_runtime_posture.py
```

Run all quality gates before release:

```bash
python3 -m pytest -q -p no:cacheprovider
cd dashboard_frontend && npm run lint && npm run build
cd ../phantomnet-website && npm run lint && npm run build
```

## Explicit limits

Phase 6 adds readiness, not new autonomous response. It does not enable a disabled adapter, rotate secrets, make a live cloud call, contact Wazuh during preflight, test a production endpoint, replace the external-lab deployment gate, or permit any AI, enrichment, graph, BAS, dashboard, or hunt result to execute containment independently.
