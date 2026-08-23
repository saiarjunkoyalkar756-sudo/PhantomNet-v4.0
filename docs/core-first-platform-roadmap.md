# PhantomNet Core-First Development Roadmap

## Product direction

The user-provided `PHANTOMNET_DEV_PROMPT.txt` is retained at the repository root. Its current-state snapshot is reconciled in `docs/DEVELOPMENT_PROMPT_RECONCILIATION.md`; source-controlled evidence on the current main branch remains authoritative when the prompt and implementation differ.

PhantomNet is being developed as a **self-hosted, AI-native SOC** for teams that need capable detection, investigation, and governed response without vendor lock-in. The platform’s non-negotiable core is durable tenant-owned evidence, analyst authority, human approval for high-impact action, verifiable execution, and signed audit history. Every later capability must strengthen this core rather than bypass it.

> **Development rule:** no enrichment, graph finding, BAS result, automation, or AI output may independently execute containment. High-impact response remains request → human approval → HMAC-signed audit → execution → read-back verification → rollback.

## Current platform baseline

The current codebase already includes versioned canonical events; durable detection, alerts, and cases; structured hunting; endpoint inventory; Wazuh-compatible read-only forwarding; approval-governed containment; evidence-backed attack-path analysis; and a fail-closed AWS Security Group adapter. The next work focuses on turning these strong feature boundaries into a consistent, deployable operating core.

| Existing foundation | Current state | Core rule retained |
|---|---|---|
| Canonical event, detection, alert, and case contracts | Implemented and isolated-test covered | Versioned evidence and tenant ownership |
| Correlation and alert workflows | Implemented with suppression and lifecycle control | Deterministic severity and analyst visibility |
| Endpoint and Wazuh telemetry | Read-only ingestion implemented | No Wazuh-originated containment |
| Containment and audit | Endpoint and AWS Security Group paths implemented | Approval, HMAC audit, verify, and rollback required |
| Attack-path analysis | Governed tenant-scoped projection implemented | Read-only graph context only |
| AWS test safety | Unit coverage and Docker-gated LocalStack integration harness implemented | No live-cloud test by default |

## Delivery phases

| Phase | Core capability | Completion gate |
|---:|---|---|
| 1 | **Runtime configuration and security posture core** | One typed source of truth for security-relevant environment settings, explicit fail-closed validation, and readiness output that identifies disabled, misconfigured, and ready capabilities without exposing secrets. |
| 2 | **Canonical ingestion reliability** | Durable replay identity, dead-letter evidence, tenant-bound provenance, retry classification, and operational metrics proven in isolated broker tests. |
| 3 | **Detection and correlation engineering** | Versioned rule governance, test fixtures, false-positive/suppression controls, MITRE coverage evidence, and deterministic correlation behavior. |
| 4 | **Evidence integration layer** | Tenant-scoped asset, identity, endpoint, Wazuh, and intelligence evidence adapters with strict read-only boundaries and source provenance. |
| 5 | **Analyst operations layer** | Case playbooks, guided hunting, dashboard health, graph context, explainable prioritization, and evidence-to-decision traceability. |
| 6 | **Governed response layer** | Additional narrowly scoped response adapters, preflight checks, least privilege, execution verification, rollback, and audit-chain integrity. |
| 7 | **Self-hosted deployment and observability** | Docker Compose deployment, dependency readiness, log and metric visibility, backup/recovery rehearsal, performance baselines, and upgrade checks on a Docker-capable host. |
| 8 | **Adversarial validation and BAS** | Safe BAS scenarios, endpoint telemetry fixtures, rule validation, response approval simulations, and no-live-target assurance. |
| 9 | **AI-native analyst assistance** | Explainable, advisory-only correlation suggestions, rule-draft workflows, accepted-evaluation gates, and analyst review with no direct response authority. |
| 10 | **External lab readiness** | Non-production deployment guide, operator runbooks, security review, onboarding checklist, and first external lab or university validation. |

## Completed development increment: governed defensive-data foundation

The current main branch contains a **governed defensive-data and advisory-evaluation foundation**. It stores tenant-scoped source provenance and sanitized scalar-only labelled features, fingerprints each versioned corpus, calculates immutable held-out evaluation metrics, and requires an accepted evaluation for the exact model ID/version before an advisory assessment can be recorded. The optional structured external provider is disabled by default, mockable, and structurally limited to observation or investigation guidance.

> **Boundary:** controlled BAS fixtures exercise the pipeline; they do not demonstrate trained-model efficacy, real-world false-positive performance, production telemetry learning, or autonomous response. Advisory output cannot create, approve, or execute containment.

## Next development increment: observable service contract inventory

The next production-readiness implementation is a source-controlled inventory of the Phase 7 control-plane services and their health, readiness, and metrics contracts. The inventory must distinguish standardized shared-factory routes from legacy service-specific routes, identify dependency expectations, and add regression tests that prevent coverage from silently regressing. This creates Class A source evidence; a Docker-host deployment/recovery exercise remains Class C.

The first extension beyond the Phase 7 control plane now covers the **core telemetry-to-alert path**. Telemetry ingestion, event normalization, command dispatch, and behavioral analysis declare Kafka as their only readiness dependency; alert storage declares PostgreSQL and Kafka. These explicit contracts replace the generic database/Kafka/Redis default for those services, so `/ready` fails closed only when an actual upstream dependency is unavailable. Full service-by-service coverage remains open.

## Completed bounded increment: audit-log collector persistence and observability boundary

The audit-log collector now declares **PostgreSQL/database only** as its readiness dependency and uses a complete synchronous session dependency rather than an incomplete local helper. In a configured deployment, the collector resolves `AUDIT_DATABASE_URL` or `DATABASE_URL`, or derives a PostgreSQL URL from the injected database environment. The collector-owned audit table is initialized through the explicit service startup hook; isolated SQLite remains a local fallback only when no database configuration is supplied.

The legacy broad development Compose service now has a bounded `/ready` healthcheck, and regression coverage verifies its dependency declaration, startup initialization call, and probe configuration. Its optional legacy ledger mirror remains non-authoritative: after the collector’s durable write returns, a missing module is logged as informational and a mirror exception is emitted through exception logging without blocking ingestion. This removes silent suppression while preserving the durable audit write path.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence only. It does not prove a live Docker healthcheck, PostgreSQL persistence, an external ledger mirror, cryptographic audit immutability, or production-operable deployment. The root Compose file remains a legacy development topology; the hardened six-service Phase 7 reference and controlled external-lab gates remain the authoritative paths for deployment proof.

## Completed bounded increment: case-management tenant-safety boundary

The case-management service now declares **database only** as its readiness dependency, initializes only the governed workflow store, and has a bounded `/ready` healthcheck in the legacy development Compose file. The former `/cases` CRUD and simulated-playbook routes were untenant-scoped and did not enforce a capability boundary. They now fail closed with `410 LEGACY_CASE_API_RETIRED` and direct callers to the governed API.

The retained `/governed-cases` lifecycle remains tenant-bound and capability-protected. Case creation begins from an authenticated tenant-owned alert; playbook runs begin approval-bound, require `response:approve` before approval, and the workflow records lifecycle state without dispatching an action. Regression coverage validates the actual retired route, startup-store boundary, readiness declaration, healthcheck configuration, tenant isolation, and approval-before-running invariant.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not migrate or delete historic rows in the legacy `cases` table, prove a live PostgreSQL/Docker-host deployment, or prove real external response execution. An operator-approved data migration or retention decision, controlled-host health evidence, and governed response evidence remain separate work.

## Completed bounded increment: threat-intelligence advisory boundary

The threat-intelligence service now registers its guarded routes after declaration, so its `/api/threat-intel/lookup` and bounded `/bulk` APIs are actually reachable. Both require the existing `alerts:read` capability. Indicator types and lengths are constrained, bulk requests are limited to 50 indicators, and provider failures are returned as generic advisory availability results rather than serialized exceptions. Provider payloads are withheld from API responses; the response retains only a per-provider availability summary.

The service treats Redis caching and external providers as optional advisory dependencies. Its explicit empty readiness contract avoids inheriting unrelated database, broker, and Redis checks; cache availability is logged during startup without blocking process startup. The shared factory now preserves an explicit empty dependency set. The container now invokes the actual `main:app` entrypoint and the legacy development Compose service has a bounded `/ready` healthcheck.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not prove API-key validity, provider authorization, live external enrichment accuracy, Redis durability, rate-limit behavior, cache isolation under real load, live Docker startup, or any detection/containment efficacy. The enrichment path is advisory-only and must not be represented as an enforcement or autonomous-response capability.

## Completed bounded increment: graph-intelligence raw-query boundary

The graph-intelligence service now declares **Neo4j only** as its readiness dependency, verifies the graph store on startup, closes the process-owned driver on shutdown, invokes the correct `main:app` container entrypoint, and has a bounded legacy Compose `/ready` healthcheck. The former `/graph` endpoint accepted arbitrary Cypher without an authorization or tenant boundary. It now returns `410 RAW_GRAPH_API_RETIRED`; tenant-scoped investigation must use the governed graph APIs instead.

The shared readiness runner now preserves an explicitly empty dependency set, matching the earlier factory correction for advisory services. Regression coverage verifies the real ASGI retirement response, Neo4j startup/shutdown ownership, static Compose healthcheck, container entrypoint, and empty-set behavior without connecting to a graph database.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not prove a live Neo4j authentication/authorization policy, graph data migration, tenant isolation inside a legacy graph projection, Docker-host startup, backup/recovery, query performance, or graph-analysis efficacy. The incomplete internal consumer remains outside this release’s production claim boundary.

## Completed bounded increment: correlation-engine rule-management boundary

The correlation engine now declares **database and Kafka only** as its readiness dependencies, matching its durable projection initialization and background broker consumer. The prior `/rules` CRUD endpoints were untenant-scoped and unauthenticated. They now fail closed with `410 LEGACY_RULE_API_RETIRED`; rule management is limited to the existing tenant-scoped, capability-protected `/governed-rules` interface.

The governed API retains structured deterministic rule definitions, tenant-mismatch rejection, immutable revisions, fixture evaluation, quality summaries, and no response-execution authority. Regression coverage validates dependency declaration, retention of governed-capability guards, actual ASGI retirement behavior, absence of the legacy rule-store import, and the existing ingestion/alert/tenant workflow invariants.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not demonstrate live Kafka consumer startup, PostgreSQL durability, topic authorization, replay performance, external enrichment provider behavior, Docker-host startup, or detection efficacy. Controlled broker/database-host and recovery evidence remains required before operational claims.

## Completed bounded increment: legacy SOAR playbook retirement

The legacy SOAR playbook engine exposed unauthenticated, untenant-scoped playbook creation, run updates, and approval records. It is now an explicit fail-closed compatibility boundary: all former `/playbooks`, `/playbook_runs`, and `/playbook_approvals` paths return `410 LEGACY_SOAR_PLAYBOOK_API_RETIRED`, the legacy service no longer imports its CRUD/session layer, and the development Compose entry has a bounded `/ready` healthcheck.

The approved control surface remains the existing tenant-scoped governed containment API. High-impact containment continues to require a request, human approval, HMAC-signed audit, adapter execution, verification, and rollback. Regression coverage exercises all retired route families through ASGI and reruns governed containment, preflight, tenant-isolation, and Wazuh response-bridge boundaries.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not migrate legacy playbook records, prove real containment execution, validate a Docker-host deployment, or validate an external Wazuh manager, endpoint, cloud account, or response adapter. The retirement does not alter the separate governed containment approval protocol.

## Completed bounded increment: fail-closed endpoint command signing

The governed agent-command producer now signs the complete canonical `phantomnet.agent-command.v1` envelope with **RSA-PSS/SHA-256** using deployment-managed `PHANTOMNET_AGENT_COMMAND_SIGNING_PRIVATE_KEY` material. Signing occurs before the established audit-first broker dispatch. Missing or invalid signing material rejects the request before either audit acceptance or command publication.

The endpoint agent now preserves the complete broker envelope and requires a matching trusted public key or X.509 certificate at `PHANTOMNET_AGENT_COMMAND_TRUSTED_CERT_PATH`. It rejects missing, malformed, unsupported, altered, untrusted, or unverifiable signatures before any command executor handler is selected. The older optional signature enforcement and missing-certificate bypasses were removed. Previously tracked generated certificates and all private keys were removed from source control and must be replaced with a fresh operator-provisioned trust chain.

The source-controlled protocol and controlled-device evidence requirements are detailed in `docs/ENDPOINT_COMMAND_SIGNING_PROVISIONING.md`. Focused regressions prove canonical signature validation, tamper rejection, missing-key non-publication, audit-before-dispatch for a valid signed command, and removal of the unsigned fallback.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not prove agent packaging, runtime secret injection, OS trust-store behavior, broker ACLs, certificate rotation, command delivery, live device execution, or containment effectiveness. Those claims require the controlled-device validation gate with fresh non-repository credentials.

## Completed bounded increment: legacy API gateway retirement

The legacy API gateway previously composed authentication, administrative blacklist, agent enrollment, websocket, and orchestrator routers into one service. Its audit identified untenant-scoped and unauthenticated route families that could not be safely retained as a public compatibility surface. The legacy gateway is now a fail-closed boundary: standard `/health`, `/ready`, `/metrics`, and compatibility `/health_status` remain available, while former routes return `410 LEGACY_API_GATEWAY_RETIRED`.

The separate self-hosted governed gateway and tenant-scoped service APIs remain the supported control plane. The retired gateway declares no mandatory upstream dependency because it performs no authentication, persistence, broker, enrollment, or response function. Regression coverage verifies actual ASGI retirement responses for former administrative, agent, authentication, and orchestrator paths and confirms standard health visibility remains intact.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not demonstrate migration of legacy callers, live ingress routing, replacement API adoption, Docker-host startup, hosted authentication behavior, agent enrollment, or response execution. Operators must update integrations to supported governed APIs before retiring any legacy deployment.

## Completed development increment: Phase 7

Phase 7 now provides a **self-hosted deployment and observability reference architecture**. The new Compose topology isolates PostgreSQL, Redis, Redpanda, and Neo4j on an internal network; exposes the gateway and Prometheus only through loopback ports; health-gates the control-plane startup; pins service images; protects stateless services with read-only filesystems and dropped capabilities; and requires every credential to be injected outside source control.

The standard service factory now exposes bounded, Prometheus-compatible process counters. Readiness continues to combine upstream dependency checks with secret-safe runtime posture, while the existing recovery harness remains the minimum Docker-host proof for broker, database, and HMAC audit-chain recovery. The architecture documentation defines backup, restore, upgrade, ingress, and external Docker-host validation requirements without claiming a live deployment from this sandbox.

> **Phase 7 closure rule:** internal topology is not public ingress, liveness is not readiness, static Compose proof is not live-host proof, and a successful start does not replace backup, recovery, audit-chain, or operator acceptance evidence.

## Sequencing principles

The roadmap is intentionally core-first. It prioritizes safety and operability over additional integrations, and it builds every new adapter around the same canonical contracts, RBAC, tenant isolation, audit-chain rules, and test harnesses. Deployment validation cannot be represented as complete until it runs on Docker-capable infrastructure; similarly, real cloud validation remains a separate non-production lab gate rather than a sandbox action.
