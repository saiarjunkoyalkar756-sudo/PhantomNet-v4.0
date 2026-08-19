# PhantomNet Core-First Development Roadmap

## Product direction

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
| 9 | **AI-native analyst assistance** | Explainable, advisory-only correlation suggestions, rule-draft workflows, and analyst review gates with no direct response authority. |
| 10 | **External lab readiness** | Non-production deployment guide, operator runbooks, security review, onboarding checklist, and first external lab or university validation. |

## Completed development increment: Phase 3

Phase 3 now provides **versioned detection and correlation engineering**. Tenant-owned deterministic rules require a strictly increasing dotted numeric version when their definition changes. Every accepted version retains an immutable definition snapshot and SHA-256 fingerprint, so historical rule evidence can be reviewed reproducibly without activating an old definition.

The implementation also provides bounded offline fixtures that evaluate canonical events in deterministic timestamp/event-ID order without broker, database-write, endpoint, cloud, or response-adapter activity. Technique-to-tactic MITRE mappings are complete by contract and can be summarized per tenant. Finally, rules can carry a bounded analyst-alert suppression window that groups repeated alerts without suppressing durable telemetry, match evidence, detections, approvals, or any high-impact action.

> **Phase 3 closure rule:** rule governance, fixture evaluation, MITRE coverage, and alert-suppression controls remain advisory-only. They cannot alter containment scope, bypass human approval, execute a response adapter, or generate automatic enforcement.

## Sequencing principles

The roadmap is intentionally core-first. It prioritizes safety and operability over additional integrations, and it builds every new adapter around the same canonical contracts, RBAC, tenant isolation, audit-chain rules, and test harnesses. Deployment validation cannot be represented as complete until it runs on Docker-capable infrastructure; similarly, real cloud validation remains a separate non-production lab gate rather than a sandbox action.
