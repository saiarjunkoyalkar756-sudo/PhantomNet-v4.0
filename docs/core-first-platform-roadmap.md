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

## Completed bounded increment: legacy vulnerability-management retirement

The legacy vulnerability-management service exposed mock asset inventory, scanner, external-CVE lookup, vulnerability, and patch-recommendation routes without an authentication or tenant boundary. It now declares no mandatory upstream dependency and fails closed with `410 LEGACY_VULNERABILITY_API_RETIRED` for its former route family, while retaining standardized health endpoints.

This prevents fixture-backed data and ungoverned recommendation behavior from being represented as a real vulnerability-management capability. Regression coverage exercises representative asset, scan, CVE, and patch-recommendation paths through ASGI and confirms the retired service has no dependency claim.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed replacement asset inventory, scanner, patch executor, real CVE-provider validation, tenant-safe remediation lifecycle, Docker-host evidence, or vulnerability-detection efficacy. Those remain separate source and controlled-lab workstreams.

## Completed bounded increment: legacy honeypot lifecycle retirement

The legacy honeypot service exposed unauthenticated routes that could create and stop local runner processes, list their status, and return event placeholders. It now declares no mandatory dependency and returns `410 LEGACY_HONEYPOT_API_RETIRED` for all former honeypot lifecycle paths. The entry point no longer imports the lifecycle manager or process runner; standard health and metrics endpoints remain available.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not implement a governed replacement honeypot deployment, validate safe listener isolation, capture real attacker interaction, forward telemetry, or establish any external-lab honeypot proof.

## Completed bounded increment: legacy microsegmentation retirement

The legacy microsegmentation service exposed unauthenticated fixture network segments, violations, threats, graph topology, and a non-governed segment-creation route. It now declares no mandatory upstream dependency and returns `410 LEGACY_MICROSEGMENTATION_API_RETIRED` for its former `/api/v1` surface. The entry point no longer initializes a Kafka consumer or in-memory topology graph.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not implement a governed tenant-safe microsegmentation replacement, validate live broker ingestion, prove topology accuracy, execute a network policy, or provide Docker-host or external enforcement evidence.

## Completed bounded increment: legacy plugin marketplace retirement

The legacy plugin marketplace accepted unauthenticated upload files, registered JSON manifests, and enabled or disabled plugin state without tenant context, signature verification, provenance, or controlled execution assurance. It now declares no mandatory dependency and returns `410 LEGACY_PLUGIN_MARKETPLACE_API_RETIRED` for all former plugin routes. The entry point no longer initializes a plugin manager or filesystem artifact directory.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed signed-artifact replacement, malware scanning, provenance validation, compatibility testing, sandboxed execution, tenant-owned extension lifecycle, Docker-host proof, or plugin efficacy evidence.

## Completed bounded increment: legacy PhantomQL retirement

The legacy PhantomQL service exposed direct database-backed event search and aggregate analytics without authentication or tenant scope. It now starts a valid standard service with no mandatory dependency and returns `410 LEGACY_PHANTOMQL_API_RETIRED` for former query and analytics routes. The service no longer initializes session or query-parser dependencies.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-safe query replacement, validate query correctness, prove database performance, authorize data access, or establish Docker-host or analyst-workflow proof.

## Completed bounded increment: legacy vulnerability scanner retirement

The legacy vulnerability scanner accepted arbitrary port-scan targets, returned fixture CVE findings, and processed configuration payloads without authentication, authorization, tenant scope, or approved target boundaries. It now declares no mandatory dependency and returns `410 LEGACY_VULNERABILITY_SCANNER_API_RETIRED` for all former scanner routes. The entry point no longer imports nmap or scanner request models.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed authorized-scanning replacement, target ownership validation, real CVE detection, scan accuracy, remediation lifecycle, Docker-host proof, or external assessment evidence.

## Completed bounded increment: legacy PNQL retirement

The legacy PNQL service accepted direct parser-and-executor requests without authentication or tenant scope. It now declares no mandatory dependency and returns `410 LEGACY_PNQL_API_RETIRED` for its former query route. The entry point no longer imports the query parser, executor, or request model.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-safe PNQL replacement, validate parser correctness, prove query authorization, establish database performance, or supply Docker-host or analyst-workflow evidence.

## Completed bounded increment: legacy SIEM integration retirement

The legacy SIEM integration service accepted unauthenticated log ingestion, executed direct in-memory PhantomQL queries, enumerated a fixture workspace, and exposed raw and normalized log records without tenant scope. It now declares no mandatory dependency and returns `410 LEGACY_SIEM_INTEGRATION_API_RETIRED` for the entire former `/api/siem` route family. The entry point no longer starts the ingest worker, normalizer, in-memory stores, or direct query engine.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-scoped replacement ingestion or analytical API, validate telemetry delivery, normalization correctness, log durability, broker/database performance, source authorization, Docker-host deployment, or detection efficacy.

## Completed bounded increment: legacy auto-response retirement

The legacy auto-response engine exposed unauthenticated execution and approval-resume routes for simulated `isolate_host`, `block_ip`, and ticket actions. It neither enforced tenant scope nor established a complete human-approval, HMAC-audit, verification, or rollback chain. It now declares no mandatory dependency and returns `410 LEGACY_AUTO_RESPONSE_API_RETIRED` for the entire former route family; the entry point no longer imports or starts the simulated executor, background runner, or legacy playbook CRUD path.

The supported containment surface remains the separate governed workflow, in which high-impact action is requested, human-approved, HMAC-audited, executed through a controlled adapter, verified, and rollback-capable. This retirement does not broaden automatic enforcement.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not validate a governed response replacement through this legacy service, live adapter execution, approval identity, audit durability, verification, rollback, Docker-host deployment, or containment efficacy.

## Completed bounded increment: legacy asset-inventory retirement

The legacy asset-inventory service accepted arbitrary scan targets through an unauthenticated background task and disclosed an unscoped asset list. It now declares no mandatory dependency and returns `410 LEGACY_ASSET_INVENTORY_API_RETIRED` for its former scan and asset routes. The entry point no longer imports or initializes the scanner, local asset table, or background task.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-safe inventory or authorized-discovery replacement, validate target ownership, perform a real scan, prove source authentication, establish asset accuracy or durability, or provide Docker-host or external assessment evidence.

## Completed bounded increment: legacy asset relationship retirement

The secondary legacy asset-inventory service authenticated callers but initialized a shared fixture graph and returned organizational assets, dependency topology, and blast-radius relationships without tenant binding or durable source provenance. It now declares no mandatory dependency and returns `410 LEGACY_ASSET_RELATIONSHIP_API_RETIRED` for its former asset relationship routes. The entry point no longer imports or initializes fixture graph data.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-safe relationship-inventory replacement, validate source provenance, asset or topology accuracy, authorization behavior, data durability, Docker-host operation, or graph-analysis efficacy.

## Completed bounded increment: legacy DFIR toolkit retirement

The legacy DFIR toolkit accepted unauthenticated server filesystem paths for YARA, memory, PCAP, and timeline analysis, and accepted arbitrary file uploads to a shared temporary directory. It now declares no mandatory dependency and returns `410 LEGACY_DFIR_API_RETIRED` for its former analysis and upload routes. The entry point no longer imports forensic tools or initializes an upload directory.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-scoped evidence intake or forensic-analysis replacement, validate file provenance, retention, malware isolation, YARA or memory/PCAP correctness, analyst authorization, Docker-host operation, or investigative efficacy.

## Completed bounded increment: legacy cloud-security retirement

The legacy cloud-security service accepted AWS access keys and secrets in unauthenticated request bodies, enumerated S3 configuration from caller-supplied credentials, and emitted a fixture-style IAM-abuse finding. It now declares no mandatory dependency and returns `410 LEGACY_CLOUD_SECURITY_API_RETIRED` for its former cloud posture routes. The entry point no longer imports boto3 or accepts, logs, or processes caller-supplied cloud credentials.

The separate governed AWS Security Group containment adapter remains deployment-managed, approval-bound, HMAC-audited, verified, and rollback-capable. This retirement does not add automatic cloud enforcement.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed cloud-posture replacement through this service, validate cloud credential injection or authorization, enumerate real cloud resources, prove S3/IAM detection accuracy, establish AWS account isolation, or provide controlled-cloud/Docker-host evidence.

## Completed bounded increment: legacy compliance-reporting retirement

The legacy compliance-reporting service generated unauthenticated fixture compliance scores and findings, wrote PDFs to a shared local directory, maintained a process-local report list, and allowed unscoped report download. It now declares no mandatory dependency and returns `410 LEGACY_COMPLIANCE_REPORTING_API_RETIRED` for its former report-generation, listing, and download routes. The entry point no longer imports the PDF generator, initializes a report directory, or maintains fixture report state.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed tenant-scoped compliance-reporting replacement, validate evidence collection, control mapping, report accuracy, generation integrity, secure storage or download authorization, retention, Docker-host operation, or audit/compliance efficacy.

## Completed bounded increment: legacy malware sandbox retirement

The legacy malware sandbox exposed unauthenticated file upload and sandbox execution, disclosed whether its Docker connection was real or mocked, wrote user-controlled files and generated scripts into temporary directories, and returned fixture-like findings. It now declares no mandatory dependency and returns `410 LEGACY_SANDBOX_API_RETIRED` for its former analysis and detailed-health routes. The entry point no longer imports or initializes the sandbox runner, upload handler, or temporary execution components.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed evidence-intake or malware-analysis replacement, validate tenant-bound sample ownership, upload malware isolation, sandbox escape resistance, analysis accuracy, artifact retention, analyst authorization, Docker-host operation, or malware-detection efficacy.

## Completed bounded increment: legacy autonomous blue-team retirement

The legacy autonomous blue-team service accepted unauthenticated defensive-action requests, started an ungated Kafka consumer, and exposed process-local action-history files and identifiers. It now declares no mandatory dependency and returns `410 LEGACY_AUTONOMOUS_BLUE_TEAM_API_RETIRED` for its former action and history routes. The entry point no longer imports or starts its consumer, local history directory, or simulated defensive-action path.

The supported containment surface remains the separate governed workflow, in which high-impact action is requested, human-approved, HMAC-audited, executed through a controlled adapter, verified, and rollback-capable. This retirement does not permit automatic enforcement.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not validate a governed response replacement through this legacy service, broker authorization, live response execution, action-history durability, approval identity, audit-chain integrity, verification, rollback, Docker-host operation, or containment efficacy.

## Completed bounded increment: legacy BAS engine retirement

The legacy BAS engine accepted unauthenticated arbitrary targets and directly invoked XSS, SQLi, RCE, privilege-escalation, ransomware-mimic, port-scan, and brute-force simulation modules. It also disclosed process-local simulation result files and identifiers. It now declares no mandatory dependency and returns `410 LEGACY_BAS_API_RETIRED` for its former simulation and result routes. The entry point no longer imports simulation modules or initializes a local result directory.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed BAS replacement, target ownership authorization, scenario safety, isolation, accurate simulation behavior, result integrity, tenant-safe evidence storage, Docker-host operation, real-target validation, or detection/response efficacy. Controlled baseline scenarios remain no-live-target evaluation infrastructure, not a public attack surface.

## Completed bounded increment: legacy playbook-flow builder retirement

The legacy playbook-flow builder accepted unauthenticated workflow definitions and converted them into playbook step sequences without tenant binding, capability checks, evidence linkage, human approval, audit, verification, or rollback controls. It now declares no mandatory dependency and returns `410 LEGACY_PLAYBOOK_FLOW_BUILDER_API_RETIRED` for its former conversion route. The entry point no longer imports the flow schema or converter.

The supported containment surface remains the separate governed workflow, in which high-impact action is requested, human-approved, HMAC-audited, executed through a controlled adapter, verified, and rollback-capable. This retirement does not permit automatic enforcement.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed response-workflow builder replacement, validate tenant-scoped authoring, policy enforcement, approval identity, audit-chain integrity, execution verification, rollback, Docker-host operation, or containment efficacy.

## Completed bounded increment: legacy analyzer retirement

The legacy analyzer service exposed an unauthenticated conversational AI endpoint backed by the neural threat brain and started a separate unmanaged consumer thread at service startup. It now declares no mandatory dependency and returns `410 LEGACY_ANALYZER_API_RETIRED` for its former chat route. The entry point no longer imports the neural threat brain or starts the legacy consumer.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed advisory replacement through this service, validate model behavior, conversation privacy, tenant isolation, provider authorization, evaluation quality, broker behavior, Docker-host operation, or AI/detection efficacy. Advisory assistance remains evidence-bound, policy-gated, and non-executing.

## Completed bounded increment: legacy event-stream processor retirement

The legacy event-stream processor started an ungated Kafka consumer and exposed a direct database log-query API without authentication or tenant scoping. It now declares no mandatory dependency and returns `410 LEGACY_EVENT_STREAM_PROCESSOR_API_RETIRED` for its former log route. The entry point no longer imports or starts the consumer, database connection, or direct SQL query path.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed analytical-query replacement through this service, validate broker authorization, event durability, database query correctness or performance, tenant isolation in historic data, Docker-host operation, or detection efficacy. Governed canonical ingestion and tenant-scoped workflows remain separate supported paths.

## Completed bounded increment: legacy lateral-movement detector retirement

The legacy lateral-movement detector accepted unauthenticated arbitrary batches of normalized events and returned sensitive host, user, command-line, and detection context without tenant binding or evidence provenance. It now declares no mandatory dependency and returns `410 LEGACY_LATERAL_MOVEMENT_API_RETIRED` for its former direct detection route. The entry point no longer imports the event schema or direct detector implementation.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed lateral-movement detection replacement through this service, validate telemetry normalization, MITRE mapping, detection correctness, false-positive rate, tenant data isolation, analyst authorization, Docker-host operation, or detection efficacy. Governed tenant-scoped correlation and investigation workflows remain separate supported paths.

## Completed bounded increment: legacy MITRE mapper retirement

The legacy MITRE ATT&CK mapper disclosed its local technique dataset and accepted arbitrary event dictionaries for direct mapping without authentication, tenant binding, source provenance, or analyst authorization. It now declares no mandatory dependency and returns `410 LEGACY_MITRE_MAPPER_API_RETIRED` for its former technique-listing and event-mapping routes. The entry point no longer imports the mapper or local dataset.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed ATT&CK mapping replacement through this service, validate content versioning, MITRE coverage or mapping correctness, source provenance, tenant data isolation, analyst authorization, Docker-host operation, or detection efficacy. Governed tenant-scoped detection content and investigation workflows remain separate supported paths.

## Completed bounded increment: legacy forensics-engine retirement

The legacy forensics engine accepted unauthenticated forensic-job requests, ran placeholder background work, initialized its own database tables, listed unscoped jobs, nested evidence and timeline routers, and wrote local forensic-vault records. It now declares no mandatory dependency and returns `410 LEGACY_FORENSICS_API_RETIRED` for its former job, timeline, and evidence route families. The entry point no longer imports job persistence, nested routers, background-task code, or forensic-vault logging.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed forensic replacement through this service, validate evidence collection, chain of custody, source provenance, tenant isolation, forensic analysis correctness, secure retention, analyst authorization, Docker-host operation, or investigative efficacy. Governed tenant-scoped evidence intake and analyst-authorized investigation remain separate supported work.

## Completed bounded increment: legacy AI agent orchestrator retirement

The legacy AI agent orchestrator accepted unauthenticated natural-language task requests and returned AI-generated reasoning and proposed actions without tenant binding, evidence provenance, policy gating, analyst oversight, or a non-execution guarantee. It now declares no mandatory dependency and returns `410 LEGACY_AI_AGENT_ORCHESTRATOR_API_RETIRED` for its former task route. The entry point no longer imports or initializes the agent brain or any task-planning model.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed advisory replacement through this service, validate model behavior, prompt handling, tenant isolation, evidence provenance, policy evaluation, provider authorization, analyst oversight, Docker-host operation, or AI/detection efficacy. Advisory assistance remains evidence-bound, policy-gated, and non-executing.

## Completed bounded increment: legacy chatbot retirement

The legacy chatbot accepted sensitive attack payloads and queries, generated signature, attribution, score, and countermeasure output, and logged the free-text query despite lacking evidence linkage, tenancy-aware data selection, policy gating, or a non-execution guarantee. It now declares no mandatory dependency and returns `410 LEGACY_CHATBOT_API_RETIRED` for its former chat route. The entry point no longer imports the legacy role-auth, database, prompt, signature, attribution, scoring, or countermeasure components.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed advisory replacement through this service, validate prompt handling, privacy, tenant isolation, evidence provenance, signature or attribution correctness, scoring quality, policy evaluation, provider authorization, analyst oversight, Docker-host operation, or AI/detection efficacy. Advisory assistance remains evidence-bound, policy-gated, and non-executing.

## Completed bounded increment: legacy AI behavioral-engine retirement

The legacy AI behavioral engine exposed untenant-scoped event analysis and fixture user profiles, while its second entry point initialized Kafka consumers and producers, retained mutable process-local event state, ran forecasting tasks, published predictions, and disclosed broker/model safe-mode details. Both entry points now declare no mandatory dependency and return `410 LEGACY_AI_BEHAVIORAL_API_RETIRED` for their former analysis, profile, and detailed-health routes. The code no longer imports behavioral-event, consumer, broker, model, forecasting, mutable-state, or detailed-health components. The active core-ingestion readiness matrix no longer represents this retired worker as Kafka-dependent.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed behavioral-detection or forecasting replacement, validate telemetry normalization, model behavior, anomaly or forecast correctness, provenance, tenant isolation, broker authorization, event durability, policy evaluation, provider authorization, Docker-host operation, or AI/detection efficacy. Governed evidence-bound detection and non-executing advisory workflows remain separate supported paths.

## Completed bounded increment: legacy SOC copilot retirement

The legacy SOC copilot exposed unauthenticated alert explanation, auto-investigation, and AI rule/report generation, while its second entry point directly queried SIEM and vulnerability data sources, disclosed raw context and related log snippets, and returned simulated recommendations and generated artifacts without tenant isolation, provenance, policy gating, or a non-execution guarantee. Both entry points now return `410 LEGACY_SOC_COPILOT_API_RETIRED`; the service declares no mandatory dependency and no longer imports context-builder, cross-service database, schema, auto-investigation, or generation components.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed SOC copilot replacement, validate prompt handling, privacy, tenant isolation, evidence provenance, context authorization, recommendation or rule/report correctness, policy evaluation, provider authorization, analyst oversight, Docker-host operation, or AI/detection efficacy. Advisory assistance remains evidence-bound, policy-gated, and non-executing.

## Completed bounded increment: legacy gateway PQC and crypto-agility retirement

The active self-hosted gateway remains the production-reference entry point, with standardized health, readiness, environment-scoped CORS, rate limiting, and governed router composition retained. Its unauthenticated caller-selected PQC handshake and simulated crypto-agility routes are now explicitly retired with `410 LEGACY_GATEWAY_PQC_API_RETIRED`. The gateway no longer imports the PQC wrapper or invokes key encapsulation or simulated agility checks. Targeted ASGI coverage verifies the active health route remains available under isolated middleware dependencies.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not validate deployment-managed cryptographic session establishment, key custody, key rotation, ML-KEM interoperability, algorithm-agility assessment accuracy, authorization, real cryptographic posture, Docker-host operation, or production gateway security efficacy.

## Completed bounded increment: legacy SOAR engine retirement

The legacy SOAR engine exposed unscoped playbook listing and loading, direct playbook execution, simulated AI playbook generation, in-memory approval disclosure, caller-supplied approval decisions, and a legacy Kafka consumer. It now declares database-only readiness and returns `410 LEGACY_SOAR_API_RETIRED` for its legacy `/api/soar` routes. The engine no longer imports legacy playbook/executor, generation, in-memory approval, or consumer components. The separate `/api/soar/governed-containment` router remains first-class and retains tenant-scoped approvals, signed audit evidence, execution verification, and rollback.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not validate governed containment execution, approval identity, HMAC key custody, audit durability, adapter verification, rollback behavior, Wazuh receipt authentication, database recovery, Docker-host operation, or containment efficacy. The retained governed path remains approval-bound and cannot justify claims of automatic high-impact enforcement.

## Completed bounded increment: legacy gateway orchestrator-mutation retirement

The active self-hosted gateway’s mounted orchestrator router no longer accepts caller-supplied blockchain transaction mining, honeypot lifecycle control, or simulated attack forwarding to the telemetry ingestor. These routes now return `410 LEGACY_GATEWAY_ORCHESTRATOR_MUTATION_RETIRED`; the router no longer imports the command dispatcher or schemas for these operations, initializes an HTTP client, reads a telemetry-ingestor URL, or invokes block mining. Authenticated blockchain read and verification behavior was deliberately left for separate, narrower audit rather than being represented as a containment mechanism.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not validate blockchain integrity, audit notarization, honeypot isolation, authorized simulation, telemetry ingestion, tenant isolation, control-plane authorization, Docker-host operation, or production gateway security efficacy.

## Completed bounded increment: legacy gateway API-ecosystem retirement

The active self-hosted gateway no longer mounts a live conceptual API ecosystem. Its former threat-summary and daily-digest routes mixed database counts and raw-log disclosure with static attack types, risk scores, anomalies, and recommendations; the GraphQL placeholder echoed caller input; and the module retained local SDK-file generation. The entire router now returns `410 LEGACY_GATEWAY_ECOSYSTEM_API_RETIRED`, and no longer imports database analytics, user authentication, GraphQL echo, or SDK-generation components. The former gateway test now explicitly protects that retirement contract.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide governed analytics or reporting replacement, validate data provenance, tenant isolation, report authorization, aggregation correctness, privacy, retention, SDK generation, Docker-host operation, or operational detection efficacy.

## Completed bounded increment: legacy gateway agent-management retirement

The active self-hosted gateway no longer exposes its legacy agent-management surface. That router permitted optional in-memory bootstrap-token enrollment, process-local certificate authority material, unauthenticated agent heartbeats and configuration reads, an unscoped agent list, non-durable approval, and unauthenticated agent-event WebSocket subscription. Every former HTTP route under `/agents` now returns `410 LEGACY_GATEWAY_AGENT_API_RETIRED`, and the legacy WebSocket is rejected before subscription. The router no longer imports enrollment, certificate, database, telemetry, message-bus, in-memory-token, or authorization components. This does not alter separately versioned agent command interfaces, which require their own independent security evidence.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed enrollment replacement or validate agent identity, certificate issuance or revocation, key custody, tenant isolation, configuration authorization, telemetry durability, approval/audit durability, WebSocket authorization, command authorization, endpoint signing, Docker-host operation, or endpoint-security efficacy.

## Completed bounded increment: legacy gateway admin retirement

The active self-hosted gateway no longer exposes its legacy `/admin` control surface. That router could mutate a globally unique blacklist without tenant ownership, approval/audit lifecycle, or enforcement verification, and it exposed unscoped user and blacklist listings. Every former route now returns `410 LEGACY_GATEWAY_ADMIN_API_RETIRED`; the source no longer imports blacklist or user models, database access, data schemas, capability enforcement, query helpers, or commit operations.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed administrative or network-control replacement, validate tenant isolation, administrator identity, capability policy, approval/audit durability, enforcement, verification, rollback, user-directory privacy, database durability, Docker-host operation, or containment efficacy.

## Completed bounded increment: legacy gateway blockchain read/verify retirement

The active self-hosted gateway no longer exposes its legacy global blockchain read or conceptual verification routes. The former chain endpoint returned every persisted block and transaction without a tenant boundary, while the administrative verification endpoint treated a process-local, simplified link check as an audit-integrity result. Both now return `410 LEGACY_GATEWAY_BLOCKCHAIN_API_RETIRED`; the router no longer imports blockchain, block, transaction, database, user, authentication, or success-response components for these paths. Existing gateway mutation-retirement routes retain their distinct contract, and the unrelated threat-analysis compatibility endpoint remains explicitly disabled.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed audit-evidence replacement or validate tenant isolation, provenance, HMAC audit-chain integrity, cryptographic notarization, immutable-ledger semantics, blockchain correctness, administrator authorization, database durability, Docker-host operation, or compliance/security efficacy.

## Completed bounded increment: IAM self-registration and simulated-reset boundary

The mounted IAM router now treats public self-registration as a standard-user path only. The request schema no longer accepts a caller-supplied role, the handler assigns the `user` role explicitly, and its issued session token now uses the registered username as the subject expected by the session-validation dependency. The former password-reset request/confirmation endpoints were retired with `410 LEGACY_SIMULATED_PASSWORD_RESET_RETIRED`: they previously returned a reset credential directly to the caller while claiming simulated delivery and did not match the persisted reset-token record contract. Dashboard registration no longer offers privileged-role selection; the reset views now state that a verified, durable recovery workflow is required and make no calls to retired routes.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide tenant provisioning, administrator provisioning, identity proofing, verified email or other out-of-band delivery, password-reset recovery, MFA/WebAuthn assurance, session revocation under real Redis/PostgreSQL failure, rate-limit effectiveness, user-directory privacy, Docker-host operation, or production authentication security proof.

## Completed bounded increment: direct agent-command dispatch retirement

The standalone direct agent-command API no longer signs, audits, or publishes arbitrary endpoint or network commands. Although its former envelope carried a tenant claim and RSA-PSS signature, it accepted arbitrary command types and targets through a capability-only route without a tenant-owned target check or the required request → human approval → audit → execution → verification → rollback lifecycle. All routes under `/api/v1/agents` now return `410 LEGACY_DIRECT_AGENT_COMMAND_API_RETIRED`; the service no longer imports broker, signing, capability, or direct-dispatch components. The independent canonical endpoint-signature protocol and its agent-side verification regressions remain source-covered, but they are not an authorization, approval, or execution claim.

> **Evidence boundary:** this is Class A source-and-isolated-test evidence. It does not provide a governed endpoint-command replacement or validate tenant-owned endpoint identity, approval identity, audit durability, signing-key custody, broker authorization, endpoint execution, verification, rollback, Wazuh/EDR integration, Docker-host operation, or containment efficacy.

## Completed bounded increment: dashboard agent-management truthfulness boundary

The dashboard’s agent-management view no longer presents fixture agents, simulated online/quarantined/offline state, fabricated heartbeat/certificate/CPU telemetry, or in-memory approve, revoke, and quarantine controls as product capability. The former add-agent action is also removed. The view now clearly states that legacy agent enrollment and lifecycle controls are retired and that a governed, tenant-scoped endpoint control plane must provide request-bound, human-approved, auditable, verified, and rollback-capable actions before operational fleet controls can return. Regression coverage prevents reintroduction of fixture data, simulated lifecycle handlers, action-menu controls, or stale legacy agent paths.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide a governed endpoint integration, endpoint identity, inventory accuracy, telemetry delivery, certificate lifecycle, lifecycle authorization, approval/audit durability, command execution, verification, rollback, device packaging, Docker-host operation, or endpoint-security efficacy.

## Completed bounded increment: dashboard self-healing truthfulness boundary

The dashboard self-healing console no longer polls a retired legacy agent API, renders unauthenticated endpoint health/error/certificate data, or presents placeholder repair, patch, recovery, safe-mode, or self-healing controls as usable actions. It now states that autonomous endpoint status and remediation controls are retired pending a governed response integration. Any future capability must be tenant-scoped and evidence-bound, with human approval for high-impact action plus audit, verification, and rollback before it can appear as an operational control. Regression coverage prevents the stale polling path and simulated action language from being restored.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide endpoint telemetry, a self-healing or remediation adapter, policy evaluation, endpoint identity, approval/audit durability, execution, verification, rollback, device packaging, Docker-host operation, or remediation/containment efficacy.

## Completed bounded increment: dashboard malware-sandbox truthfulness boundary

The dashboard malware-sandbox page no longer uploads suspicious files to the retired sandbox API or presents behavioral, network, cryptographic, artifact, verdict, hash, raw-output, or analysis-ID data as real analysis result. It now states that the legacy file-upload and sandbox-analysis control is retired pending an isolated, governed integration. A future workflow must provide authorized submission, isolated execution, tenant-scoped evidence handling, auditable lifecycle control, and validated result provenance before it is exposed as operational capability. Regression coverage prevents the direct upload request and unsupported result components from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide file submission, malware execution, sandbox isolation, authorization, tenant isolation, evidence retention, result provenance, verdict accuracy, external-analysis provider authorization, Docker-host operation, or malware-detection efficacy.

## Completed bounded increment: dashboard SIEM-integration truthfulness boundary

The dashboard SIEM-integration page no longer creates, lists, configures, or exposes connection data for the retired SIEM integration API, and it no longer submits test events to external platforms. It now states that the legacy connection and forwarding controls are retired pending a governed telemetry integration. A future integration must keep provider credentials outside the client, maintain tenant-scoped configuration, enforce policy-bound routing, produce auditable delivery records, and independently validate provider behavior before it is presented as operational capability. Regression coverage prevents the stale connection-management, configuration-disclosure, and event-forwarding code from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide provider authorization, credential custody, tenant isolation, connection management, event routing, delivery guarantees, SIEM ingestion, raw-data privacy, audit durability, Docker-host operation, or telemetry/detection efficacy.

## Completed bounded increment: dashboard vulnerability-scanner truthfulness boundary

The dashboard vulnerability-scanner page no longer accepts targets or configuration data, invokes the retired scanner API, or presents port, CVE, configuration-alert, or vulnerability-finding data as operational result. It now states that target-scanning and configuration-analysis controls are retired pending an authorized, governed assessment integration. A future workflow must require authorized targets, tenant-scoped scope and evidence, policy-bound execution, auditable lifecycle records, rate-limit control, and independently validated results before it is exposed as operational capability. Regression coverage prevents direct scanner requests and unsupported finding views from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide target authorization, scan execution, CVE coverage, asset discovery, configuration assessment, tenant isolation, evidence retention, rate-limit control, provider authorization, result accuracy, Docker-host operation, or vulnerability-detection efficacy.

## Completed bounded increment: dashboard vulnerability-management truthfulness boundary

The dashboard vulnerability-management page no longer presents fixture asset inventory, fabricated scan progress, CVE exposure, risk scores, patch posture, AI remediation rationale, or remote patch actions as live security operations. It now states that these controls are retired pending governed assessment and change-management integration. A future workflow must establish authorized asset ownership, tenant-scoped inventory and evidence, validated finding provenance, advisory-only recommendations, human-approved change control for remediation, audit, verification, and rollback before it is exposed as operational capability. Regression coverage prevents fixture content, simulated assessment behavior, AI remediation claims, and remote patch controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide asset inventory, scan execution, CVE coverage, risk scoring, AI recommendation efficacy, patch/change execution, approval identity, audit durability, verification, rollback, provider authorization, Docker-host operation, or vulnerability/remediation efficacy.

## Completed bounded increment: dashboard marketplace truthfulness boundary

The dashboard marketplace no longer presents fixture XDR, honeypot, AI, or blockchain plugins, simulated signature validity, simulated enablement state, or browsing/inspection controls as live extension capability. It now states that the fixture extension catalogue and controls are retired pending a governed extension lifecycle. A future lifecycle must establish trusted provenance, tenant-scoped configuration, reviewable permissions, approval-bound activation, durable audit evidence, rollback, and validated runtime isolation before it is exposed as operational capability. Regression coverage prevents fixture records, signature/enablement state, and extension controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide extension sourcing, signature verification, authorization, tenant isolation, permission review, activation, runtime isolation, rollback, marketplace provider authorization, Docker-host operation, or extension-security efficacy.

## Completed bounded increment: dashboard compliance-reporting truthfulness boundary

The dashboard compliance-reporting page no longer generates, lists, inspects, scores, or downloads retired report artifacts, and it no longer presents control findings or compliance semantics as live evidence. It now states that the legacy reporting control is retired pending a governed compliance-evidence integration. A future workflow must establish tenant-scoped evidence, policy-controlled report generation, durable audit records, authorized artifact access, retention controls, and independently validated control mappings before it is exposed as operational capability. Regression coverage prevents retired reporting APIs, audit scores/findings, and PDF-download controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide compliance report generation, report authorization, tenant isolation, evidence provenance, control-evaluation completeness, artifact retention, audit durability, PDF integrity, independent attestation, Docker-host operation, or compliance efficacy.

## Completed bounded increment: dashboard forensics truthfulness boundary

The dashboard forensics page no longer presents fixture acquisition jobs, evidence-vault artifacts, reconstructed attack timelines, custody-integrity assertions, artifact acquisition, or report-export controls as live investigative capability. It now states that these controls are retired pending governed forensics integration. A future workflow must establish authorized collection targets, tenant-scoped evidence, immutable custody records, controlled artifact access, validated timeline provenance, policy-bound task execution, human approval where required, retention controls, verification, and rollback before it is exposed as operational capability. Regression coverage prevents fixture forensic state and retired task/evidence/export controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide forensic collection, endpoint acquisition, evidence custody, cryptographic integrity, artifact access, timeline reconstruction, authorization, tenant isolation, task execution, retention, verification, rollback, Docker-host operation, or investigative efficacy.

## Completed bounded increment: dashboard cloud-security truthfulness boundary

The dashboard cloud-security page no longer accepts caller-supplied cloud credentials, queries cloud resources, enumerates buckets, checks IAM abuse or cloud misconfiguration, or presents fixture cloud-security findings as operational result. It now states that the legacy cloud control is retired pending governed cloud integration. A future integration must use authorized credentials held outside the client, tenant-scoped provider authorization, policy-bound scope, auditable read-only collection, rate-limit controls, validated finding provenance, and approved change control for remediation before it is exposed as operational capability. Regression coverage prevents caller credential handling, retired cloud requests, and finding controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide cloud-account authorization, credential custody, resource discovery, bucket enumeration, IAM analysis, configuration assessment, tenant isolation, provider rate-limit behavior, evidence provenance, remediation, Docker-host operation, or cloud-security efficacy.

## Completed bounded increment: dashboard SOAR truthfulness boundary

The dashboard SOAR page no longer presents fixture playbooks, simulated approvals, manual mitigation, execution status, firewall blocks, blockchain assertions, or containment outcomes as live operations. It now states that the legacy view is retired pending dashboard integration with the separately protected governed containment control plane. A future dashboard integration must remain tenant-scoped and capability-protected, issue a request before human decision, retain HMAC-signed audit evidence, use controlled adapters, verify execution, and support rollback; high-impact containment must never become automatic through the client. Regression coverage prevents fixture SOAR state and retired response controls from returning while preserving the governed containment tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide a dashboard-to-containment integration, playbook lifecycle, endpoint or network control, approval identity, audit durability, blockchain integrity, adapter execution, verification, rollback, Docker-host operation, or containment efficacy.

## Completed bounded increment: dashboard attack-path visualization truthfulness boundary

The dashboard threat-graph canvas no longer presents a placeholder attack-path map, relationship data, or inert graph controls as live investigation capability. It now states that the visualization is pending integration with the separately protected attack-path API. A future visualization must query tenant-scoped, authorized, provenance-linked results and distinguish graph hypotheses from verified evidence before it is exposed as operational capability. Regression coverage prevents placeholder graph claims and inert controls from returning while preserving the governed attack-path contract tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide a dashboard-to-graph integration, attack-path discovery, relationship accuracy, asset exposure analysis, tenant isolation, result provenance, graph evidence verification, deployment operation, or detection/investigation efficacy.

## Completed bounded increment: dashboard advisory decision-evidence truthfulness boundary

The dashboard advisory decision-evidence page no longer polls an unsupported AI endpoint or presents decision logs, confidence values, execution traces, agent outcomes, raw details, or autonomous-action claims as live capability. It now states that advisory evidence-log integration is pending. A future view must use tenant-scoped, provenance-linked observations; minimize displayed evidence; distinguish recommendations from deterministic findings; remain policy-gated and non-executing; and preserve approval-bound containment rather than implying autonomous remediation. Regression coverage prevents unsupported AI polling and autonomous-decision claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide a dashboard-to-advisory-log integration, AI decision provenance, confidence calibration, model efficacy, raw evidence authorization, tenant isolation, autonomous enforcement, containment execution, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard network-overview truthfulness boundary

The dashboard network-overview page no longer connects to an unscoped network WebSocket or displays real-time traffic, active connections, anomaly counts, or blocked-threat metrics. It now states that governed network-evidence integration is pending. Any future network view must use a protected tenant-scoped analyst workflow with authorization-checked, provenance-linked, validated and minimized observations; identify data currency and collection boundaries; distinguish network observations from verified detections; retain deterministic auditability; and remain read-only and non-enforcing. It must not imply live network visibility, threat blocking, automatic containment, or response execution. Regression coverage prevents the direct stream client and unsupported network-metric claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-network-evidence integration, live network collection, connection or traffic accuracy, anomaly or blocking accuracy, source authorization, tenant isolation, observation provenance, data validation or minimization, audit durability, containment, response execution, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard alert-evidence truthfulness boundary

The dashboard alerts page no longer polls an unsupported alert endpoint or displays alert identifiers, rule names, endpoint identifiers, severity, timestamps, or raw details. It now states that governed alert-evidence integration is pending. Core detection, correlation, and analyst workflow services remain separately protected. Any future dashboard integration must use tenant-scoped, authorization-checked, provenance-linked alert evidence; minimize sensitive fields; distinguish deterministic detections from analyst interpretation; retain auditable retrieval and lifecycle transitions; and remain non-enforcing with no containment or response authority. Regression coverage prevents direct polling, timed refresh, raw alert-table disclosure, and unproven alert fields from returning while preserving alert-workflow and analyst-context tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-alert integration, live alert delivery, analyst identity or capability enforcement, tenant isolation, evidence provenance or minimization, alert completeness, rule or severity accuracy, lifecycle-transition execution, audit durability, containment, response execution, Docker-host operation, or detection/response efficacy.

## Completed bounded increment: dashboard log-viewer truthfulness boundary

The dashboard log viewer no longer replays fixture logs on a timer or exposes local formatting, copy, export, clear, or inert advanced-search controls. The unused log-viewer simulator components have been removed. It now states that governed log-evidence integration is pending. Any future log view must use a protected tenant-scoped analyst workflow with authorization-checked, provenance-linked, minimized results; constrain queries and exports; redact or gate sensitive fields; retain deterministic auditability; and distinguish observed raw telemetry from verified analytical findings. It must not imply live ingestion, log completeness, detection efficacy, automatic containment, or response execution. Regression coverage prevents fixture streaming, fabricated security events, and local disclosure controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-log-evidence integration, live ingestion, source authorization, tenant isolation, log completeness or integrity, query or export authorization, sensitive-data minimization, audit durability, detection accuracy, containment, response execution, Docker-host operation, or investigative efficacy.

## Completed bounded increment: dashboard graph-investigation truthfulness boundary

The dashboard graph-investigation page no longer accepts Cypher or other arbitrary graph queries, executes direct raw-graph searches, or renders raw relationship results. It now states that governed graph-investigation integration is pending. The separately protected governed graph and attack-path APIs remain the supported read-only investigation boundaries. Any future dashboard integration must use tenant-scoped, authorization-checked, provenance-linked results; expose only safe structured investigation inputs; minimize returned evidence; distinguish graph hypotheses from verified findings; and remain non-enforcing with no containment or response authority. Regression coverage prevents the direct raw-graph client, arbitrary Cypher input, and unbounded result disclosure from returning while preserving graph-service and governed attack-path contract tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-governed-graph integration, graph query execution, Neo4j authorization, tenant isolation, source provenance, result correctness or minimization, analyst authorization enforcement, graph data durability, attack-path accuracy, containment, response execution, Docker-host operation, or investigative efficacy.

## Completed bounded increment: dashboard case-management truthfulness boundary

The dashboard case-management page no longer calls the direct legacy case surface or exposes case creation, listing, inspection, assignment, status updates, notes, timeline, playbook-status, or hard-coded playbook-execution controls. It now states that governed case-lifecycle integration is pending. The separately protected governed case lifecycle remains the supported control plane. Any future dashboard integration must bind cases to authenticated tenant-owned alerts, enforce analyst capabilities and tenant scope for every lookup and transition, minimize displayed evidence, retain auditable state transitions, and keep playbook runs approval-bound and non-executing until a separately governed response lifecycle performs request, human approval, HMAC-signed audit, controlled execution, verification, and rollback. Regression coverage prevents the direct legacy client and its unsupported lifecycle controls from returning while preserving governed case-service boundary tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-governed-case integration, case creation or transition execution, analyst identity or capability enforcement, tenant isolation, evidence authorization or minimization, case-history durability, playbook execution, approval identity, audit durability, verification, rollback, Docker-host operation, or incident-response efficacy.

## Completed bounded increment: dashboard global-evidence visualization truthfulness boundary

The dashboard global map no longer presents mock regional hotspots, animated attack vectors, regional risk labels, latency measurements, active-threat counts, or global activity as security telemetry. It now states that governed global-evidence visualization integration is pending. Any future visualization must consume tenant-scoped, provenance-linked and minimized evidence through a protected analyst workflow; distinguish source geography from verified attacker attribution; disclose data currency and availability; and remain read-only, advisory, and non-enforcing. It must not claim live global visibility, threat-detection efficacy, automatic containment, or response execution. Regression coverage prevents the mock map state, visual effects, and numerical claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-evidence integration, global telemetry collection, geographic source accuracy, attacker attribution, data currency, provider authorization, analyst authorization enforcement, tenant isolation, evidence minimization, audit durability, detection efficacy, containment, response execution, Docker-host operation, or operational global visibility.

## Completed bounded increment: dashboard network-segmentation truthfulness boundary

The dashboard network-segmentation page no longer requests unsupported topology or segmentation-violation endpoints, renders a client-side force-directed network map, or displays raw source and destination identifiers. The unused topology renderer has been removed. The page now states that governed segmentation-evidence integration is pending. Any future view must use tenant-scoped, provenance-linked evidence through a protected analyst workflow; minimize sensitive identifiers; distinguish observed relationships from verified policy violations; preserve deterministic auditability; and avoid claims of live topology accuracy, policy enforcement, active network control, automatic containment, or incident-response execution. Regression coverage prevents the direct fetches, topology component, raw-table interface, and unproven violation fields from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-evidence integration, live topology discovery, segmentation-policy evaluation, relationship or violation accuracy, analyst authorization enforcement, tenant isolation, evidence provenance, result minimization, audit durability, policy enforcement, network control, containment, Docker-host operation, or detection/response efficacy.

## Completed bounded increment: dashboard network-threat truthfulness boundary

The dashboard network-threat page no longer requests an unsupported direct endpoint or renders raw source addresses, timestamps, and threat labels. It now states that governed network-threat evidence integration is pending. Any future analyst view must consume tenant-scoped, provenance-linked evidence through a protected workflow, minimize sensitive network identifiers, distinguish observations from verified findings, preserve deterministic auditability, and avoid implying active network control, automatic containment, or incident-response execution. Regression coverage prevents the direct fetch, raw-table interface, and unproven threat-result fields from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-evidence integration, live network telemetry, threat detection, source-address accuracy, analyst authorization enforcement, tenant isolation, evidence provenance, result minimization, audit durability, network control, containment, Docker-host operation, or detection/response efficacy.

## Completed bounded increment: dashboard OSINT truthfulness boundary

The dashboard OSINT page no longer generates randomized reputation scores, malicious-report counts, geolocation, provider, indicator, or timeline values, and it no longer presents placeholder OSINT evidence panels as capability. The local simulated search and result-card components have been removed. The page now states that governed advisory-enrichment integration is pending; the separately protected threat-intelligence service remains the supported advisory boundary. Any future dashboard integration must require analyst authorization, constrain and validate indicator input, preserve tenant scope and evidence provenance, minimize displayed provider data, expose availability without provider exception detail, and remain advisory-only with no response authority. Regression coverage prevents simulated enrichment state, OSINT claims, and stale components from returning while preserving the guarded threat-intelligence service boundary tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-enrichment integration, provider authorization, live lookup execution, reputation or geolocation accuracy, indicator coverage, source provenance, analyst authorization enforcement, tenant isolation, data minimization, audit durability, Docker-host operation, or intelligence/detection efficacy.

## Completed bounded increment: dashboard SIEM direct-legacy-query truthfulness boundary

The dashboard SIEM overview no longer sends direct requests to the retired PhantomQL service or renders raw log-search results. The obsolete direct localhost client component and service have been removed. The page now states that governed log-search integration is pending and identifies the separately protected threat-hunting capability as the supported analysis boundary. Any future dashboard integration must enforce tenant scope and analyst authorization, use evidence-linked and minimized results, and preserve deterministic auditability rather than exposing a direct legacy query endpoint. Regression coverage prevents the deleted PhantomQL client, hard-coded local URL, query payload, and raw-table interface from returning while preserving the legacy fail-closed and threat-hunting service tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-threat-hunting integration, live log ingestion, query execution, result provenance, analyst identity, authorization enforcement, tenant isolation, evidence minimization, audit durability, Docker-host operation, or detection/investigation efficacy.

## Completed bounded increment: dashboard attack-graph truthfulness boundary

The dashboard attack-graph page no longer presents fixture lateral-movement topology, compromise/risk assertions, segmentation findings, blast-radius estimates, or local simulated node isolation as live capability. It now states that governed attack-path and containment integration is pending. The separately protected attack-path analysis and governed containment control planes remain the only supported boundaries. Any future dashboard integration must use tenant-scoped, provenance-linked results; distinguish graph hypotheses from verified evidence; and retain request, human approval, HMAC-signed audit, controlled execution, verification, and rollback without automatic high-impact containment. Regression coverage prevents fixture graph state and simulated containment from returning while preserving governed attack-path and containment contract tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide a dashboard-to-analysis integration, attack-path discovery, relationship accuracy, risk scoring, segmentation assessment, containment execution, approval identity, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.

## Completed development increment: Phase 7

Phase 7 now provides a **self-hosted deployment and observability reference architecture**. The new Compose topology isolates PostgreSQL, Redis, Redpanda, and Neo4j on an internal network; exposes the gateway and Prometheus only through loopback ports; health-gates the control-plane startup; pins service images; protects stateless services with read-only filesystems and dropped capabilities; and requires every credential to be injected outside source control.

The standard service factory now exposes bounded, Prometheus-compatible process counters. Readiness continues to combine upstream dependency checks with secret-safe runtime posture, while the existing recovery harness remains the minimum Docker-host proof for broker, database, and HMAC audit-chain recovery. The architecture documentation defines backup, restore, upgrade, ingress, and external Docker-host validation requirements without claiming a live deployment from this sandbox.

> **Phase 7 closure rule:** internal topology is not public ingress, liveness is not readiness, static Compose proof is not live-host proof, and a successful start does not replace backup, recovery, audit-chain, or operator acceptance evidence.

## Sequencing principles

The roadmap is intentionally core-first. It prioritizes safety and operability over additional integrations, and it builds every new adapter around the same canonical contracts, RBAC, tenant isolation, audit-chain rules, and test harnesses. Deployment validation cannot be represented as complete until it runs on Docker-capable infrastructure; similarly, real cloud validation remains a separate non-production lab gate rather than a sandbox action.
