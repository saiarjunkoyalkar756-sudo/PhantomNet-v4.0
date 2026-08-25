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

## Completed bounded increment: login truthfulness and server-authority boundary

The login page no longer displays randomized operational telemetry, presents client-selected administrative roles, claims global containment capability, or makes unsupported cryptographic assurances. It retains the server-authoritative authentication request and MFA-required transition. Access roles are assigned by server-side policy, not the form. Regression coverage preserves authentication and MFA paths while preventing fixture operations and client role framing from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not prove live identity-provider availability, credential security, MFA delivery, session integrity, role enforcement, tenant isolation, cryptographic handshakes, production deployment, or defensive efficacy.

## Completed bounded increment: dashboard security-validation truthfulness boundary

The security-validation dashboard no longer simulates attack playbook execution, report viewing, or new simulations. It now states that authorized security-validation integration is pending. Any future workflow must require explicit authorization, tenant and target scope, bounded execution in an approved environment, evidence-linked results, independent safety controls, and immutable audit records. It must not create autonomous containment or production-impacting response authority. Regression coverage prevents simulated playbook and report controls from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide test authorization, target permission, validation execution, environmental isolation, finding accuracy, report generation, production safety, containment, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard compliance-evidence truthfulness boundary

The compliance dashboard no longer runs simulated audits, calculates fixture framework posture, presents fabricated findings or AI remediation, or implies report generation. It now states that governed compliance-evidence integration is pending. Any future workflow must use authorized tenant-scoped evidence, validated control mappings, reproducible assessment methods, source-linked findings, appropriately authorized report generation, and auditable review. Recommendations must remain advisory; remediation requires separately governed human approval, verification, and rollback. Regression coverage prevents fixture compliance claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide compliance assessment, control mapping accuracy, audit execution, report generation, evidence authorization, tenant isolation, recommendation efficacy, remediation, Docker-host operation, or regulatory assurance.

## Completed bounded increment: dashboard governed-configuration truthfulness boundary

The settings dashboard no longer simulates autonomous-defense activation, threat-scoring changes, log-level changes, or successful configuration saves. It now states that governed configuration integration is pending. Any future workflow must enforce privileged authorization and tenant scope, validate policy and safe defaults, record immutable auditable changes, require approval for high-impact settings, and preserve verification and rollback. AI remains advisory-only and cannot enable automated containment through the dashboard. Regression coverage prevents unsupported mutable settings behavior from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide configuration integration, privileged authorization, policy validation, change persistence, audit durability, approvals, verification, rollback, automatic containment, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard event-evidence truthfulness boundary

The event-stream dashboard no longer connects to an unscoped event WebSocket, retains events in browser state, filters endpoint data, or exposes raw event details. It now states that governed event-evidence integration is pending. Any future event view must use a protected tenant-scoped analyst workflow with authorization-checked, provenance-linked, validated and minimized observations; constrain filters and returned fields; retain deterministic auditability; and distinguish collected telemetry from verified detections. It must remain read-only and non-enforcing, with no containment or response authority. Regression coverage prevents the unscoped stream client and raw evidence interface from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide live event collection, source authorization, tenant isolation, event integrity or completeness, query or filter authorization, evidence provenance, analyst authorization, containment, response execution, Docker-host operation, or detection efficacy.

## Completed bounded increment: unused agent-detail component retirement

The unreferenced legacy agent-detail component has been removed. It previously rendered raw agent identity, status, heartbeat, address, load, certificate, and metadata values without an active tenant-scoped governed agent-lifecycle dashboard integration. Regression coverage requires the deleted component to remain absent. Any future detail view must use tenant-scoped, authorization-checked, provenance-linked, minimized observations and must not imply direct lifecycle or containment authority.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide agent inventory, endpoint telemetry, identity validation, certificate state, tenant isolation, lifecycle actions, containment, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard advisory-chat truthfulness boundary

The dashboard conversational copilot no longer accepts prompts, returns AI explanations, retrieves operational status, or implies playbook or defensive-action authority. It now states that governed advisory AI integration is pending. Any future advisory integration must use evidence-minimized, tenant-scoped, provenance-linked inputs; remain policy-gated and non-executing; identify recommendations as advisory; and preserve approval-bound containment with HMAC-signed audit, verification, and rollback outside the chat interface. Regression coverage prevents the unsupported copilot client and action claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-AI integration, model availability, prompt handling, evidence authorization, tenant isolation, recommendation accuracy, action authority, containment, verification, rollback, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard administration truthfulness boundary

The administrative dashboard no longer polls an unsupported alert endpoint, reports hard-coded agent or user counts, asserts operational health, or provides implied action shortcuts. It now states that governed administration integration is pending. Any future administration surface must enforce authenticated role and tenant scope; use authorization-checked, provenance-linked, minimized data; distinguish readiness signals from production availability; audit all changes; and keep high-impact actions within their separately governed approval, audit, verification, and rollback lifecycles. Regression coverage prevents the unsupported client and operational claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide dashboard-to-administration integration, live alert or inventory data, user or agent counts, operational health, role enforcement at the UI boundary, tenant isolation, change auditing, high-impact execution, verification, rollback, Docker-host operation, or defensive efficacy.

## Completed bounded increment: dashboard threat-hunting summary truthfulness boundary

The dashboard home view now retains only the protected threat-hunting summary read path and no longer presents global-command framing, autonomous orchestration, inert new-investigation controls, live-propagation labeling, fabricated remediation results, or mock AI chat. It explicitly states that dashboard actions, global telemetry, and AI assistance require separately authorized integrations. Any future dashboard expansion must retain tenant-scoped authorization, evidence provenance and minimization, deterministic auditability, and advisory non-enforcing boundaries. Regression coverage preserves the governed summary service path while preventing unsupported autonomous, remediation, chat, and propagation claims from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide global visibility, autonomous orchestration, dashboard action authority, new-investigation creation, live propagation, remediation execution or success, AI assistant integration or efficacy, tenant isolation at the UI boundary, Docker-host operation, or defensive efficacy.

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


## Completed bounded increment: dashboard MFA credential-lifetime boundary

The dashboard MFA transition no longer writes the primary password or username into `sessionStorage`. The existing login route keeps the pending credentials only in module memory for the active single-page challenge; the challenge clears that handoff after a successful login and whenever the challenge route unmounts. A refreshed, restored, or directly opened challenge therefore fails closed and requires a new sign-in rather than recovering a persisted password. The MFA replay now uses the same form-encoded `/auth/token` contract as the active login route, forwards either a six-digit TOTP code or the server-defined ten-character alphanumeric recovery code, and continues to consume the server-issued token and role response rather than making a client-side authorization decision. The self-registration client now follows the same normalized API-base path convention through `/auth/register`. Regression coverage prevents persistent-browser storage, stale response-shape handling, mismatched API prefixes, and an obsolete challenge URL from returning.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not prove browser-memory isolation against a compromised client, MFA enrollment or recovery-code lifecycle security, server-side rate-limit behavior, session fixation resistance, authentication availability, identity proofing, tenant isolation at every IAM route, production deployment, or overall account-security efficacy. A server-minted, single-use MFA continuation credential remains future work if the authentication API is redesigned.


## Completed bounded increment: unreferenced dashboard legacy-client retirement

The dashboard source no longer contains unreferenced direct clients for legacy SOAR playbooks, vulnerability-management assets, or the retired SOC copilot, nor the only components that imported the SOAR and vulnerability clients. These files hard-coded a localhost service address and exposed legacy CRUD, playbook-run, unscoped asset, advisory-query, or fixture security-validation concepts that no longer corresponded to an active supported control path. The unreferenced simulated red-team playbook component has also been removed. This does not change the separately protected governed containment API, governed case lifecycle, or the dashboard’s retained read-only threat-hunting summary path; the threat-hunting client remains present and regression-covered.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not add a dashboard integration to governed containment, case management, vulnerability assessment, advisory AI, or security validation; it does not prove analyst authorization, tenant isolation, operational API availability, Docker-host deployment, response execution, or defensive efficacy. The deletion only removes stale unsupported client claims and local direct-client paths.


## Completed bounded increment: dashboard fabricated-event simulator retirement

The dashboard’s unreferenced WebSocket simulator has been removed. It hard-coded a localhost endpoint, generated randomized event types, severities, endpoint names, source addresses, timestamps, and AI-insight statements, then injected them into client state on a timer. It had no import path from any mounted dashboard route and could not support a defensible product claim. The retained dashboard summary and threat-hunting workflows continue to use their separately governed API clients; this retirement removes only a fabricated local-event pathway.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not establish a live event-stream integration, event integrity or completeness, source authorization, tenant isolation, evidence provenance, dashboard freshness, detection efficacy, containment, response execution, Docker-host operation, or defensive efficacy.


## Completed bounded increment: unmounted dashboard MFA-setup retirement

The unmounted dashboard MFA-setup page has been removed. It was not registered in the router, used API paths and response-envelope handling inconsistent with the active dashboard client, and displayed the TOTP seed and recovery codes in a client flow with no reachable product boundary. The removal does not retire the server-side authenticated MFA enrollment and verification routes, and it does not change the active server-authoritative login-to-MFA challenge. Any future account-security settings page must be deliberately routed behind an authenticated account boundary, use the normalized client contract, minimize secret display, and have dedicated enrollment, recovery-code, and cancellation-lifecycle tests.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate the retained MFA enrollment API, TOTP correctness, recovery-code lifecycle, identity proofing, user authorization, secret handling in a browser, session integrity, rate-limit behavior, tenant isolation, production deployment, or account-security efficacy.


## Completed bounded increment: unmounted dashboard AI-console retirement

The unmounted dashboard AI-console page has been removed. Although its embedded advisory component now accurately states that integration is pending, the page itself still claimed an interactive AI security analyst was online. No router registered the page and no source imported it. Removing the stale availability framing preserves the separate governed advisory-integration notice, which remains policy-gated and non-executing, while preventing an unreachable component from being mistaken for a live conversational defensive capability.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not provide advisory AI availability, model behavior, prompt handling, evidence authorization, tenant isolation, recommendation quality, provider authorization, analyst workflow integration, containment authority, Docker-host operation, or defensive efficacy.


## Completed bounded increment: orphaned gateway alert-manager retirement

The unmounted `gateway_service/alert_manager_api.py` module has been removed after source tracing confirmed no imports, router inclusion, or test dependency. It maintained in-memory alert and agent-status stores, exposed unauthenticated alert and agent-status WebSockets, assumed a localhost Kafka path, and allowed caller-driven alert simulation. This retirement does not modify the separately active alert-storage service or governed analyst workflows; it removes only a dormant legacy gateway module that could be accidentally remounted or misrepresented as an operational alert-control plane.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not prove the active alert-storage service’s deployment, broker connectivity, data durability, authorization, tenant isolation, alert evidence provenance, stream integrity, real-time delivery, analyst workflow behavior, containment, response execution, or defensive efficacy.


## Completed bounded increment: orphaned gateway dashboard-module retirement

Two unmounted legacy gateway dashboard modules have been removed after source tracing confirmed they had no active imports, router inclusion, or tests. One accepted raw PNQL queries against fixture logs and threats with commented authorization checks; the other exposed fabricated incident details, attack paths, SOAR previews, executive metrics, remediation counts, risk trends, and security claims. This does not modify the independently active dashboard service, the protected threat-hunting summary, governed attack-path analysis, alert storage, case workflow, or containment controls. It removes only dormant modules that could otherwise be accidentally remounted or treated as product evidence.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate any dashboard service deployment, PNQL or hunting semantics, data authorization, tenant isolation, evidence provenance, analytics accuracy, threat detection, remediation, executive reporting, alert delivery, containment, response execution, Docker-host operation, or defensive efficacy.


## Completed bounded increment: orphaned gateway WebSocket-router retirement

The unmounted `gateway_service/websocket_api.py` router has been removed after reachability tracing confirmed no imports or router inclusion. It accepted JWTs in query parameters and exposed event and log streams without tenant or capability controls. The gateway background event and log helpers remain unchanged because they are separately referenced, and separately routed WebSocket modules outside this orphan gateway router were not altered. This increment only prevents accidental remounting of the legacy query-token stream surface.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate any remaining WebSocket route, authentication, authorization, token confidentiality, tenant isolation, event or log provenance, stream integrity, delivery, retention, broker connectivity, operational monitoring, Docker-host operation, or defensive efficacy.


## Completed bounded increment: orphaned gateway policy-router retirement

The unmounted `gateway_service/policy_api.py` router has been removed after reachability tracing confirmed no imports or router inclusion. It allowed in-memory policy creation, update, deletion, and disclosure without authentication, authorization, tenant scope, durable storage, approval, audit, verification, or rollback. The removal does not change separately governed capability-protected configuration controls or approved response governance; it prevents accidental remounting of an unscoped policy-control surface.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate remaining configuration controls, policy evaluation, authorization, tenant isolation, persistence, audit durability, approval, verification, rollback, enforcement, Docker-host operation, or defensive efficacy.


## Completed bounded increment: orphaned gateway threat-intelligence-router retirement

The unmounted `gateway_service/threat_intelligence_api.py` router has been removed after source tracing confirmed no imports or router inclusion. It accepted unauthenticated IOC submissions and alert feedback, hard-coded the submitting identity, and retained records only in process memory while presenting a conceptual threat-intelligence and AI-feedback lifecycle. The removal does not change separately governed intelligence, detection, or analyst workflows; it prevents accidental remounting of an unscoped and non-durable intake surface.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate intelligence ingestion, IOC vetting, source authorization, tenant isolation, provenance, persistence, data quality, feedback handling, AI learning, detection efficacy, analyst workflows, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy log-service retrieval retirement

The source-reachable standalone log-service retained global raw attack-log and SIEM-polling endpoints despite no tenant identifier on the legacy `AttackLog` model and no tenant filter on either retrieval path. Both routes now return a distinct 410 retirement contract, and the service status no longer claims raw-log retrieval is operational. The log service is not part of the hardened self-hosted reference, and the dashboard log viewer already states that governed evidence integration is pending. This change preserves the service boundary while preventing global raw-data disclosure until a tenant-scoped evidence integration is designed and validated.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate a replacement log-service deployment, raw-log ingestion, broker connectivity, data durability, authorization, tenant isolation, provenance, data minimization, analyst retrieval, retention, observability, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy SIEM ingestion retirement

The source-reachable standalone SIEM ingestion service exposed unauthenticated single and batch raw-log ingestion plus global raw-record lookup and listing. Its legacy data model did not establish source identity, tenant scope, or durable evidence provenance, and the service is absent from the hardened self-hosted reference. The four compatibility routes now return a distinct 410 retirement contract and the service status reports the retired state. This does not alter the separately governed endpoint-inventory telemetry integration, which uses capability checks and tenant-scoped Wazuh ingestion and evidence handling.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate a replacement SIEM deployment, telemetry ingestion, forwarder authentication, tenant isolation, source provenance, data durability, broker operation, evidence handling, alert correlation, analyst retrieval, Wazuh integration, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy log-normalizer retirement

The source-reachable standalone log-normalizer service exposed unauthenticated single and batch raw-log normalization without source identity, tenant scope, or evidence provenance. Its helper functions and HTTP routes had no external imports, and the service is separate from the canonical event-normalizer pipeline. The two compatibility routes now return a distinct 410 retirement contract and the service status reports the retired state. This change does not alter the canonical pipeline’s versioned event handling; it prevents accidental reuse of unscoped HTTP normalization as a SOC telemetry boundary.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate the canonical normalization pipeline, telemetry ingestion, source authentication, tenant isolation, schema mapping, event fidelity, broker connectivity, data durability, downstream correlation, detection efficacy, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy network WebSocket retirement

The source-reachable standalone network WebSocket service accepted telemetry after a fixed in-code agent-ID and client-supplied platform-hash check, then published arbitrary JSON directly to the normalized-event broker topic. It had no tenant scope, operator-provisioned credential, canonical signature verification, durable receipt, source provenance, or governed adapter boundary. The WebSocket now closes with a policy-violation retirement reason before accepting a connection or telemetry, and startup no longer connects a direct broker producer. This does not modify separately governed signed telemetry credential controls or tenant-scoped forwarder integrations.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate signed telemetry, agent identity, credential provisioning, tenant isolation, broker connectivity, event delivery, durability, source provenance, forwarder integration, Wazuh integration, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy command-dispatcher retirement

The source-reachable standalone command-dispatcher service started a direct consumer for the `agent-commands` broker topic and reported a command-dispatch lifecycle despite no canonical signature verification, tenant boundary, approval linkage, HMAC audit linkage, controlled adapter, verification, or rollback. The consumer and Kafka dependency are removed; its detailed status now reports the retired boundary. This does not modify the separate fail-closed direct agent-command API, canonical signing tests, or human-approved governed containment lifecycle.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate canonical signing in a deployed environment, agent identity, operator credential provisioning, authorization, tenant isolation, broker connectivity, audit durability, containment approval, adapter execution, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: simulated forensic evidence-collector retirement

The unmounted forensic evidence-collector router has been removed after source tracing confirmed no application import, router inclusion, deployment reference, or test dependency. It accepted arbitrary asset and job identifiers without authentication or tenant scope, fabricated memory dumps, archives, registry hives, storage paths, sizes, artifact identities, and completion claims, and logged simulated collection data. The separately fail-closed forensics-engine boundary and governed tenant-scoped evidence-intake path remain unchanged.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate forensic collection, asset identity, authorization, tenant isolation, evidence provenance, storage, chain of custody, integrity verification, analyst workflow, Docker-host operation, or defensive efficacy.


## Completed bounded increment: simulated forensic timeline-builder retirement

The unmounted forensic timeline-builder router has been removed after source tracing confirmed no application import or router inclusion. It accepted arbitrary asset identifiers and fabricated malware process, C2 network, filesystem, identity, timestamp, and completed-timeline claims without authentication, tenant scope, evidence provenance, or actual data collection. The legacy root development compose reference may still instantiate the already fail-closed forensics engine, but does not mount this module. The separately fail-closed forensics-engine boundary and governed tenant-scoped evidence-intake path remain unchanged.

> **Evidence boundary:** this is Class A source-and-build evidence. It does not validate forensic timeline construction, asset identity, authorization, tenant isolation, evidence provenance, source collection, chain of custody, integrity verification, analyst workflow, Docker-host operation, or defensive efficacy.


## Completed bounded increment: standalone audit-log collector API retirement

The root-compose-exposed standalone audit-log collector HTTP surface is now an explicit fail-closed compatibility boundary. Its former unauthenticated single and batch ingestion paths accepted client-asserted audit fields and wrote mutable records; its log-list path returned globally scoped records without tenant scope, authorization, source provenance, or immutable-audit enforcement. Each former data path now returns `410 LEGACY_AUDIT_LOG_COLLECTOR_API_RETIRED`, while the compatibility status explicitly reports retirement.

The `audit_log_collector` package's integrity and verification modules remain intact because the separately governed containment lifecycle imports them for its approval-bound, HMAC-audited execution evidence. The retired standalone HTTP process no longer initializes a collector schema or depends on a database; only generic non-mutating operational probes remain.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove audit-event ingestion, authorization, tenant isolation, durable storage, append-only behavior, source provenance, HMAC material provisioning, audit-chain integrity, containment approval or execution, Docker-host operation, recovery, or defensive efficacy.


## Completed bounded increment: standalone compliance API retirement

The root-compose-exposed standalone compliance service is now an explicit fail-closed compatibility boundary. Its former standards and assessments APIs permitted client-driven creation, update, and global retrieval without tenant ownership, authorization, evidence provenance, or a governed remediation lifecycle. The seven former data routes now return `410 LEGACY_COMPLIANCE_API_RETIRED`, and status explicitly identifies the boundary as retired.

This increment does not remove or expose the separately tested shared compliance-engine utility. No tenant-scoped compliance replacement is currently represented as an exposed API, so the retired boundary directs no caller toward an unsupported workflow.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove compliance control assessment, authorization, tenant isolation, evidence collection or provenance, report generation, durable storage, regulatory alignment, remediation, Docker-host operation, or compliance efficacy.


## Completed bounded increment: unscoped attack-graph consumer retirement

The root-compose-exposed attack-graph engine no longer provides an opt-in legacy consumer that read broker events into an unscoped in-memory graph or supported direct path analysis. The consumer, graph builder, path analyzer, and the `PHANTOMNET_LEGACY_ATTACK_GRAPH_ENABLED` setting are removed. The historical direct traversal URL remains only as a `410 LEGACY_UNSCOPED_ATTACK_GRAPH_RETIRED` compatibility boundary.

The preserved governed router continues to require authenticated tenant identity and capabilities for evidence refresh and bounded, read-only attack-path analysis. This change does not alter the governed projection's tenant checks, evidence contracts, read-only semantics, or the separate human-approved containment lifecycle.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove broker access controls, graph-backend connectivity, Neo4j persistence, source-event delivery, evidence completeness, tenant isolation under a live multi-service deployment, analyst authorization in production, Docker-host operation, or attack-path analysis efficacy.


## Completed bounded increment: standalone RabbitMQ log collector retirement

The unmounted standalone `backend_api/collector` application and its Docker build surface have been removed after tracked-source tracing found no Compose service, workflow, import, or caller reference. It accepted arbitrary raw JSON, wrote unscoped `AttackLog` rows, and published directly to a RabbitMQ `attack_logs` queue without tenant identity, source authentication, canonical schema validation, evidence provenance, durable delivery semantics, or governed authorization.

The supported telemetry boundaries remain separate: authenticated canonical telemetry ingestion and capability-protected tenant-scoped endpoint/Wazuh evidence intake. This retirement does not alter those services, the shared database model, historical database rows, or unrelated inactive RabbitMQ analyzer modules.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove telemetry ingestion, agent identity, tenant isolation, schema fidelity, broker connectivity, data durability, historical-row handling, analyzer behavior, Docker-host operation, or detection efficacy.


## Completed bounded increment: fixture-backed legacy analyzer retirement

The unmounted analyzer package no longer contains its raw RabbitMQ `attack_logs` consumer, fixture-trained random-forest and isolation-forest helpers, simulated neural helper, dependency manifest, or standalone Docker build surface. These components accepted and mutated unscoped raw log data, made unproven AI and external-enrichment decisions, sent direct gateway alerts, and included a mock blacklist path without tenant scope, canonical evidence linkage, policy gates, approval, signed audit, verification, or rollback.

The retained analyzer `app.py` remains an explicit `410 LEGACY_ANALYZER_API_RETIRED` compatibility boundary. This retirement does not modify the separately governed tenant-scoped telemetry, detection, correlation, advisory, or analyst-investigation workflows.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove model training, external enrichment authorization, telemetry ingestion, alert correlation, analyst authorization, tenant isolation, broker or gateway connectivity, containment, Docker-host operation, or detection efficacy.


## Completed bounded increment: standalone blockchain service retirement

The unmounted standalone blockchain application, raw RabbitMQ consumer, Solidity contract artifact, and Docker build surface are removed. The retired process initialized a local database, consumed unscoped raw queues, constructed a local hash-chain representation, and reported an “immutable ledger” as operational without tenant identity, source authentication, canonical evidence linkage, durable distributed consensus, authorization, or governed containment controls. The gateway's unused direct blockchain import is also removed.

The source-controlled containment path continues to use its separate tenant-scoped HMAC-signed audit-chain integrity and verification primitives. The local `blockchain.py` library is deliberately unchanged in this increment because it has direct legacy test dependencies; it is not an exposed or deployed service and is not evidence of a distributed or immutable ledger.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove a distributed ledger, consensus, immutability, cryptographic notarization, audit durability, broker connectivity, source-event ingestion, authorization, tenant isolation, containment execution, Docker-host operation, or compliance efficacy.


## Completed bounded increment: unmounted external IP-information retirement

The duplicate unmounted IP-information route and standalone IP-info service are removed after source tracing found no active router inclusion, deployment, or caller. They accepted arbitrary path-supplied IP addresses, called an external geolocation provider directly, and exposed provider responses and error text outside the project’s bounded advisory contract. Their role checks did not establish a tenant-scoped evidence, provenance, or retained advisory record boundary.

The separately supported threat-intelligence service remains the bounded alternative: it requires `alerts:read`, limits public indicator types and bulk input, and provides sanitized provider availability summaries rather than relaying raw provider data. This change does not assert live provider authorization, source attribution, enrichment accuracy, or detection efficacy.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove external provider authorization, indicator enrichment, source provenance, analyst authorization in production, tenant isolation under live load, provider privacy handling, Docker-host operation, or detection efficacy.


## Completed bounded increment: ungoverned dashboard aggregation retirement

The source-reachable unified-stack dashboard service no longer mounts unauthenticated incident aggregation or an executive-summary endpoint with fabricated remediation, risk, escalation, and attack-vector metrics. The removed router made direct downstream calls using legacy localhost assumptions, returned raw alert details without tenant or capability scope, and framed low-impact cases as `AUTO_EXECUTE` without the governed approval, signed audit, verification, or rollback lifecycle.

The mounted dashboard service now provides only an explicit `410 LEGACY_DASHBOARD_API_RETIRED` compatibility boundary. This change does not alter the separately governed tenant-scoped analyst, threat-hunting, attack-path, case, telemetry, evidence, or containment workflows.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove dashboard availability, analyst authorization in production, tenant isolation under live load, downstream service connectivity, telemetry completeness, incident correlation, metric accuracy, containment execution, Docker-host operation, or defensive efficacy.


## Completed bounded increment: unmounted local-agent configuration disclosure retirement

The duplicate unmounted configuration route and standalone config service are removed after tracked-source tracing found no active router inclusion, unified-stack mount, deployment reference, or caller. They read and returned a local `phantomnet_agent/config.json` file in full, creating a reconnaissance and configuration-disclosure surface without tenant ownership, field filtering, evidence linkage, or a governed configuration lifecycle.

The separately supported endpoint/Wazuh configuration workflows remain capability-protected with `config:write` and tenant identity checks. This retirement does not claim agent configuration management, local-file protection, tenant isolation under live load, configuration deployment, or runtime enforcement.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove configuration authorization in production, local-file protection, configuration deployment, agent behavior, tenant isolation under live load, audit durability, Docker-host operation, or defensive efficacy.


## Completed bounded increment: fixture-backed Kafka enrichment retirement

The unmounted enrichment service and its Docker build surface are removed after tracked-source tracing found no active mount, deployment, import, caller, or regression dependency. It consumed normalized events and emitted deterministic mock “threat intelligence” labels, scores, feed names, actor attribution, and simulation claims from hard-coded indicators and keywords, without tenant scope, evidence provenance, provider authorization, evaluation, or policy controls.

The separately supported threat-intelligence service remains the bounded advisory replacement: it requires `alerts:read`, limits indicator types and bulk input, and sanitizes provider availability output. This retirement does not modify the active behavioral consumer’s separate topic contract or establish enrichment accuracy, source delivery, or production provider behavior.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove external provider authorization, enrichment accuracy, source-event delivery, broker connectivity, tenant isolation under live load, advisory quality, analyst authorization in production, Docker-host operation, or detection efficacy.


## Completed bounded increment: simulated SOC copilot context-builder retirement

The unmounted SOC copilot context builder is removed after tracked-source tracing found no caller, service mount, deployment reference, or governed advisory dependency. It simulated cross-service event, vulnerability, asset, and context retrieval through legacy direct CRUD assumptions, had no tenant scope or provenance controls, and lacked evidence-bound policy gates, authorization, or supported advisory contract.

The separately retained SOC copilot router remains an explicit `410 LEGACY_SOC_COPILOT_API_RETIRED` compatibility boundary. This retirement does not alter the governed tenant-scoped threat-intelligence, endpoint-inventory, case, attack-path, or evidence workflows.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove SOC copilot functionality, context retrieval, cross-service connectivity, data provenance, analyst authorization, tenant isolation under live load, advisory quality, Docker-host operation, or defensive efficacy.


## Completed bounded increment: mock vulnerability-management router retirement

The unmounted vulnerability-management router is removed after source tracing confirmed that the root-compose service starts the separately fail-closed `main.py` entry point and no tracked import mounted the router. The deleted router returned fixture assets and simulated vulnerability scans, CVE resolution, prioritization, and patch recommendations without tenant scope, authorized asset ownership, validated finding provenance, evidence controls, change management, or approval-bound remediation.

The service’s explicit `410 LEGACY_VULNERABILITY_API_RETIRED` compatibility boundary remains, as do the separately tested internal patch-prioritization utilities. This retirement does not turn those utilities into a supported assessment, scanner, inventory, CVE, or remediation workflow.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove asset discovery, scanner operation, CVE resolution, finding provenance, patch availability, recommendation quality, analyst authorization, tenant isolation under live load, remediation execution, Docker-host operation, or defensive efficacy.


## Completed bounded increment: public user-portal truthfulness boundary

The source-reachable static `/user` portal page no longer displays fabricated endpoint posture, telemetry, honeypot state, security tokens, vulnerability data, cryptographic audit results, or response controls. The retired page made direct requests to legacy or fail-closed service paths, generated local fallback values and pseudo tokens, cycled random security events, and represented simulated results as operational user security controls.

The route now states plainly that it is non-operational and directs users to authenticated, tenant-scoped governed service boundaries. This change does not alter any governed analyst workflow or claim that the public portal provides operational SOC functionality.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove public portal availability, endpoint posture, telemetry ingestion, honeypot operation, cryptographic audit status, authentication, tenant isolation, containment execution, Docker-host operation, or defensive efficacy.


## Completed bounded increment: alert-storage tenant fallback removal

The active alert-storage broker consumer no longer assigns broker records without a tenant identifier to a shared default tenant. A new explicit tenant parser rejects non-object records and missing, blank, or malformed tenant UUIDs before any insert is attempted. This preserves the service’s existing tenant-filtered read API and the canonical detection workflow’s explicit tenant-bearing alerts without converting malformed cross-tenant inputs into stored data.

Invalid broker records remain visible through the existing error-and-rollback path; the change does not silently coerce them into a shared tenant or claim broker enforcement, durable delivery, source authentication, or production tenant isolation.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove broker access controls, source-event delivery, alert persistence, database availability, source authentication, tenant isolation under live load, operational alerting, Docker-host operation, or detection efficacy.


## Completed bounded increment: autonomous blue-team direct-action worker retirement

The legacy autonomous blue-team Kafka worker, direct defense helpers, container build surface, and root-Compose service are removed. The worker consumed raw alert payloads, mapped alert names to direct block, isolate, process-kill, account-lock, and rollback calls, posted directly to local gateway paths, and wrote file-based action reports. It had no tenant validation, human approval, HMAC-signed audit, controlled adapter gate, verification, or governed rollback contract.

The retained autonomous blue-team HTTP boundary remains an explicit `410 LEGACY_AUTONOMOUS_BLUE_TEAM_API_RETIRED` response. This does not alter the separately governed containment lifecycle, which remains request → human approval → signed audit → controlled adapter → verification → rollback.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove containment execution, adapter availability, firewall or endpoint operation, alert delivery, approval authorization, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy auto-response deployment retirement

The legacy auto-response package retains only its explicit `410 LEGACY_AUTO_RESPONSE_API_RETIRED` compatibility boundary. Its obsolete Python 3.9 container build surface and root development-Compose service are removed, so the retired ASGI boundary is no longer deployed from the broad legacy topology. Source tracing found no tracked caller of the package beyond that Compose exposure, and the hardened self-hosted reference topology contains no legacy auto-response service.

The retained boundary does not execute playbooks, issue agent commands, or invoke security controls. High-impact response remains limited to the separate governed containment lifecycle: request → human approval → HMAC-signed audit → controlled adapter execution → verification → rollback. Regression coverage preserves both the `410` route contract and the absence of the legacy Dockerfile and root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove containment execution, adapter availability, approval authorization, audit durability, verification, rollback, Docker-host operation, migration of legacy callers, or defensive efficacy.


## Completed bounded increment: raw SOAR direct-action worker retirement

The unmounted raw SOAR worker, its alert-name-to-playbook helper, direct Kafka agent-command publisher, obsolete standalone container, and direct-action test are removed. The worker consumed raw broker alerts and turned a port-scan rule into an unsigned `block_network_address` command without tenant validation, request creation, human approval, HMAC-signed audit evidence, controlled adapter selection, verification, or rollback. Source tracing found no tracked deployment or caller for the worker beyond a stale manual startup instruction.

The retained `backend_api/soar_engine/app.py` control plane remains separate: it mounts the tenant-scoped governed containment router, requires its durable database store, and rejects legacy API routes with `410 LEGACY_SOAR_API_RETIRED`. The deployment guide and architecture description now name the governed ASGI control plane rather than the deleted worker. Regression coverage preserves both the worker/container absence and the approval-bound governed containment route.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove broker authorization, alert delivery, containment execution, endpoint or firewall operation, approval authorization, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy SOAR consumer retirement

The unmounted legacy SOAR consumer and its direct-action tests are removed. The consumer contained duplicate response helpers, accepted raw Kafka alerts, evaluated playbook conditions, dispatched localhost agent commands and external response calls, and marked playbook runs completed. Its source-only tests validated dry-run blocking, synthetic ticket generation, and critical-alert execution rather than the supported containment lifecycle. Source tracing found no mounted startup hook, deployment reference, or caller outside those tests.

The retained SOAR ASGI service remains limited to the tenant-scoped governed containment router and durable store initialization. Its high-impact control path continues to require a request, human approval, HMAC-signed audit, controlled adapter execution, verification, and rollback; legacy `/api/soar` routes continue to fail closed. Regression coverage now requires the raw consumer to remain absent and preserves the governed route and boundary assertions.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove broker authorization, alert delivery, playbook migration, ITSM integration, endpoint or firewall operation, containment execution, approval authorization, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: SOAR autonomous-execution module retirement

The unmounted `AutoResponseEngine` and `SOARPlaybookEngine` modules are removed. Together, they selected and simulated playbooks, permitted confidence-and-impact-threshold-based autonomous execution, issued direct localhost agent-isolation requests, created simulated external-response results, performed state capture or temporal reset calls, and wrote conceptual queue records. They did not bind actions to tenant-owned evidence, a containment request, human approval, HMAC-signed audit evidence, controlled adapter execution, verification, or governed rollback. Source tracing found no mounted route, startup hook, deployment, or tracked caller for either module.

The mounted SOAR service remains the separate tenant-scoped governed containment API. It continues to initialize its durable store, exposes the approval-bound request lifecycle, and returns `410 LEGACY_SOAR_API_RETIRED` for legacy route families. Regression coverage now requires the legacy raw worker, consumer, autonomous executor, auto-response helper, and obsolete container to remain absent.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove broker authorization, alert delivery, AI-policy quality, asset-context accuracy, containment execution, adapter availability, approval authorization, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: orphaned SOAR autonomy scaffolding retirement

The unmounted `AISoarBrain`, `PlaybookStrategyEngine`, `SimulationBlastRadiusAnalyzer`, and `HumanInTheLoop` modules are removed. They exposed heuristic confidence scoring, hard-coded critical-asset exceptions, simulated playbook selection and impact analysis, direct asset-service calls, and conceptual in-memory approval/resume behavior. None had a mounted route, startup hook, deployment reference, or tracked caller after retirement of the legacy SOAR execution modules. They did not implement tenant-owned evidence, authenticated approval identity, HMAC-signed audit evidence, controlled adapter execution, verification, or governed rollback.

The separately retained SOAR control plane remains the tenant-scoped governed containment API and durable-store startup path. It does not consume this legacy scaffolding and continues to reject legacy route families. Regression coverage prevents restoration of the complete raw-worker, consumer, autonomous-execution, simulation, heuristic, and conceptual-human-loop module set.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove AI-policy quality, asset inventory availability or accuracy, impact analysis, analyst approval authorization, alert delivery, containment execution, adapter availability, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: simulated AI playbook-generator retirement

The unreferenced internal `AIPlaybookGenerator` is removed. It converted incident fields into hard-coded playbook steps for indicator enrichment, firewall blocking, ticket creation, user notification, and password reset, described the result as AI-generated, and included a local demonstration runner. It had no mounted API, startup hook, deployment reference, tracked caller, tenant-owned evidence requirement, approval identity, HMAC-signed audit evidence, controlled adapter gate, verification, or governed rollback.

The separate legacy playbook-flow-builder service remains an explicit fail-closed boundary, while the retained SOAR control plane remains the tenant-scoped governed containment API. Regression coverage requires the generator and the prior raw worker, consumer, autonomous execution, simulation, and conceptual-human-loop modules to remain absent.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove AI generation quality, enrichment authorization or accuracy, ticketing integration, identity or password-management operation, firewall or endpoint operation, containment execution, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: orphaned SOAR playbook-model retirement

The now-unreferenced legacy SOAR playbook-model module is removed after source tracing found no tracked caller, deployment, startup hook, or test dependency remaining after retirement of the legacy worker, consumer, autonomous-execution, simulation, human-loop, and AI-generator modules. Its schemas still defined automated remediation actions including firewall blocks, host isolation, process kill, password reset, custom scripts, agent-command dispatch, and temporal rollback or snapshot behavior outside the retained governed containment contracts.

The mounted SOAR service remains limited to the tenant-scoped governed containment API and durable-store startup path. Its high-impact lifecycle does not import these legacy playbook models and continues to require request creation, human approval, HMAC-signed audit evidence, controlled adapter execution, verification, and rollback. Regression coverage prevents restoration of the model module together with its retired execution paths.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove containment execution, adapter availability, command delivery, identity or password-management operation, firewall or endpoint operation, approval authorization, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy AI behavioral worker deployment retirement

The legacy AI behavioral raw Kafka consumer, obsolete Python 3.9 container build, root development-Compose service, and stale manual-start instruction are removed. The consumer constructed behavioral events from raw broker payloads and invoked legacy direct-analysis code without an authenticated tenant context, source provenance contract, accepted model evaluation, advisory-only policy boundary, or governed response lifecycle. Source tracing found no tracked consumer import or startup hook outside the consumer itself; the hardened self-hosted reference topology did not include the service.

The retained `app.py` and `main.py` boundaries continue to return `410 LEGACY_AI_BEHAVIORAL_API_RETIRED`. The separate defensive-evaluation implementation remains the supported tenant-scoped, evidence-bound, advisory-only evaluation path and is not altered. Regression coverage preserves both fail-closed ASGI boundaries and requires the raw consumer, container build, and root-Compose service to remain absent. The event-schema and tenant-isolation documentation no longer identify the retired service as a producer or consumer.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove broker authorization, source-event delivery, behavioral analysis, forecasting, model quality, telemetry provenance, tenant isolation under live load, alert production, Docker-host operation, detection efficacy, or defensive efficacy.


## Completed bounded increment: legacy event-stream raw-worker retirement

The unmounted legacy event-stream raw Kafka consumer, direct PostgreSQL helper, and obsolete Python 3.9 container build are removed. The worker accepted raw telemetry without a tenant requirement, created an unscoped `events` table, stored raw event payloads, and emitted low-severity alerts from a string match without source provenance, canonical event validation, tenant isolation, authenticated analyst context, deterministic governed detection content, or alert-workflow controls. Source tracing found no tracked caller or deployment for the package; the separately retained ASGI boundary remains explicit `410 LEGACY_EVENT_STREAM_PROCESSOR_API_RETIRED`.

The supported `backend_api.shared.event_stream_processor` used by gateway and shared-service paths is separate and unchanged. Regression coverage requires the retired consumer, database helper, and container to remain absent while preserving the zero-dependency fail-closed compatibility route.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove telemetry delivery, broker authorization, source authentication, database availability, canonical normalization, alert generation, tenant isolation under live load, Docker-host operation, detection efficacy, or defensive efficacy.


## Completed bounded increment: legacy SOAR playbook implementation retirement

The unmounted legacy SOAR playbook CRUD, database session helper, playbook model, obsolete Python 3.9 container build, and root development-Compose service are removed. They maintained playbooks, runs, and approvals in a separate schema and deployment path outside tenant-owned evidence, authenticated approver identity, HMAC-signed audit evidence, controlled adapter execution, verification, and governed rollback. The root service exposed only the retained `410 LEGACY_SOAR_PLAYBOOK_API_RETIRED` boundary; source tracing found no tracked caller of the deleted implementation modules.

The retained SOAR control plane remains the separately mounted tenant-scoped governed containment API. Regression coverage preserves the fail-closed legacy routes and prevents restoration of the legacy implementation and deployment surfaces.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove playbook migration, approval authorization, containment execution, adapter availability, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy playbook-flow conversion retirement

The unmounted legacy playbook-flow converter, schema, obsolete Python 3.9 container build, and root development-Compose service are removed. The converter transformed user-supplied flow nodes into linear action, approval, and condition steps, selected an arbitrary path through branching, and represented approval as a generic action without tenant-owned evidence, authenticated approver identity, HMAC-signed audit evidence, controlled adapter execution, verification, or governed rollback. The retained API remains explicit `410 LEGACY_PLAYBOOK_FLOW_BUILDER_API_RETIRED`; source tracing found no tracked caller of the deleted implementation.

The separately mounted SOAR control plane remains the tenant-scoped governed containment API. Regression coverage preserves the fail-closed compatibility route and prevents restoration of the converter, schema, container, or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove playbook migration, approval authorization, containment execution, adapter availability, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: unmounted raw-log route retirement

The unmounted raw-log route is removed. It queried shared attack-log rows and legacy raw SIEM records, returned raw log payloads, and performed no tenant filter or tenant-owned evidence authorization. Although it declared a role dependency, source tracing found no router mount or tracked caller. The mounted log-service API remains a separate explicit `410 LEGACY_LOG_RETRIEVAL_API_RETIRED` boundary directing callers to governed tenant-scoped analyst-evidence workflows.

Regression coverage prevents restoration of the unmounted route while preserving the mounted fail-closed compatibility contract.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove analyst-evidence availability, tenant isolation under live load, source authentication, raw-log retention, authorization correctness, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy DFIR utility retirement

The unmounted legacy DFIR host-analysis utility and obsolete container build are removed. The utility accepted local server paths, invoked a host-installed Volatility command, parsed PCAP files, scanned memory bytes, and reconstructed timelines without tenant-owned evidence intake, file provenance, analyst authorization, sandboxing, bounded resource controls, or an immutable evidence contract. Source tracing found no tracked caller or deployment; the retained API remains explicit `410 LEGACY_DFIR_API_RETIRED`.

The separate shared DFIR implementation remains the supported evidence-analysis boundary and is unchanged. Regression coverage prevents restoration of the legacy utility and container while preserving the zero-dependency fail-closed compatibility route.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove forensic intake, file provenance, analyst authorization, tool availability, sandboxing, analysis accuracy, evidence durability, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy asset-inventory implementation retirement

The unmounted legacy asset-inventory scanner, database helper, CVE mapper, and obsolete container build are removed. The implementation exposed arbitrary scan targets, maintained a separate inventory store, and mapped CVEs without a tenant-owned asset contract, authorized-discovery control, source provenance, authenticated analyst context, rate or scope limits, or governed evidence lifecycle. Source tracing found no tracked caller or deployment; the retained API remains explicit `410 LEGACY_ASSET_INVENTORY_API_RETIRED`.

Separate governed tenant-scoped inventory and authorized-discovery workflows remain the supported path and are unchanged. Regression coverage prevents restoration of the legacy scanner, storage, mapper, and container while preserving the zero-dependency fail-closed compatibility route.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove asset discovery, scan authorization, inventory accuracy, CVE coverage, tenant isolation under live load, evidence durability, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy compliance implementation retirement

The unmounted legacy compliance CRUD, database helper, model, obsolete Python 3.9 container build, and root development-Compose service are removed. They maintained mutable standards and assessments outside tenant scope, authorization, evidence provenance, immutable evidence, or governed remediation controls. Source tracing found no tracked caller of the deleted implementation; the retained API remains explicit `410 LEGACY_COMPLIANCE_API_RETIRED`.

The separate shared compliance analysis engine remains unchanged. Regression coverage prevents restoration of the legacy persistence and deployment surfaces while preserving the zero-dependency fail-closed compatibility route.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove compliance assessment accuracy, evidence provenance, tenant isolation under live load, authorization correctness, remediation execution, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy audit-log collector deployment retirement

The obsolete Python 3.9 container build and root development-Compose service for the fail-closed legacy audit-log collector are removed. That service exposed only the retained `410 LEGACY_AUDIT_LOG_COLLECTOR_API_RETIRED` boundary, while its deployment topology unnecessarily carried PostgreSQL credentials and a network port for an intentionally unavailable API. The package’s integrity and verification modules are retained because governed containment imports them for HMAC-bound audit chain append and verification.

Regression coverage prevents restoration of the legacy container and root-Compose service while preserving the explicit fail-closed API contract and the required governed audit imports.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove audit persistence, cryptographic-key handling, chain durability, adapter execution, verification, rollback, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy log-normalizer deployment retirement

The unreferenced legacy normalizer event schema, obsolete Python 3.9 container build, and root development-Compose service are removed. The exposed service had already been reduced to the fail-closed `410 LEGACY_LOG_NORMALIZER_API_RETIRED` boundary, but its deployment continued to publish a port for an intentionally unavailable unauthenticated normalization API. The separate canonical tenant-aware event-normalization pipeline remains unchanged.

Regression coverage preserves the fail-closed compatibility routes and prevents restoration of the legacy schema, container, or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove normalization accuracy, source authentication, tenant isolation under live load, event delivery, canonical-schema conformance for external traffic, Docker-host operation, or defensive efficacy.


## Completed bounded increment: legacy PhantomQL deployment retirement

The obsolete Python 3.9 container build and root development-Compose service for the fail-closed legacy PhantomQL API are removed. The retired direct-query service previously carried database credentials and a network port despite returning `410 LEGACY_PHANTOMQL_API_RETIRED` for its legacy query and aggregate routes. The separate governed threat-hunting analysis boundary remains unchanged.

Regression coverage preserves the fail-closed compatibility routes and prevents restoration of the PhantomQL container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove query execution, event delivery, analyst identity, authorization enforcement, tenant isolation, evidence provenance, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: legacy lateral-movement deployment retirement

The obsolete Python 3.9 container build and root development-Compose service for the fail-closed legacy lateral-movement detector are removed. The service exposed only `410 LEGACY_LATERAL_MOVEMENT_API_RETIRED` for arbitrary untenant-scoped event-batch analysis, yet its legacy deployment continued to publish a network port. Governed tenant-scoped detection, correlation, and analyst investigation workflows remain unchanged.

Regression coverage preserves the fail-closed compatibility route and prevents restoration of the lateral-movement container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove event delivery, lateral-movement detection, analyst authorization, tenant isolation under live load, correlation accuracy, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: legacy forensics-engine deployment retirement

The obsolete Python 3.9 container build and root development-Compose service for the fail-closed legacy forensics engine are removed. The retired service carried database credentials and a network port despite returning `410 LEGACY_FORENSICS_API_RETIRED` for its historical timeline interface. The separate governed tenant-scoped evidence-intake path remains unchanged.

Regression coverage preserves the explicit fail-closed legacy route and prevents restoration of the forensics container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove forensic timeline construction, asset identity, authorization, tenant isolation, evidence provenance, source collection, chain of custody, integrity verification, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: legacy vulnerability-management deployment retirement

The obsolete Python 3.9 container build and root development-Compose service for the fail-closed legacy vulnerability-management API are removed. The retired service published a network port and carried database credentials although its historical routes return `410 LEGACY_VULNERABILITY_API_RETIRED`. Separately tested vulnerability data contracts and non-executing recommendation utilities remain source-controlled; governed tenant-scoped asset and remediation integrations remain unchanged.

Regression coverage preserves the explicit fail-closed legacy route and prevents restoration of the vulnerability-management container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove vulnerability discovery, CVE accuracy, asset identity, authorization, tenant isolation, remediation accuracy, source collection, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: legacy AI-agent orchestrator deployment retirement

The obsolete container build and root development-Compose service for the fail-closed legacy AI-agent orchestrator are removed. The retired service published a network port and depended on legacy playbook and graph services although its historical task route returns `410 LEGACY_AI_AGENT_ORCHESTRATOR_API_RETIRED`. Governed evidence-grounded advisory decisions, analyst investigation, and approval-bound containment workflows remain unchanged.

Regression coverage preserves the explicit fail-closed legacy route and prevents restoration of the AI-agent orchestrator container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove agent planning, model operation, analyst authorization, tenant isolation, evidence provenance, playbook execution, graph analysis, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: legacy BAS deployment retirement

The obsolete container build and root development-Compose service for the fail-closed legacy BAS API are removed. The retired service published a network port although its historical simulation and local-result routes return `410 LEGACY_BAS_API_RETIRED`. Separately tested controlled baseline scenarios continue to emit safe canonical event fixtures for detection-validation paths; no external target or response execution path is changed.

Regression coverage preserves the explicit fail-closed legacy routes and prevents restoration of the BAS container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove attack simulation, scanning, exploitation, external-target authorization, event delivery, detection accuracy, tenant isolation under live load, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: legacy SIEM-ingest deployment retirement

The obsolete Python 3.9 container build and root development-Compose service for the fail-closed legacy SIEM-ingest API are removed. The retired service published a network port and carried database credentials although its unauthenticated raw-ingest and raw-log routes return `410 LEGACY_SIEM_INGEST_API_RETIRED`. Canonical telemetry ingestion and governed tenant-scoped endpoint integration paths remain unchanged.

Regression coverage preserves the explicit fail-closed legacy routes and prevents restoration of the SIEM-ingest container or root-Compose service.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove source authentication, telemetry delivery, raw-evidence durability, tenant isolation under live load, Wazuh integration, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: shared PNQL scanner-registry retirement

The shared service registry no longer constructs an unreachable PNQL data-source registry that exposed globally scoped raw-log access and loaded scanner plugins against caller-supplied targets. The active canonical telemetry-ingest accessor remains available to the authenticated telemetry route. The standalone legacy PhantomQL compatibility boundary and governed threat-hunting analysis path remain unchanged.

Regression coverage preserves the telemetry accessor dependency while preventing restoration of PNQL raw-data helpers, scanner-plugin execution wiring, or the shared PNQL registry.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove telemetry source authentication, raw-evidence durability, tenant isolation under live load, threat-hunting behavior, scanner operation, target authorization, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: shared randomized OSINT simulation retirement

The unreachable shared OSINT module that generated randomized, fabricated Shodan, Censys, Spyse, Chaos, GitHub-secret, and Google-dork results is removed, together with its unused gateway and shared-registry imports. The separately governed threat-intelligence service and the canonical telemetry accessor remain source-controlled and unchanged.

Regression coverage prevents restoration of the randomized simulation or unused imports while retaining the distinct governed threat-intelligence and telemetry boundaries.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove external enrichment, source authentication, target authorization, target discovery, threat-intelligence accuracy, telemetry delivery, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: deterministic event-stream advisory fallback

The shared event-stream processor no longer fabricates randomized anomaly scores, classifications, or investigation recommendations when an advisory plugin is unavailable. It now records no advisory anomaly result in that condition while retaining deterministic rule correlation, threat-intelligence matching, and UEBA handling. This change does not add response authority or alter governed containment.

Regression coverage prevents restoration of the runtime randomized fallback while preserving the deterministic analysis boundaries.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove event delivery, source authentication, rule accuracy, threat-intelligence accuracy, UEBA calibration, tenant isolation under live load, plugin behavior, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: shared BlueTeamAI simulation retirement

The unreachable shared BlueTeamAI module that fabricated anomaly outcomes and printed simulated defense actions is removed, together with unused gateway and shared-registry imports and startup wiring. Advisory-only AI boundaries and the separately governed request, human approval, signed audit, controlled adapter, verification, and rollback containment lifecycle remain unchanged.

Regression coverage prevents restoration of the simulated BlueTeamAI module or background startup wiring while retaining the distinct governed containment boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove AI analysis, event delivery, source authentication, authorization, tenant isolation, containment execution, verification, rollback behavior, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: shared PNQL simulation-engine retirement

The unreachable shared PNQL engine and its direct unit tests are removed, together with an unused gateway import. The removed engine contained simulated plugin-query output and did not own the supported analyst workflow. The separate fail-closed PhantomQL compatibility boundary and governed tenant-scoped threat-hunting service remain unchanged.

Regression coverage prevents restoration of the shared PNQL implementation or its obsolete tests while retaining the distinct retirement and governed hunting boundaries.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove query execution, tenant isolation, authorization, evidence provenance, threat-hunting behavior, event delivery, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: shared simulated command-dispatcher retirement

The unreachable shared command dispatcher that fabricated successful agent-command responses is removed. The separate fail-closed direct command-dispatcher boundary remains, while canonical signed agent commands and the governed request, approval, signed audit, controlled adapter, verification, and rollback lifecycle remain unchanged.

Regression coverage prevents restoration of the simulated shared dispatcher while retaining the separate fail-closed and governed containment boundaries.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove command delivery, signing-material provisioning, authorization, tenant isolation, adapter execution, verification, rollback behavior, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: fabricated BAS simulation retirement

The unmounted BAS simulator that fabricated attack outcomes and persisted local simulation-result files is removed with its unused gateway and shared-registry imports. Controlled baseline scenarios continue to emit safe canonical event fixtures for detection validation; no external target or response execution path is added.

Regression coverage prevents restoration of the fabricated BAS simulator modules while preserving the separate baseline-fixture pipeline.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove attack simulation, scanning, exploitation, external-target authorization, event delivery, detection accuracy, tenant isolation under live load, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: CVE resolver prototype retirement

The unmounted CVE resolver prototypes are removed: one fabricated CVE response API and one direct NVD query helper. The retained vulnerability-management API continues to fail closed, directing callers to governed tenant-scoped asset and remediation integrations.

Regression coverage prevents restoration of the resolver prototypes while retaining the explicit `410` vulnerability-management boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove vulnerability enrichment, CVE accuracy, external-source authentication, asset identity, authorization, tenant isolation, remediation accuracy, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: fail-closed plugin sandbox unavailability

The shared plugin sandbox no longer fabricates mock container or plugin results when the Docker SDK or daemon is unavailable. It now returns an explicit `PLUGIN_SANDBOX_UNAVAILABLE` error stating that no plugin result was produced. Plugin execution remains an advisory boundary and no response authority is added.

Regression coverage prevents restoration of fabricated mock plugin output while retaining the plugin-manager sandbox boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove Docker isolation, plugin safety, plugin execution, source authentication, AI analysis, tenant isolation, response authorization, containment behavior, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: randomized shared MITRE simulation retirement

The unreachable shared MITRE module that assigned randomized confidence values, generic random technique fallbacks, and simulated coverage explanations is removed. Governed tenant-scoped MITRE evidence remains separately implemented in correlation, investigation, and threat-hunting paths.

Regression coverage prevents restoration of the randomized shared MITRE simulation while retaining separate governed MITRE evidence implementations.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove ATT&CK mapping accuracy, coverage completeness, evidence provenance, tenant isolation under live load, investigation behavior, threat-hunting behavior, Docker-host operation, or defensive efficacy.


## Completed bounded increment: deterministic zero-trust evidence handling

The active shared zero-trust engine no longer generates randomized trust or device-posture values. It derives a score only from bounded supplied numeric evidence and uses a deterministic zero score when required evidence is unavailable; device posture is preserved from request context or set to `unknown`. Active RBAC, approval-bound governed containment, signed audit, verification, and rollback controls remain separate and unchanged.

Regression coverage prevents restoration of randomized trust and posture fallbacks while preserving the active zero-trust manager contract and separate governed control boundaries.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove identity assurance, device posture, access enforcement, policy accuracy, authorization, tenant isolation under live load, containment execution, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: side-effect-free gateway readiness monitoring

The active gateway health monitor no longer selects agents randomly, probes a hard-coded local endpoint, writes audit or identity state, gossips to peers, or triggers key rotation. It now delegates only to the structured gateway readiness check and records observational readiness without taking action.

Regression coverage prevents restoration of randomized or mutating monitor behavior while preserving the active gateway monitor import and structured readiness implementation.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove service availability, dependency reachability, control-plane operation, recovery, Docker-host operation, scale, investigation efficacy, or defensive efficacy.


## Completed bounded increment: fabricated SOC copilot implementation retirement

The unreachable SOC copilot implementation that fabricated canned LLM responses and simulated investigation content is removed. The separate SOC copilot API boundary remains explicitly fail closed, and governed evidence-grounded advisory controls remain separate.

Regression coverage prevents restoration of the fabricated copilot implementation while retaining the `410` legacy boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove AI analysis, model-provider availability, evidence provenance, investigation behavior, tenant isolation, advisory usefulness, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: simulated attack-path generator retirement

The unused shared attack-path generator that fabricated random assets, topology, and risk values is removed with its sole gateway import. The active governed tenant-scoped evidence-bound attack-path service and route remain separate.

Regression coverage prevents restoration of the simulated generator while retaining the governed attack-path analysis boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove attack-path completeness, asset accuracy, topology accuracy, risk accuracy, evidence provenance, tenant isolation under live load, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: simulated password-reset email logger retirement

The unreferenced password-reset email helper that logged simulated delivery and reset-link content is removed with its sole gateway import. The separate legacy password-reset API boundary remains explicitly fail closed.

Regression coverage prevents restoration of the simulated email logger while retaining the `410` password-reset boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove password-reset delivery, mailbox ownership, reset-token confidentiality, authentication, account recovery, notification availability, Docker-host operation, or defensive efficacy.


## Completed bounded increment: simulated credential-spraying plugin retirement

The auto-discoverable Kerbrute plugin that simulated credential enumeration and password-spraying outcomes is removed with its discovery manifest. The separate plugin sandbox boundary remains explicitly unavailable without Docker execution and does not fabricate a plugin result.

Regression coverage prevents restoration of the credential-spraying plugin while retaining the separate fail-closed sandbox boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove credential enumeration, password spraying, authorization, scanning, sandbox isolation, plugin safety, target ownership, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: simulated asset-management retirement

The unreferenced shared asset-management module that fabricated fixed network hosts, ports, vulnerabilities, and risk scores is removed together with its companion simulation-only unit test. Source tracing found no product import, caller, service mount, or deployment reference; full regression collection identified the unit test as the sole remaining import dependency. The separately active endpoint-inventory service remains the supported tenant-scoped, evidence-ingestion boundary and stays non-enforcing.

Regression coverage prevents restoration of the simulated module or its simulation-only test while preserving the tenant-bound endpoint-inventory ingestion boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove asset discovery, network scanning, vulnerability identification, risk-score accuracy, tenant isolation under live load, evidence durability, source authentication, endpoint-inventory availability, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: simulated threat-marketplace retirement

The unmounted threat-marketplace package that accepted arbitrary detection-logic payloads, recorded in-memory developer reputation and reward balances, and marked submissions as validated after a fixed delay is removed with its companion demonstration script. Source tracing found no product caller, service mount, deployment reference, or governed publication path. The separate threat-intelligence service remains capability-protected, advisory, and non-enforcing.

Regression coverage prevents restoration of the simulated marketplace package while preserving the separate advisory threat-intelligence boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove detection-module validation, rule safety, threat-intelligence sharing, provider authorization, analyst authorization in production, reputation or reward accounting, tenant isolation under live load, evidence provenance, Docker-host operation, investigation efficacy, or defensive efficacy.


## Completed bounded increment: pseudo-enforcement edge-brain retirement

The unmounted edge-brain package that claimed endpoint syscall and process interception is removed with its non-runnable local demonstration script. It derived a local identifier, returned hard-coded “verified” integrity status, and applied a fixed string drop list without tenant-owned evidence, authenticated approval, signed audit evidence, controlled adapter execution, verification, or rollback. Source tracing found no product caller, service mount, or deployment reference.

The separately supported governed containment lifecycle remains request → human approval → signed audit → controlled adapter → verification → rollback. Regression coverage prevents restoration of the pseudo-enforcement package while preserving that governed boundary.

> **Evidence boundary:** this is Class A source-and-test evidence. It does not prove endpoint telemetry, syscall or process interception, policy enforcement, integrity verification, containment execution, adapter availability, approval authorization, audit durability, verification, rollback, Docker-host operation, or defensive efficacy.
