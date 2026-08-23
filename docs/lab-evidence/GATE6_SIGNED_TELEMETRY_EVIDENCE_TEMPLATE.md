# Gate 6 — Signed Agent Telemetry Evidence Template

## Scope and safety declaration

| Field | Operator-recorded value |
|---|---|
| Run identifier | `<lab-signed-telemetry-run-id>` |
| Operator and approval reference | `<owner-and-approval-reference>` |
| Code identity | `<commit-sha>`, `<branch>`, `<migration-head>` |
| Device profile | `<approved-lab-device-os-and-architecture>` |
| Tenant and agent identifiers | `<sanitized-lab-tenant-and-agent-aliases>` |
| Credential authority | `<authenticated-governed-api-user-role-or-approval-reference>` |
| Private key retained in evidence | **No** — only a public-key fingerprint and key ID may be retained. |
| Production tenant, production credential, customer telemetry, or public endpoint used | **No** — stop and record a failed preflight if this cannot be truthfully stated. |

> This template records validation evidence for signed telemetry ingestion. It does not authorize endpoint control, containment, command dispatch, persistence, privilege escalation, credential access, or response automation.

## Credential lifecycle

| Check | Expected result | Sanitized observation |
|---|---|---|
| Provision | An `agents:approve` principal registers a tenant-scoped public key and returns only metadata | `<credential-id-key-id-public-key-fingerprint>` |
| Private-key posture | The device retains its private key locally; no private key crosses the governed API or evidence bundle | `<pass/fail>` |
| Credential listing | An `audit:read` principal sees metadata for its own tenant only, never PEM material | `<pass/fail>` |
| Tenant isolation | A principal from another lab tenant cannot list, revoke, or authenticate with the credential | `<pass/fail>` |
| Revocation | An `agents:approve` principal records one-way active-to-revoked transition | `<credential-id-revocation-time>` |
| Post-revocation | Further submissions signed by the revoked key are rejected before broker publication | `<pass/fail>` |

## Signed telemetry request observations

| Field | Sanitized value |
|---|---|
| Event body digest | `<sha256>` |
| Key ID | `<key-id>` |
| Signature algorithm | `RSA-PSS-SHA256` |
| Signed timestamp | `<UTC-timestamp>` |
| Nonce identifier | `<nonce-alias-or-fingerprint>` |
| Credential / agent / tenant binding | `<metadata-only>` |
| Valid request result | `<accepted-before-publication>` |
| Durable nonce record identifier | `<nonce-record-id>` |
| Broker topic alias and receipt | `<configured-topic-alias-and-sanitized-result>` |

## Required negative observations

| Case | Required result | Observation |
|---|---|---|
| Missing signature header | HTTP 403; producer is not initialized or used | `<pass/fail>` |
| Altered request body | HTTP 403; digest/signature mismatch | `<pass/fail>` |
| Reused nonce | HTTP 403; durable replay rejection | `<pass/fail>` |
| Stale or future timestamp | HTTP 403; bounded clock-window rejection | `<pass/fail>` |
| Wrong tenant / agent / key ID | HTTP 403; no matching active credential | `<pass/fail>` |
| Revoked key | HTTP 403; no broker publication | `<pass/fail>` |

## Cleanup and conclusion

Record private-key disposal or retained lab-device key posture, revoked credential state, deleted temporary fixtures, and any nonce/evidence retention decision. State precisely what the run proves and what it does not: a successful run can demonstrate signed telemetry authentication for the recorded device and lab configuration only. It does not prove endpoint efficacy, production identity management, real-world detection efficacy, Wazuh/AWS behavior, containment, or trained-model performance.
