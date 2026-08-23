# Controlled External-Lab Validation Protocol

## Purpose and boundary

This protocol converts implementation claims into **repeatable, non-production proof gates**. It is designed for an operator-controlled lab only. No procedure authorizes testing on a production tenant, a third-party system, a customer endpoint, an unrestricted cloud account, or a public target.

> **Stop immediately** if a proposed target, credential, IP range, account, endpoint, or data source is not explicitly owned and approved for the lab exercise. A failed preflight is a valid result; bypassing it is not.

The protocol supplements isolated regression evidence. It does not replace code review, threat modeling, third-party assessment, legal approval, incident-management policy, or operator responsibility.

## Evidence standard

Every gate must retain a small, secret-free evidence bundle. Do not place API keys, JWTs, session cookies, endpoint private keys, full hostnames, customer identifiers, raw production telemetry, personal data, or sensitive command output in the bundle.

| Field | Required content |
|---|---|
| Run identifier | Human-readable unique identifier such as `lab-wazuh-2026-08-20-01`. |
| Code identity | Git commit SHA, branch, migration head, and rendered Compose digest or image tags. |
| Scope | Gate name, approved lab assets, owner, approval reference, and explicit statement that no production target was used. |
| Configuration posture | Adapter enablement flags, safe-mode status, allowlist/profile count, and secret **identifiers only**. |
| Inputs | Synthetic fixture hashes, test-rule identifiers, test security-group rule ID aliases, and expected lifecycle transitions. |
| Observations | Health/readiness status, request/receipt/case/evidence IDs, timing summary, metrics snapshot, and pass/fail assertions. |
| Recovery and cleanup | Rollback status, destroyed test resources, deleted ephemeral credentials, and retained backup/restore artifacts. |
| Limits | Any failed precondition, unexpected behavior, skipped step, or conclusion that cannot be supported by the run. |

An evidence bundle must say **what was not tested**. For example, a mock Wazuh receipt proves signed receipt handling, not a live Wazuh manager; source compilation proves Python syntax, not Android device runtime.

## Gate 0: lab preflight

| Check | Required result | Stop condition |
|---|---|---|
| Ownership | The operator can identify the owner and approval for every host, account, endpoint, and network. | Any unknown or shared-production asset. |
| Credentials | Lab-only, least-privilege, revocable credentials are available. | Production or reused credential. |
| Network | Lab network has an explicit egress policy and an operator recovery path. | Public or uncontrolled target is reachable from the planned test. |
| Data | All events, logs, and fixtures are synthetic or expressly approved lab data. | Customer, sensitive, or unexplained data enters the test. |
| Response | Endpoint, Wazuh, AWS, and other adapters are disabled until the specific gate enables exactly one reviewed path. | More than one response authority is active or target scope is broader than expected. |
| Recovery | Backup, restore, and emergency release procedures have an owner and a tested communication path. | No rollback or resource cleanup path. |

## Gate 1: self-hosted topology and observability

### Objective

Prove that the Phase 7 reference topology starts on a controlled Docker host, has only the documented ingress, becomes ready only when dependencies are ready, and exposes bounded internal metrics.

### Procedure

1. Complete `docs/lab-evidence/GATE1_TOPOLOGY_EVIDENCE_TEMPLATE.md` with a run identifier, lab scope declaration, and no-response-adapter confirmation before starting the topology.
2. Copy `deploy/self-hosted/env/.env.example` to a protected lab-only environment file and provide fresh non-production values.
3. Render the topology with `docker compose ... config`; retain only a secret-redacted digest or sanitized output.
4. Start the reference topology. Record image tags, volume names, service health state, and the resolved gateway/Prometheus loopback bindings.
5. Confirm PostgreSQL, Redis, Redpanda, and Neo4j have no host-published ports. Confirm the gateway and Prometheus are loopback-only or sit behind a lab-controlled TLS boundary.
6. Request `/health`, `/ready`, and `/metrics` from the controlled host. Confirm readiness fails before a required dependency is ready and recovers only after it is healthy.
7. Confirm Prometheus scrapes only the internal gateway target and that no metric label contains tenant, user, event, case, raw request body, credential, or exception text.
8. Stop and restart the topology. Confirm persistent volumes behave according to the documented recovery plan and record results in the Gate 1 template.

### Pass criteria

The topology is healthy, ingress matches the architecture, readiness is dependency-aware, metrics remain bounded and secret-free, and no response adapter was enabled.

## Gate 2: backup, restore, and audit-chain recovery

### Objective

Demonstrate durable recovery rather than a simple restart.

### Procedure

1. Start with an empty lab topology and generate only approved synthetic events and a governed containment dry-run record.
2. Take operator-approved backups of PostgreSQL, Redpanda state or export, Neo4j, Redis according to the deployment decision, and audit key identifiers.
3. Record the current audit-chain verification result.
4. Rebuild a blank lab instance from backups or restore the documented durable stores.
5. Verify intended rows, replay behavior, and the tenant audit-chain result after restore. Do not reuse production key material.
6. Record elapsed recovery steps so the operator can set realistic RPO/RTO targets. Do not claim generic RPO/RTO values from one lab result.
7. Destroy the temporary topology or restore it to an agreed clean baseline.

### Pass criteria

The operator can show backup provenance, successful restore to an isolated environment, expected data integrity, and a verified audit chain. Any component that is intentionally disposable must be explicitly declared disposable.

## Gate 3: safe incident workflow and BAS fixtures

### Objective

Prove the canonical analyst workflow without running an uncontrolled attack.

### Procedure

1. Use the repository’s BAS fixtures, synthetic telemetry, or a lab honeypot owned by the operator. Do not use real malware, credential theft, credential spraying against unapproved services, exploit frameworks, persistence techniques, or lateral movement.
2. Select one or more named fixtures from the controlled BAS corpus and complete `docs/lab-evidence/GATE3_BAS_EVIDENCE_TEMPLATE.md` before submitting them through the canonical ingestion path. The template records the eight current fixture/rule/MITRE expectations and explicitly excludes command execution.
3. Record each normalized event identifier, detection evidence, MITRE mapping, alert, and case identifiers.
4. Use the analyst workflow to inspect evidence, decision trace, and priority factors.
5. If response is part of the gate, create a containment request and record the required human approval. Use a mock adapter or an isolated endpoint only.
6. Verify the expected audit-chain entry, adapter verification state, and governed rollback receipt.

### Pass criteria

The run shows fixture → canonical event → detection → alert → case → analyst trace → explicit approval → verified action or safe simulation → rollback. The evidence bundle uses the Gate 3 template, includes the selected fixture digest and expected MITRE mappings, and records any detection miss or false positive rather than filtering it from the evidence.

## Gate 4: Wazuh manager and endpoint bridge

### Objective

Validate the staged Wazuh bridge against a live **lab** manager and allowlisted lab endpoint.

### Procedure

1. Deploy a lab Wazuh manager and one test endpoint. Record versions, configuration digest, local operator identity, and allowlisted Wazuh agent ID without exposing credentials.
2. Start with telemetry-only forwarding. Validate tenant-bound asset and integrity evidence before enabling response.
3. Run the Phase 6 preflight. It must show correct local scope, response profile, receipt requirement, and signed-audit readiness without sending a command.
4. Enable only the named response bridge with lab keys and the one reviewed profile. Record the configuration posture, not key values.
5. Create and approve one request for an explicitly harmless lab isolation or release exercise. Observe the Wazuh acknowledgement and signed endpoint receipt.
6. Attempt one negative case: an expired, wrong-tenant, replayed, unsigned, or mismatched receipt. The platform must fail closed and record no verified execution.
7. Run governed release and retain receipt, audit-chain, and endpoint connectivity evidence.

### Pass criteria

Wazuh telemetry provenance is visible; bridge scope is tenant/agent/profile bound; only approved commands execute; signed receipts bind to the request; replay is rejected; and release is independently verified.

## Gate 5: AWS Security Group sandbox

### Objective

Validate the AWS adapter only in a dedicated sandbox account and only against one reviewed test rule.

### Procedure

1. Use a sandbox account with a purpose-built IAM role scoped to the named test security group and exact rule action. Record the policy digest, role ARN alias, and account alias—not long-lived credentials.
2. Create a single harmless inbound or egress test rule with a documented rollback baseline. Do not use a shared or production security group.
3. Run the local Phase 6 preflight and prove that it does not construct a cloud client or perform a cloud call.
4. Create and approve one containment request. Record the AWS identity evidence, rule read-back, CloudTrail event identifiers, and HMAC audit identifiers.
5. Run governed rollback. Record exact rule restoration and CloudTrail evidence.
6. Attempt a denied operation outside the configured allowlist. The adapter must fail closed without changing the out-of-scope rule.
7. Tear down test infrastructure, revoke temporary role sessions, and retain only redacted evidence.

### Pass criteria

The adapter proves least privilege, exact rule targeting, identity/read-back verification, CloudTrail traceability, verified rollback, and failure outside scope.

## Gate 6: agent packaging and resource footprint

### Objective

Move beyond source compilation without generalizing from one device.

### Procedure

1. Use approved Linux, Windows, and Android/Termux lab devices. Record OS version, architecture, install method, and available capability class.
2. Complete `docs/lab-evidence/GATE6_SIGNED_TELEMETRY_EVIDENCE_TEMPLATE.md` with the approved lab scope, key-handling boundary, and no-response-authority declaration.
3. Build or package the agent for the intended platform. Record artifact checksum and source commit.
4. Install with the least required privilege. Provision a tenant-bound public telemetry key through the governed credential API; record only the key fingerprint and metadata. Validate valid signature acceptance, altered-body rejection, durable nonce replay rejection, and post-revocation rejection before recording start/stop behavior, telemetry route, identity enrollment behavior, and clean uninstall behavior.
5. Collect CPU, memory, network, and—where relevant—battery observations for a defined idle and synthetic-workload interval. Do not claim a universal footprint from a single device.
6. Record any eBPF or native-capture fallback explicitly. A simulator fallback is a different evidence class from a native collector.
7. Revoke lab credentials, delete temporary agent state, and retain only secret-free evidence after the run.

### Pass criteria

Each result is tied to one real device profile and workload, states enabled versus fallback capability, and includes artifact identity plus cleanup proof.

## Gate 7: throughput and latency benchmark

### Objective

Produce a reproducible performance statement rather than a vague real-time claim.

### Procedure

1. Define a synthetic, non-sensitive event corpus and publish its schema, count, size distribution, source mix, and hash.
2. Record host hardware, operating system, CPU/memory limits, image tags, database/broker topology, cache state, and concurrency.
3. Run a warm-up followed by at least one measured interval. Record accepted, processed, detected, failed, dropped, and retried event counts.
4. Report p50, p95, and p99 latency with the measurement boundary stated clearly—for example, ingestion accepted to durable detection record.
5. Capture resource metrics and error logs without sensitive payloads.
6. Repeat enough times to report variation. Do not compare results to commercial products without equivalent workload and topology methodology.

### Pass criteria

The evidence contains workload, environment, success/error rate, latency distribution, resource profile, and limitations. A benchmark may support only the scope it measured.

## Stop and cleanup rules

Stop a gate on unexpected scope expansion, unexplained outbound traffic, a production credential, an unknown asset, an inability to roll back, a cross-tenant record, a missing audit record, a signature validation anomaly, or suspected exposure of sensitive data. Preserve the minimum redacted evidence needed for investigation, rotate lab credentials, tear down resources, and record the failure as a test result.

A gate is complete only when the expected proof and cleanup evidence are both present. A gate that is skipped, fails, or is partially executed must remain classified as incomplete.
