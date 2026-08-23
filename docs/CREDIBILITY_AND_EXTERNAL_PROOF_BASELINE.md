# PhantomNet Credibility and External-Proof Baseline

## Purpose

This document is the project’s evidence-led response to legitimate questions about scope, production readiness, AI claims, response safety, deployment proof, and long-term operability. It replaces broad product language with four explicit evidence classes.

> **A claim is not treated as operational proof merely because it has code, documentation, or a passing isolated test.** The project distinguishes source evidence, controlled harness evidence, non-production external-lab evidence, and production evidence.

## Evidence taxonomy

| Class | Meaning | Examples |
|---|---|---|
| **A — Implemented and regression-covered** | Source-controlled code with deterministic isolated regression evidence. | Canonical contracts, governed correlation, evidence integration, evidence-grounded autonomous decision records, case and analyst workflow, signed containment lifecycle, audit-chain verification, Phase 7 Compose static contract. |
| **B — Controlled harness evidence** | Mocked, SQLite, LocalStack-gated, disposable Docker, or simulated endpoint proof. | Wazuh governed-response dry run, AWS adapter unit coverage, recovery harness, source-contract CI. |
| **C — Non-production external-lab proof required** | Requires a real but isolated dependency, account, host, device, manager, or operator. | Live Wazuh manager, AWS sandbox account, Docker-host topology, endpoint agent footprint, real proxy/TLS ingress, backup restore. |
| **D — Roadmap or intentionally unsupported** | Not currently represented as an operational capability. | Autonomous high-impact containment, self-healing infrastructure, predictive threat forecasting, distributed blockchain, post-quantum audit, independently evaluated AI models. |

## Claim ledger

| Area | Evidence class | Current evidence | Public positioning rule |
|---|---|---|---|
| Canonical telemetry, tenant-scoped evidence, governed correlation, MITRE mappings, analyst traces | A | Versioned contracts, durable projections, rule fixtures, evidence and analyst regressions. | Describe as implemented controls; do not promise universal source coverage or detection efficacy. |
| High-impact containment | A/B | Approval-bound request, HMAC audit, adapter routing, verification, rollback, receipt handling, and dry-run regressions. | State that adapters are disabled by default and require human approval plus adapter-specific verification. |
| Wazuh bridge | B/C | Read-only telemetry path, signed command envelope, signed endpoint receipt, isolated dry run, deployment runbook. | Describe as a staged integration; live Wazuh-manager and endpoint proof remains a lab gate. |
| AWS Security Group adapter | B/C | Narrow reviewed-rule revoke/restore semantics, read-back checks, LocalStack-gated integration harness. | Do not claim a live AWS action until an isolated account, IAM policy, CloudTrail evidence, and rollback proof exist. |
| Tamper-evident audit | A/B | Tenant-scoped HMAC-signed application hash chain and verification tests. | Use “tamper-evident audit chain”; do not call it a distributed blockchain, immutable ledger, proof of compliance, or post-quantum system. |
| Audit-log collector service boundary | A | Database-only readiness declaration, configured synchronous database-session path, startup schema initialization, static `/ready` probe contract, and explicit optional-mirror logging are regression-covered. | Describe only as source-level collector observability and persistence-boundary hardening. Do not claim live PostgreSQL durability, external-ledger replication, cryptographic immutability, or Docker-host healthcheck proof. |
| Case-management service boundary | A | The untenant-scoped legacy `/cases` API is explicitly retired with a 410 response; the retained governed case/playbook routes require capabilities, bind all lookups to the authenticated tenant, require approval before a playbook can run, and are regression-covered with a database-only readiness and static `/ready` probe contract. | Do not imply backward compatibility for the retired API, an automatic migration of historic legacy rows, live PostgreSQL/Docker-host proof, or external playbook execution. |
| Threat-intelligence advisory service boundary | A | Guarded lookup and bounded bulk routes require `alerts:read`; provider payloads and exception text are withheld; partial bulk failures are explicit; optional cache/provider behavior, actual container entrypoint, static healthcheck, and explicit-empty readiness semantics are regression-covered. | Describe only as a protected advisory enrichment interface. Do not claim real provider authorization or accuracy, live cache behavior, rate-limit resilience, Docker-host proof, detection efficacy, containment authority, or autonomous response. |
| Graph-intelligence service boundary | A | The arbitrary-Cypher `/graph` API is explicitly retired with a 410 response; Neo4j-only readiness, startup verification, owned-driver shutdown, actual container entrypoint, static `/ready` probe, and empty dependency-set semantics are regression-covered. | Do not claim a live Neo4j authorization policy, data migration, tenant-safe legacy graph projection, backup/recovery, production query performance, or graph-analysis efficacy. |
| Correlation-engine rule-management boundary | A | The untenant-scoped legacy `/rules` API is explicitly retired with a 410 response; the governed-rule API remains capability-protected and tenant-bound, while database-plus-Kafka readiness and correlation/ingestion/alert workflow regressions are covered. | Do not imply backward compatibility for the retired API, live broker or database durability, topic authorization, replay performance, external-enrichment reliability, Docker-host proof, or generalized detection efficacy. |
| Legacy SOAR playbook boundary | A | The untenant-scoped playbook, playbook-run, and approval APIs are explicitly retired with a 410 response; the retired service no longer imports legacy CRUD/session dependencies, has an empty dependency contract and static `/ready` probe, while governed containment approval and preflight regressions remain covered. | Do not claim compatibility with the retired API, migration of historic playbooks, real response execution, adapter validation, Docker-host proof, Wazuh manager/endpoint proof, or cloud containment proof. |
| Endpoint command signing boundary | A | The governed producer signs the complete canonical command envelope with deployment-managed RSA-PSS/SHA-256 key material after request construction and before audit-first dispatch; agents preserve the original envelope and reject missing, malformed, unsupported, altered, untrusted, or unverifiable signatures before handlers. Tracked generated certificates and private keys were removed and regression-covered. | Do not claim device packaging, operating-system trust-store behavior, live broker ACLs, key rotation in production, real endpoint execution, Wazuh/EDR validation, or containment efficacy without controlled-device evidence. |
| Evidence-grounded autonomous defense decisions | A | Tenant-owned policy evaluation, durable immutable decisions, source evidence linkage, refusal thresholds, cooldown/rate limits, and approval-required containment proposals are regression-covered. | Describe as bounded policy automation: it can record observations/investigations or create an approval-bound proposal; it never executes an adapter or self-approves high-impact containment. |
| Governed defensive data and baseline evaluation | A | Tenant-scoped source provenance, SHA-256 corpus identity, sanitized scalar-only labelled samples, operator/license approvals for non-BAS sources, immutable confusion-matrix results, and regression fixtures are source-controlled and tested. | Describe as controlled fixture evaluation and advisory calibration infrastructure; do not call it production training, live telemetry learning, or real-world detection efficacy. |
| Advisory model provider / evaluated model efficacy | A/D | The provider boundary is disabled by default, mockable, structured, evidence-minimized, accepted-evaluation-gated, and limited to observe/investigate output. The deterministic risk-score baseline is evaluated only against controlled fixtures; external/provider efficacy remains unvalidated. | Do not imply model-driven containment, autonomous remediation, production training, or validated AI performance. Any future model must remain evidence-cited, mockable, policy-gated, evaluated, and approval-bound. |
| Performance and scale | B/C | Isolated benchmark and resilience evidence exists; Phase 7 deployment reference is static and tested. | Publish only measured workload, environment, and percentile results. Do not generalize to real-time or high-scale operational capacity. |
| Self-hosted deployment | A/B/C | Reference Compose topology, internal networking, a source-controlled six-service observability contract inventory, full gateway dependency readiness, metrics, recovery runbook, and static YAML tests. | Call it a self-hosted deployment reference; live host, persistence, backup, proxy, and upgrade proof remain required. |
| Cross-platform agent | A/B/C | Cross-platform source contract compiles source and verifies required packaging inputs on hosted runners. | Do not equate source portability with native binaries, eBPF proof, Termux proof, or measured device resource use. |
| CI quality gates | A | Main-branch Quality Gates enforce Python regression/benchmarks, deterministic frontend lockfile installs, full dependency audits, and frontend lint/build; current workflow result must be checked per revision. | Reference the current workflow state, not historical counts or assertions. |
| License | A | Complete MIT License text is source-controlled. | Avoid stating legal or compliance conclusions beyond the license grant itself. |
| Broad legacy Compose topology | A/D | Root `docker-compose.yml` contains a broad development topology; the Phase 7 manifest is the hardened reference. | Do not present the broad development Compose file as a production topology. |

## Findings from the external review

The external report correctly identified several credibility risks: unsupported autonomous-AI and blockchain language, lack of external operational proof, a broad Compose surface, unvalidated real integrations, and the need for recovery, scalability, device, and security evidence. It also contained stale or incomplete assertions. The repository now contains a CI quality-gate workflow, committed frontend lockfiles, a Phase 7 self-hosted reference topology, governed Wazuh dry-run coverage, and more than 300 isolated regression tests.

The report’s license observation was confirmed: the prior source file was truncated despite naming MIT. The license is now replaced with the complete MIT grant. The report’s CI observation was historically true for an earlier state but not for the current quality-gate workflow; a Phase 7 environment-template omission briefly caused a remote CI failure and was corrected by tracking the safe template explicitly. This incident is retained as evidence that workflow status must be verified on the current revision rather than asserted from local results.

## Public claims policy

The portal now follows these rules.

| Do state | Do not state |
|---|---|
| The concrete control, its evidence type, and its explicit boundary. | That a design goal, roadmap item, or simulated path is production proof. |
| “HMAC-signed tamper-evident application audit chain.” | “Blockchain,” “immutable ledger,” “post-quantum audit,” or compliance certification. |
| “Approval-bound containment with verification and rollback.” | “Autonomous containment,” “self-healing defense,” or instant remediation. |
| “Evidence-grounded policy evaluation that records decisions or creates an approval-bound proposal.” | “AI automatically stops attacks,” “self-approved containment,” “autonomous remediation,” or independently validated model efficacy. |
| “Deterministic correlation, fixtures, MITRE evidence, analyst context, and controlled advisory evaluation.” | Generalized AI/ML, production-trained detection, prediction, global-feed, zero-day, or universal detection claims. |
| “Self-hosted deployment reference with a Docker-host lab gate.” | A production-ready or fully validated deployment claim. |

The credibility regression suite prevents known unsupported phrases from returning to the public portal without a deliberate review and evidence reclassification.

## Prioritized hardening plan

| Priority | Work item | Acceptance evidence |
|---:|---|---|
| P0 | Keep remote quality gates green and remove stale failing workflow behavior. | Current main-branch run succeeds; workflows state their actual proof boundary. |
| P0 | Keep runtime frontend dependencies in audited, lockfile-controlled ranges. | `npm ci` plus the full dependency audit gate passes; no known advisory in the resolved lockfile is ignored. |
| P0 | Maintain accurate public positioning and complete licensing. | Claim-regression tests pass; MIT text is complete; no placeholder public social or domain metadata remains. |
| P1 | Validate the Phase 7 Compose reference on a controlled Docker host. | Health-gated startup, dependency readiness, loopback ingress, metrics scrape, durable-volume restart, and recovery report. |
| P1 | Rehearse PostgreSQL, Redpanda, Neo4j, Redis, and audit-chain recovery. | Backup and restore evidence, RPO/RTO targets set by the operator, post-restore chain verification. |
| P1 | Execute Wazuh and AWS tests in non-production environments only. | Manager/endpoint receipt evidence; scoped IAM policy, CloudTrail evidence, exact-rule read-back, and rollback evidence. |
| P2 | Expand detection content through fixture-backed, MITRE-mapped rules. | Rule count and technique coverage published with fixtures, expected detections, and false-positive methodology. |
| P2 | Establish benchmark discipline. | Versioned workload, host specification, event mix, dependency topology, p50/p95/p99, error rate, and retained artifacts. |
| P2 | Validate agent packaging and footprint on supported lab devices. | Signed or checksummed artifacts, OS/device matrix, CPU/memory/battery measurements, and failure-mode documentation. |
| P3 | Establish external-model and real-telemetry evidence only after operator-approved data intake and controlled lab review. | Source-license approval, sanitization evidence, time-separated labelled corpus, calibration/acceptance metrics, drift evidence, and no-response-authority proof. |

## Controlled external-lab proof gates

No external proof gate may use a production target, production secrets, an unrestricted cloud account, live customer telemetry, or an unapproved endpoint. The following gates are documented for controlled execution:

1. **Topology gate:** start the Phase 7 reference on a lab Docker host; record image tags, rendered Compose configuration, readiness state, metrics scrape, and internal-network inspection.
2. **Recovery gate:** create disposable test data, take operator-managed backups, restore to a blank lab environment, and verify broker/database round trips plus HMAC audit chain.
3. **Incident-flow gate:** inject only approved BAS fixtures or lab honeypot telemetry; prove event → detection → alert → case → approval → signed audit → verified mock or lab response → rollback.
4. **Wazuh gate:** use a lab manager and allowlisted endpoint; verify telemetry provenance, one named command, exact signed receipt, replay rejection, and governed release.
5. **AWS gate:** use a dedicated sandbox account and a reviewed security-group rule; verify least-privilege identity, CloudTrail, exact read-back, and restoration. Never use production rules.
6. **Agent gate:** use test Linux, Windows, and Android/Termux devices; record installed version, host details, permissions, telemetry output, CPU, memory, battery observations, and clean uninstall behavior.
7. **Scale gate:** use synthetic, non-sensitive event fixtures; publish the exact rate, duration, host specification, topology, latency distribution, loss/error rate, and resource measurements.

## Remaining limits

This program improves honesty, repeatability, and readiness. It does not turn PhantomNet into a Splunk-, Sentinel-, Elastic-, or Wazuh-equivalent platform; certify regulatory compliance; create a third-party audit; establish a support SLA; prove production availability; or validate live attack tooling. Those outcomes require independent operational evidence, governance, sustained maintenance, and explicit owner acceptance.
