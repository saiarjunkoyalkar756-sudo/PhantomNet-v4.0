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

## Completed development increment: Phase 7

Phase 7 now provides a **self-hosted deployment and observability reference architecture**. The new Compose topology isolates PostgreSQL, Redis, Redpanda, and Neo4j on an internal network; exposes the gateway and Prometheus only through loopback ports; health-gates the control-plane startup; pins service images; protects stateless services with read-only filesystems and dropped capabilities; and requires every credential to be injected outside source control.

The standard service factory now exposes bounded, Prometheus-compatible process counters. Readiness continues to combine upstream dependency checks with secret-safe runtime posture, while the existing recovery harness remains the minimum Docker-host proof for broker, database, and HMAC audit-chain recovery. The architecture documentation defines backup, restore, upgrade, ingress, and external Docker-host validation requirements without claiming a live deployment from this sandbox.

> **Phase 7 closure rule:** internal topology is not public ingress, liveness is not readiness, static Compose proof is not live-host proof, and a successful start does not replace backup, recovery, audit-chain, or operator acceptance evidence.

## Sequencing principles

The roadmap is intentionally core-first. It prioritizes safety and operability over additional integrations, and it builds every new adapter around the same canonical contracts, RBAC, tenant isolation, audit-chain rules, and test harnesses. Deployment validation cannot be represented as complete until it runs on Docker-capable infrastructure; similarly, real cloud validation remains a separate non-production lab gate rather than a sandbox action.
