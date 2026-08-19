# Wazuh Governed-Response Operational Dry-Run

## Purpose and safety boundary

This runbook validates the **governed decision and evidence path** for a representative Wazuh alert: a synthetic alert creates a containment request, a human approval is recorded, the Wazuh Active Response bridge dispatches an allow-listed isolate command, a signed endpoint receipt verifies execution, and a governed release command completes rollback.

> **This is an operational dry-run, not an endpoint-control test.** Neither path contacts a Wazuh manager, contacts an endpoint, opens an outbound connection, changes firewall rules, or accepts production credentials. It is safe only because all Wazuh acknowledgements and endpoint receipts are deliberately simulated within the runner.

| Path | Command | Dependencies | Evidence | Intended use |
|---|---|---|---|---|
| Isolated | `python3 scripts/run_wazuh_governed_response_dry_run.py` | Python dependencies only | Timestamped JSON in `artifacts/` | Fast, repeatable validation of application security logic. |
| Docker-host | `./scripts/run_docker_wazuh_governed_response_dry_run.sh` | Docker Engine and Compose v2 | Isolated timestamped evidence directory and container log | Reproves the identical dry-run in a disposable, hardened container. |

## What the dry-run exercises

The runner uses the production application services against a new in-memory SQLite database. It instantiates the real `GovernedContainmentService`, `WazuhActiveResponseContainmentAdapter`, `WazuhResponseReceiptService`, and audit-chain verifier. Three fresh, in-memory HMAC keys are generated for every invocation: one for containment auditing, one for command envelopes, and one for receipts. The values are neither read from nor written to artifacts.

| Lifecycle stage | Real component under test | Simulated boundary | Required evidence |
|---|---|---|---|
| Wazuh alert intake | `WazuhForwarderService` and endpoint inventory ingestion | Alert is constructed locally and streamed through a registered in-memory forwarder; no network forwarder is contacted. | Tenant-bound forwarder, ordered batch, asset creation, integrity evidence, canonical events, and no-automatic-enforcement marker. |
| Approval | `GovernedContainmentService.approve` | The named dry-run incident commander represents the human approver. | Approval ID bound to the tenant and request. |
| Isolate dispatch | `WazuhActiveResponseContainmentAdapter` | A local Wazuh client accepts only `!phantomnet-network-isolate` for agent `007`. | Signed command-envelope validation and acknowledgement. |
| Execution verification | `WazuhResponseReceiptService` | A local endpoint verifier signs a receipt after dispatch. | Tenant, request, approval, asset, command fingerprint, nonce, action, and network state binding. |
| Rollback | `GovernedContainmentService.rollback` and bridge adapter | The simulated Wazuh client accepts only `!phantomnet-network-release`. | A separate signed `released` receipt. |
| Audit review | `verify_chain` | None. | Every audit record’s hash link and HMAC signature are verified. |

The request uses the constrained laboratory bridge parameters shown below. It intentionally requires approval and sets `automatic_enforcement` to `false`.

```text
wazuh_agent_id: 007
response_profile: lab-network-isolation-v1
management_cidr: 192.0.2.0/24
verification_timeout_seconds: 5
```

## Run the isolated path

From the repository root, activate the same Python environment used for the normal regression suite and run:

```bash
python3 scripts/run_wazuh_governed_response_dry_run.py
```

A successful invocation writes one artifact named `artifacts/wazuh_governed_response_dry_run_<UTC timestamp>.json` and prints a compact locator, for example:

```json
{"artifact":"artifacts/wazuh_governed_response_dry_run_20260819T120000Z.json","audit_chain_valid":true,"status":"passed"}
```

Set `PHANTOMNET_WAZUH_DRY_RUN_ARTIFACT_DIR` when evidence must be written outside the default repository `artifacts/` directory.

```bash
PHANTOMNET_WAZUH_DRY_RUN_ARTIFACT_DIR=/secure/lab-evidence \
  python3 scripts/run_wazuh_governed_response_dry_run.py
```

## Run the Docker-host path

Run this only on a Docker-capable laboratory host. The wrapper checks for Docker Engine and Compose v2 before it creates its timestamped Compose project.

```bash
chmod +x scripts/run_docker_wazuh_governed_response_dry_run.sh
./scripts/run_docker_wazuh_governed_response_dry_run.sh
```

The wrapper builds the repository’s integration-test image, launches one `governed-response-dry-run` container, mounts a unique local evidence directory, and removes the Compose project with its disposable resources on exit. The Compose manifest has an internal-only network, no published ports, a read-only root filesystem, a small `/tmp` tmpfs, no Linux capabilities, and `no-new-privileges` enabled.

> Do **not** set real Wazuh, endpoint, database, cloud, or production HMAC credentials for either path. The dry-run’s simulated components neither require nor use them.

## Interpret the evidence

The artifact includes the request and approval identifiers, both allow-listed Wazuh command names, two unique receipt IDs, lifecycle statuses, audit-record count, and a short safety declaration. Treat a result as valid only when all of the following hold.

| Field | Required result | Meaning |
|---|---|---|
| `status` | `passed` | The full simulated lifecycle completed without an adapter or verification failure. |
| `telemetry_evidence` | One ordered read-only batch with asset and integrity evidence | The synthetic Wazuh alert traversed the tenant-bound Phase 1 forwarder boundary before containment was proposed. |
| `execution_status` | `verified` | The isolate command had a matching valid receipt before execution was considered verified. |
| `rollback_status` | `rolled_back` | The separate release command and signed released receipt completed. |
| `wazuh_commands` | `!phantomnet-network-isolate`, then `!phantomnet-network-release` | Only the two explicit bridge commands were dispatched. |
| `receipt_ids` | Exactly two distinct IDs | Isolate and release have independent endpoint evidence. |
| `audit_chain_valid` | `true` | Every containment audit record is linked and HMAC-authenticated for that invocation. |
| `safety` | All four booleans are `false` | Confirms no external Wazuh, network, endpoint action, or automatic enforcement was used. |

A nonzero exit code, absent artifact, non-`verified` execution, non-`rolled_back` rollback, invalid audit chain, unexpected command, or receipt-count mismatch is a failure. Preserve the artifact and runner log, do not bypass the error, and investigate the bridge configuration or receipt binding before advancing to a real lab acceptance test.

## Limits and next validation step

This runbook proves application-level approval, dispatch construction, receipt validation, rollback state handling, and audit-chain correctness. It does **not** prove that a Wazuh manager can reach a Wazuh agent, that an endpoint-side verifier can alter a real network stack, or that an actual control is reversible. Those claims require the separately documented, disabled-by-default laboratory procedure in [Wazuh Governed Response Deployment](WAZUH_GOVERNED_RESPONSE_DEPLOYMENT.md), with a dedicated non-production agent, fresh environment-provided keys, explicit human approval, and a pre-approved emergency release procedure.
