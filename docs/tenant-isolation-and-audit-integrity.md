# Tenant Isolation and Audit Integrity Verification

## Purpose

This verification increment tests that governed evidence remains visible only to its owning tenant and that containment audit evidence remains tamper-evident and signed. It adds an application-level mutation guard for containment audit rows and a read-only verifier that recomputes each tenant’s persisted hash chain and HMAC signatures.

> Hash chaining and HMAC signatures provide **tamper evidence**, not absolute protection against a database superuser. Stronger immutability requires an independently controlled archive, immutable object storage, or external anchoring; the verifier intentionally reports invalid evidence rather than attempting to repair it.

## Cross-tenant verification matrix

| Evidence layer | Verified boundary | Expected cross-tenant behavior |
|---|---|---|
| Detections | `DetectionRepository.list_for_tenant` | Only the caller’s durable detection records are returned |
| Analyst alerts | `AlertWorkflow.list_for_tenant` | Only the caller’s linked analyst alerts are returned |
| Cases | `CaseWorkflow.get_case` and alert-to-case linkage | Foreign cases and alerts raise a tenant-scope lookup error |
| Governed correlation | Rule repository listing | Rules remain tenant-owned and are not returned for another tenant |
| Response proposals | Policy repository listing | Policy configuration stays tenant-owned |
| Regional replication | Targets and delivery receipts | Targets and receipts remain tenant-owned and event-hash-bound |
| Attack paths | Governed graph projection and analysis | Existing graph checks reject foreign nodes and evidence |
| Containment audit | Per-tenant ordered chain | Each tenant receives an independent genesis-to-tail chain |

The isolated harness provisions two tenants in one SQLite database and verifies both positive tenant access and negative foreign-tenant lookups. It also validates that no replication receipt for tenant A appears in tenant B’s list.

## Audit verification contract

`ContainmentAuditVerifier.verify_tenant()` reads only one tenant’s audit rows in insertion order and passes a normalized export to the existing hash-chain and HMAC verifier. It returns only tenant ID, record count, validity, signature requirement, and expected key ID. It does not return signing keys, modify records, retry actions, or repair malformed evidence.

The governed containment API exposes `GET /governed-containment/audit/verify` to users with `audit:read`. The route derives tenant scope from the authenticated user and requires configured HMAC verification material. Missing material produces an explicit unavailable response; an invalid chain is returned as a visible `valid: false` verification result for incident handling.

## Immutability controls

The containment audit ORM model now rejects application-level `UPDATE` and `DELETE` operations before commit. The verification harness checks both paths and then deliberately performs a lower-level SQL payload rewrite to prove that the independent chain verifier rejects tampered evidence. The lower-level tamper test is deliberate test-only proof that the verifier detects an attack that bypasses the application ORM guard.

## Operational follow-up

| Control | Current state | Production follow-up |
|---|---|---|
| Tenant-scoped application repositories | Verified by isolated multi-tenant tests | Retain tenant predicates in every new repository and API route |
| ORM audit row mutation guard | Implemented | Restrict database roles so application identities cannot issue direct audit-row updates or deletes |
| Hash-chain and HMAC verification | Implemented | Run scheduled external verification and alert on `valid: false` |
| Independent immutable archive | Not implemented | Export signed chain checkpoints to separately controlled immutable storage or an external ledger |
| Database superuser resistance | Not provided by application code | Apply separate administrator duties, restricted credentials, and immutable retention controls |
