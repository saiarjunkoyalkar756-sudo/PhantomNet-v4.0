# Wazuh Governed Response Bridge — Phase 2 Design

**Status:** Implementation design. The bridge is disabled by default and is not activated by the Phase 1 telemetry pilot.

## Objective

Phase 2 permits PhantomNet to request a **named Wazuh Active Response command** only after a separately recorded PhantomNet approval. The Wazuh API confirms that a command was sent to selected agents, but that acknowledgement is not evidence of endpoint enforcement. PhantomNet therefore records an execution as verified only when it receives a fresh, signed endpoint receipt that is bound to the same tenant, request, approval, target asset, command, and intended postcondition.[1]

> **Design rule:** A command accepted by Wazuh is a dispatch acknowledgement. It is not containment proof. A missing, stale, unsigned, replayed, mismatched, or ambiguous endpoint receipt produces a failed containment execution.

## Security invariants

| Invariant | Required control |
|---|---|
| Human authorization | The canonical `ContainmentRequest` remains `requires_approval=true` and `automatic_enforcement=false`; execution requires a durable approved `ContainmentApproval`. |
| Explicit scope | The bridge accepts only `isolate_endpoint` and rollback-derived `release_endpoint`, only for tenant-to-Wazuh-agent mappings preconfigured by the operator. |
| Disabled default | `PHANTOMNET_WAZUH_RESPONSE_ENABLED` defaults to `false`. Any malformed configuration disables the bridge. |
| Least privilege | The Wazuh service account is restricted to Active Response dispatch for the dedicated named command and to agent-read status needed for verification routing. It cannot edit Wazuh rules, groups, users, or manager configuration. |
| Transport authentication | PhantomNet obtains a short-lived Wazuh API JWT through a TLS-protected service identity. Long-lived Wazuh credentials and callback HMAC keys are environment-managed secrets only. |
| Command binding | The request binds tenant ID, request ID, approval ID, asset ID, Wazuh agent ID, action, target, and a SHA-256 command fingerprint. The bridge never accepts free-form commands or arbitrary arguments. |
| Verification | A signed receipt reports the action, endpoint state, Wazuh agent ID, monotonic nonce, request/approval IDs, command fingerprint, and a UTC observation time inside the configured freshness window. |
| Replay resistance | Receipt IDs and nonces are unique per tenant; a signature check alone is insufficient. A receipt may be used once and must correspond to the pending execution. |
| Failure handling | Network errors, non-200 Wazuh responses, nonzero Wazuh failed items, unavailable callback evidence, verification mismatch, or rollback ambiguity all return `enforced=false`, `verified=false`. |
| Audit integrity | The governed containment service writes HMAC-signed chain entries for request, approval, Wazuh dispatch result, endpoint receipt, verification result, and rollback. |

## Supported action contract

The Wazuh REST API documents `PUT /active-response` with an authenticated JWT, a named command, arguments, alert context, and an explicit `agents_list`. Its direct response reports command delivery to agents; it does not replace the endpoint receipt described above.[1]

| PhantomNet action | Wazuh named command | Required postcondition | Rollback |
|---|---|---|---|
| `isolate_endpoint` | `!phantomnet-network-isolate` | Receipt reports `network_state="isolated"` and the exact approved command fingerprint. | `release_endpoint` |
| `release_endpoint` | `!phantomnet-network-release` | Receipt reports `network_state="released"` and the exact rollback command fingerprint. | No further automatic action. |

The bridge submits a single agent ID for each request. It rejects wildcard, group-wide, or `all` targeting. An operator-installed Wazuh Active Response script may perform local host isolation only after validating the received, PhantomNet-signed command envelope. That script must preserve an approved management path, emit an endpoint receipt, and support the named release action. The script is deployed only in an explicitly allow-listed lab or production agent group after a separate change review.

## Component architecture

```text
PhantomNet case / approved request
          |
          v
GovernedContainmentService
  - verifies HMAC audit configuration
  - loads approved request and tenant scope
          |
          v
WazuhActiveResponseAdapter
  - validates fixed action and tenant-agent allowlist
  - obtains Wazuh JWT through injected provider
  - PUT /active-response for one agent
  - audits dispatch acknowledgement
          |
          v
Wazuh manager / custom Active Response script
  - receives only named isolate/release command
  - performs local response only if its signed envelope is valid
          |
          v
Signed endpoint receipt receiver
  - validates HMAC, nonce, time, tenant/request/approval/asset binding
  - persists immutable receipt and appends audit evidence
          |
          v
WazuhActiveResponseAdapter verifier
  - reads exact fresh receipt
  - reports verified only if expected postcondition matches
```

The Phase 1 Wazuh forwarder is intentionally **not** reused for response commands. Its token and API surface remain telemetry-only and continue to reject containment requests.

## Request parameters

`ContainmentRequest.parameters` for `isolate_endpoint` must exactly match this bounded structure:

```json
{
  "wazuh_agent_id": "007",
  "response_profile": "lab-network-isolation-v1",
  "management_cidr": "192.0.2.0/24",
  "verification_timeout_seconds": 90
}
```

The profile is an operator-owned, preinstalled Active Response configuration name, not a shell command. `management_cidr` is an approved management exception; it is not used to construct arbitrary endpoint firewall rules. The implementation validates the CIDR and profile allowlists, requires `asset_id == wazuh_agent_id`, and limits verification timeout to a bounded value.

## Receipt contract

The endpoint script submits the following canonical receipt to a dedicated PhantomNet callback route over TLS:

```json
{
  "receipt_id": "uuid",
  "tenant_id": "uuid",
  "request_id": "uuid",
  "approval_id": "uuid",
  "asset_id": "007",
  "wazuh_agent_id": "007",
  "action": "isolate_endpoint",
  "network_state": "isolated",
  "command_fingerprint": "sha256-hex",
  "nonce": "uuid-or-opaque-unique-value",
  "observed_at": "2026-08-19T10:00:00Z",
  "signature_key_id": "wazuh-lab-key-1",
  "signature": "hex-hmac"
}
```

The HMAC covers canonical JSON excluding `signature`. PhantomNet stores only evidence and the signature metadata; it never accepts a callback that can create an approval, alter an allowlist, or request another action.

## Lifecycle and recovery

| Stage | Success criterion | Failure result |
|---|---|---|
| Proposal | Signed-audit configuration exists; canonical request is durable. | Request creation rejected. |
| Approval | Separate approved record exists for the same tenant/request. | Dispatch blocked. |
| Dispatch | Wazuh API accepts the one allowed named command for the one mapped active agent. | Failed execution, with dispatch evidence. |
| Verification | Fresh unique signed receipt has exact ID/fingerprint/state bindings. | Failed execution; no verified-success claim. |
| Rollback | A separately approved rollback path invokes the fixed release command and receives a fresh matching `released` receipt. | Failed rollback; operator escalation required. |
| Recovery | Wazuh/PhantomNet outage preserves requests and receipts; retries reuse the same idempotency binding and never issue a second action after a verified receipt. | No automatic retry after ambiguous dispatch without operator review. |

## Deployment boundary

This bridge needs a durable process and access to the Wazuh manager API plus an endpoint callback receiver. It should be deployed in the operator’s Wazuh/PhantomNet environment, not in the ephemeral validation sandbox. A local or self-hosted Docker/VM deployment is suitable when it provides TLS, firewall policy, a persistent database, durable audit secrets, and operational ownership. The default Phase 2 state remains disabled until an operator fills the allowlists, response profile, API credential, callback keys, and lab-test evidence.

## Acceptance gates

The implementation is not considered ready for activation until all of the following pass:

1. Disabled, malformed, unallowlisted, unapproved, non-tenant-matching, and wildcard target requests fail closed.
2. A mock Wazuh response with failed items cannot become verified evidence.
3. A Wazuh dispatch acknowledgement without a signed endpoint receipt remains failed.
4. A stale, replayed, wrong-tenant, wrong-asset, wrong-command, wrong-state, or bad-signature receipt is rejected.
5. A valid isolate receipt creates verified evidence and makes rollback available.
6. A valid release receipt updates the same execution to `rolled_back` and adds a signed audit-chain record.
7. The full response lifecycle remains isolated by tenant and survives injected API/callback failure without reporting false success.

## Reference

[1]: https://documentation.wazuh.com/current/user-manual/api/reference.html "Wazuh REST API — Active Response"
