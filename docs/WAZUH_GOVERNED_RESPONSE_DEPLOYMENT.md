# Wazuh Governed Response Bridge — Phase 2 Deployment

**Status:** Disabled-by-default implementation. This package is a controlled integration path, not permission to enable endpoint isolation globally.

The Phase 2 bridge allows PhantomNet to submit one approved, named Wazuh Active Response command to one allow-listed agent. It treats Wazuh’s API acknowledgement as **dispatch evidence only**. A containment execution is verified only after a fresh HMAC-signed endpoint receipt reports the exact approved state. Wazuh documents `PUT /active-response` as an authenticated command interface; the response indicates which agents accepted the request and does not establish a host firewall or network postcondition by itself.[1]

> **Do not enable this bridge until the complete lab acceptance test passes.** A configuration error, an unavailable Wazuh API, a callback failure, a stale receipt, a mismatched receipt, or a local executor that cannot prove endpoint state all fail closed.

## Delivered components

| Component | Location | Responsibility |
|---|---|---|
| Bridge adapter | `backend_api/soar_engine/wazuh_active_response_adapter.py` | Validates approval, action, scope, profile, HTTPS API identity, signed command envelope, Wazuh acknowledgement, and receipt evidence. |
| Receipt service | `backend_api/soar_engine/wazuh_response_receipts.py` | Validates HMAC receipts, time windows, tenant/request/approval/asset binding, and one-time nonces. |
| Callback route | `POST /governed-containment/wazuh/receipts` | Accepts only fresh, HMAC-authenticated endpoint evidence; it cannot create approvals or commands. |
| Database migration | `backend_api/alembic/versions/d4e7f1a9c2b5_add_wazuh_response_receipts.py` | Adds durable response receipts and tenant-scoped nonce replay protection. |
| Agent verifier | `deploy/wazuh-response/agent/phantomnet-network-response.py` | Validates the signed command envelope and requires an operator-reviewed local executor to prove state. |
| Agent command fragments | `deploy/wazuh-response/agent/` | Stages named isolate/release scripts without adding any rule-triggered automatic response. |
| Design record | `docs/WAZUH_GOVERNED_RESPONSE_BRIDGE.md` | Defines the trust model, data contracts, lifecycle, and acceptance criteria. |

## Non-negotiable operating model

| Control | Requirement |
|---|---|
| Approval | `isolate_endpoint` and `release_endpoint` require separate durable PhantomNet approval records. The bridge rejects automatic enforcement. |
| Scope | One approved request targets one numeric Wazuh agent ID. Wildcards, agent groups, and free-form Wazuh commands are not supported. |
| Actions | Only `!phantomnet-network-isolate` and `!phantomnet-network-release` are dispatched. |
| Transport | PhantomNet requires HTTPS for the Wazuh API and the receipt callback. A non-TLS URL is rejected except when an operator deliberately enables the explicit isolated-lab override. |
| Secrets | Wazuh API credentials, command HMAC keys, and receipt HMAC keys are environment-managed secrets. Never add them to `ossec.conf`, Compose files, source code, or Git. |
| Evidence | A Wazuh acknowledgement without an exact fresh signed receipt is a failed execution, not a partial success. |
| Audit | The governed execution and rollback audit records contain the full non-secret adapter verification evidence and are HMAC-chained. |

## Prerequisites

The operator must own or have explicit authorization for the Wazuh manager, the pilot agent group, and the PhantomNet environment. Use a dedicated non-production lab first. The manager API identity must be scoped to the dedicated Active Response operation and the selected pilot agents; it must not have authority to change Wazuh users, rules, groups, or manager configuration. Wazuh API authentication uses JWTs, so the bridge obtains a short-lived token with the service identity and does not persist that token.[1]

The deployment requires a persistent PhantomNet database with the new migration applied, a TLS path from PhantomNet to the Wazuh manager, and a TLS path from the selected agent to PhantomNet’s receipt route. The endpoint’s management network must be explicitly represented in both the request and the locally installed allowlist so a reviewed local executor can preserve it during isolation.

## PhantomNet bridge configuration

Create an environment file in the service’s secret-management mechanism. The values below are names and formats only; replace all placeholders outside version control.

```dotenv
# Disabled until every acceptance gate below has passed.
PHANTOMNET_WAZUH_RESPONSE_ENABLED=false

# Wazuh manager API; HTTPS is mandatory outside an isolated lab.
PHANTOMNET_WAZUH_RESPONSE_API_BASE_URL=https://wazuh-manager.example.internal:55000
PHANTOMNET_WAZUH_RESPONSE_API_USERNAME=phantomnet-response-bridge
PHANTOMNET_WAZUH_RESPONSE_API_PASSWORD=load-from-secret-store

# Command-envelope trust: shared only with the allow-listed endpoint response scripts.
PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY=load-from-secret-store
PHANTOMNET_WAZUH_RESPONSE_COMMAND_HMAC_KEY_ID=wazuh-command-key-1

# Endpoint receipt trust: shared only with the allow-listed endpoint response scripts.
PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY=load-from-secret-store
PHANTOMNET_WAZUH_RESPONSE_RECEIPT_HMAC_KEY_ID=wazuh-receipt-key-1
PHANTOMNET_WAZUH_RESPONSE_RECEIPT_MAX_AGE_SECONDS=300
PHANTOMNET_WAZUH_RESPONSE_RECEIPT_MAX_FUTURE_SECONDS=30

# Exact mapping from PhantomNet tenant UUID to pilot Wazuh agent IDs.
PHANTOMNET_WAZUH_RESPONSE_TENANT_AGENT_ALLOWLIST={"00000000-0000-0000-0000-000000000001":["007"]}
PHANTOMNET_WAZUH_RESPONSE_ALLOWED_PROFILES=lab-network-isolation-v1
PHANTOMNET_WAZUH_RESPONSE_REQUEST_TIMEOUT_SECONDS=10
PHANTOMNET_WAZUH_RESPONSE_RECEIPT_POLL_INTERVAL_SECONDS=0.5
```

The allowlist must contain only a small dedicated lab group. The bridge rejects a request when `target`, `asset_id`, and `parameters.wazuh_agent_id` do not all identify the same configured agent. The required request parameters are:

```json
{
  "wazuh_agent_id": "007",
  "response_profile": "lab-network-isolation-v1",
  "management_cidr": "192.0.2.0/24",
  "verification_timeout_seconds": 30
}
```

## Apply the database migration

Run the project’s normal Alembic deployment process before starting a bridge-enabled service. The migration adds only `wazuh_response_receipts`; it does not enable a response route or change any Wazuh host.

```bash
cd /opt/phantomnet/backend_api
alembic upgrade head
```

Confirm the application can read and write the table in the target environment before changing `PHANTOMNET_WAZUH_RESPONSE_ENABLED`.

## Stage the Wazuh agent scripts

Copy the contents of `deploy/wazuh-response/agent/` to an approved staging directory on the pilot agent. Create `/var/ossec/etc/phantomnet-response.env` from `phantomnet-response.env.example`, place real secrets in that file only, and apply `root:wazuh` ownership with mode `0640`.

Run the provided staging script as root:

```bash
sudo ./install-agent-response-bridge.sh
```

The installer stages the scripts and confirms prerequisites. It **does not** merge Wazuh configuration, restart the agent, enable local enforcement, or install a local firewall executor.

Review `ossec.command.fragment.xml` and merge only the two `<command>` definitions through the approved Wazuh agent or group configuration process. Do **not** add an `<active-response>` trigger block. Wazuh custom response scripts receive an alert message through standard input; the supplied verifier reads that input, requires the stateless `add` form, validates the signed envelope, and exits nonzero on any mismatch.[2]

The endpoint verifier calls `PHANTOMNET_WAZUH_RESPONSE_EXECUTOR` only when `PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED=true`. The executor is not supplied by PhantomNet because host-network isolation rules and management-path preservation must be reviewed for the endpoint’s operating system, management plane, and recovery policy. It must accept the documented bounded arguments and return JSON of this exact form only after an independent state check:

```json
{"verified": true, "network_state": "isolated"}
```

For release, it must return `{"verified": true, "network_state": "released"}`. Any other return, missing executable, nonzero exit status, timeout, or callback problem causes the script to fail and withhold a success receipt.

## Lab acceptance sequence

Complete the following sequence against one disposable, allow-listed Wazuh agent. Do not test against a production endpoint first.

1. Deploy the database migration and run PhantomNet with the bridge configuration still disabled.
2. Stage the endpoint verifier with local enforcement still disabled; verify a direct Wazuh invocation exits nonzero and does not alter network state.
3. Validate that a containment request without an approval fails. Validate that an approval for a different tenant or agent cannot be used.
4. Enable a lab-only local executor that independently proves isolate and release state while preserving the exact management CIDR. Test it outside the Wazuh route first.
5. Enable the endpoint’s local enforcement flag, but leave the PhantomNet bridge disabled. A Wazuh command without the valid signed envelope must fail and emit no receipt.
6. Enable `PHANTOMNET_WAZUH_RESPONSE_ENABLED=true` only for the lab service instance. Submit, approve, and execute one `isolate_endpoint` request.
7. Confirm the Wazuh API accepted exactly agent `007`; then confirm PhantomNet recorded a fresh signed receipt with `network_state="isolated"`, the correct command fingerprint, and a verified containment execution.
8. Approve and execute the governed rollback. Confirm the release command receives a distinct fresh signed receipt with `network_state="released"` and the execution becomes `rolled_back`.
9. Verify the tenant’s containment audit chain through `GET /governed-containment/audit/verify` with an `audit:read` user. Confirm the execution and rollback records contain the Wazuh command, receipt ID, and expected state.
10. Disable the bridge and local enforcement after the lab run; retain the signed audit evidence and operating logs for review.

## Failure injection and rollback

| Injected condition | Required outcome |
|---|---|
| Wazuh API credential failure, timeout, or malformed response | No verified action; a failed containment execution is recorded with dispatch failure evidence. |
| Wrong Wazuh agent acknowledgement or nonzero failed-items count | No verified action. |
| Missing receipt after Wazuh acknowledgement | No verified action and no rollback availability. |
| Stale, future-dated, replayed, wrong-tenant, wrong-approval, wrong-asset, wrong-fingerprint, or bad-signature receipt | Callback rejects the receipt or the verifier cannot find it; no verified action. |
| Local executor cannot independently prove state | Endpoint script exits nonzero and submits no receipt. |
| Rollback release receipt missing or invalid | Rollback remains failed; operator escalation is required. |

To stop the pilot immediately, set `PHANTOMNET_WAZUH_RESPONSE_ENABLED=false` and `PHANTOMNET_WAZUH_RESPONSE_LOCAL_ENFORCEMENT_ENABLED=false`, remove the Wazuh `<command>` definitions through the approved configuration process, and retain the secret files for incident evidence handling rather than deleting audit material. This does not automatically release an already isolated endpoint; use the separately approved governed release workflow or the established emergency recovery procedure.

## References

[1]: https://documentation.wazuh.com/current/user-manual/api/reference.html "Wazuh REST API reference — Active Response"
[2]: https://documentation.wazuh.com/current/user-manual/capabilities/active-response/custom-active-response-scripts.html "Wazuh custom Active Response scripts"
