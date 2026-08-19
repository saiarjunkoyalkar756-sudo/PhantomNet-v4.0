# PhantomNet v4.0

> **Capable, composable, yours.** A self-hosted, AI-native security operations platform for teams that need defensible detection, governed response, and control over their security data.

PhantomNet v4.0 is a composable SOC platform built for security teams that want a practical alternative to vendor lock-in. It brings together canonical security-event ingestion, correlation and MITRE-aligned evidence, endpoint inventory, case workflows, controlled breach-and-attack simulation (BAS), threat context, graph analysis, and operator-facing dashboards.

The project is designed around a simple operational principle: **automate context and evidence; govern high-impact response.** Detection and correlation can be fast, but containment actions such as blocking, isolating, or terminating require approval and HMAC-signed audit evidence. If required approval or audit evidence is unavailable, containment fails closed.

## Platform at a Glance

| Area | Capability |
|---|---|
| Event pipeline | Versioned canonical event schema, normalization, durable detection records, and broker-ready ingestion boundaries. |
| Detection and triage | BAS scenarios, MITRE-aligned detection evidence, correlation workflows, and analyst-ready alert states. |
| Case operations | Case lifecycle and governed playbook transitions for investigation and response. |
| Endpoint coverage | Asset inventory, endpoint telemetry ingestion, and Wazuh-compatible forwarder registration and streaming boundaries. |
| Response governance | Human approval for high-impact actions, HMAC-signed containment audit records, verification, rollback, and fail-closed behavior. |
| Cloud containment | Governed AWS Security Group containment adapter with LocalStack-oriented integration coverage. |
| Threat context | Attack-path analysis, regional telemetry replication boundaries, tenant isolation, and integrity checks. |
| Operator experience | A React/Vite SOC dashboard and a Next.js portal with dedicated user and administrator views. |
| Resilience | Isolated SQLite regression harnesses plus a Docker-host recovery topology for broker and PostgreSQL restart validation. |

## Security Model

PhantomNet is deliberately conservative where it matters. A simulation, alert, or enrichment result does not independently authorize an impactful response. High-impact containment requests are approved by a human workflow and must generate signed audit evidence before the adapter can execute.

| Control | Expected behavior |
|---|---|
| Human approval | `block`, `isolate`, and `terminate` actions require a recorded approval decision. |
| Audit integrity | Response lifecycle records are HMAC signed and verified as a chain. |
| Fail-closed containment | Missing or invalid approval/audit evidence prevents containment execution. |
| Tenant boundaries | Correlation, response, and audit workflows use tenant-scoped contracts and isolation checks. |
| Test isolation | Automated Python tests use isolated SQLite state; external dependencies are mocked or explicitly gated. |
| Secret handling | Runtime credentials and signing keys are supplied through environment variables, not embedded in source. |

> **Safe use notice:** BAS and response functionality must be run only against systems you own or are explicitly authorized to test. The benchmark harnesses are non-destructive and use simulated adapters; they are not authorization to conduct live attack activity.

## Architecture

PhantomNet uses independently deployable components with clear integration boundaries. The production topology can use PostgreSQL for durable records, Redis for supporting state, Redpanda/Kafka for event transport, and Neo4j for graph-driven context. Unit and regression tests intentionally substitute isolated SQLite state and simulated adapters to make correctness repeatable without contacting external infrastructure.

```text
Endpoint agents / BAS / forwarders
                │
                ▼
      Event normalization + canonical schema
                │
                ▼
       Broker ingestion + correlation engine
                │
       ┌────────┴────────┐
       ▼                 ▼
Detections, alerts,    Asset and graph
cases, audit evidence  context and attack paths
       │
       ▼
Governed response workflow
(approval → signed audit → adapter → verification / rollback)
       │
       ▼
SOC dashboard and operator portal
```

The detailed architecture and event contracts are documented in [Architecture](docs/ARCHITECTURE.md), [Event Bus Schema](docs/EVENT_BUS_SCHEMA.md), and [Runtime Security Posture](docs/runtime-security-posture.md).

## Repository Layout

```text
PhantomNet-v4.0/
├── backend_api/              FastAPI services, correlation, SOAR, IAM, and shared security controls
├── dashboard_frontend/       React + Vite SOC dashboard
├── phantomnet-website/       Next.js public site and operator portals
├── phantomnet_agent/         Endpoint telemetry, local analysis, and response-agent boundary
├── features/                 Optional intelligence, recovery, and trust-fabric modules
├── scripts/                  Benchmarks and isolated recovery-validation runners
├── tests/                    Cross-service regression and validation tests
├── docs/                     Architecture, deployment, operations, and security runbooks
├── docker-compose.yml        Primary Compose topology
└── docker-compose.recovery-validation.yml
                              Internal-only recovery-validation topology
```

## Quick Start: Validate the Codebase

The following workflow is the fastest way to verify the repository locally. It exercises the isolated test suite and compiles both web interfaces without starting a production-like deployment.

### Prerequisites

| Dependency | Validated development baseline | Used for |
|---|---|---|
| Python | Python 3.12 | Backend, agents, tests, and benchmark harnesses |
| Node.js | Node 22 | Dashboard and portal builds |
| npm | Current Node-compatible npm | Frontend dependency installation and quality checks |
| Docker Engine + Compose v2 | Required only for Compose and recovery-host validation | Full service topology and restart validation |

```bash
# Clone and enter the repository.
git clone https://github.com/saiarjunkoyalkar756-sudo/PhantomNet-v4.0.git
cd PhantomNet-v4.0

# Create an isolated Python environment and install repository dependencies.
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run the complete isolated regression suite.
python3 -m pytest -q -p no:cacheprovider
```

The current isolated regression gate contains **317 passing tests** and **6 explicitly skipped environment-gated tests**. The skipped checks require Docker or LocalStack and are not silently treated as successful integration validation.

### Build the Operator Interfaces

The repository does not ship lockfiles, so use `npm install` for a fresh development checkout.

```bash
# React/Vite SOC dashboard
cd dashboard_frontend
npm install
npm run lint
npm run build

# Next.js public site and operator portal
cd ../phantomnet-website
npm install
npm run lint
npm run build
```

The dashboard's production bundle uses an explicit 600 kB vendor-chunk budget. This keeps the intentionally separated React vendor bundle visible while preventing an expected bundle-size message from obscuring real build regressions.

## Local Development and Deployment

Use Docker Compose only with non-production environment values. Secrets, passwords, HMAC keys, and provider credentials must be passed through the environment or an untracked local environment file.

```bash
# Inspect the declared service topology before starting it.
docker compose config

# Start the configured local development topology after supplying required environment values.
docker compose up -d

# Follow service startup and health logs.
docker compose logs -f
```

The exact configuration, environment requirements, operational rollout sequence, and topology-specific considerations are maintained in [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) and [Operations Guide](docs/OPERATIONS.md). Treat a clean `docker compose up` as a local integration step, not a production readiness certification.

## Validation Workflows

PhantomNet separates quick, safe regression evidence from Docker-host integration evidence.

| Workflow | Command | Scope and safety boundary |
|---|---|---|
| Core regression suite | `python3 -m pytest -q -p no:cacheprovider` | Isolated tests using SQLite and mockable boundaries. |
| Canonical SOC benchmark | `python3 scripts/benchmark_canonical_soc.py` | Temporary SQLite database and simulated response adapter; no external calls or endpoint actions. |
| Resilience stress benchmark | `python3 scripts/run_resilience_stress.py --events 500` | Synthetic BAS-marked telemetry; verifies idempotency and detection/alert invariants without response execution. |
| Dashboard quality gate | `cd dashboard_frontend && npm run lint && npm run build` | Static analysis and production bundle validation. |
| Portal quality gate | `cd phantomnet-website && npm run lint && npm run build` | Static analysis, TypeScript validation, and static-route generation. |
| Docker recovery validation | `./scripts/run_docker_recovery_validation.sh` | Docker-capable host only; runs against an internal-only, ephemeral test topology. |
| Wazuh governed-response dry-run | `python3 scripts/run_wazuh_governed_response_dry_run.py` | SQLite-only, local Wazuh/endpoint simulation; validates approval, signed receipt, rollback, and HMAC audit evidence without network or endpoint changes. |
| Containerized Wazuh dry-run | `./scripts/run_docker_wazuh_governed_response_dry_run.sh` | Docker-capable host only; repeats the local simulation in an internal-only, disposable hardened container. |

The benchmark scripts run directly from the repository root and do **not** require callers to set `PYTHONPATH`.

### Docker Recovery Validation

The recovery harness validates broker and PostgreSQL stop/start behavior, checks that dependent probes fail closed during each outage, then records HMAC-verifiable audit evidence after recovery. It uses a timestamped Compose project, an internal-only network, non-production credentials, and disposable volumes.

Before running it, generate fresh test-only values for `RECOVERY_DB_PASSWORD`, `RECOVERY_AUDIT_HMAC_KEY`, and `RECOVERY_AUDIT_HMAC_KEY_ID`. Follow the full procedure in [Docker Recovery Validation](docs/DOCKER_RECOVERY_VALIDATION.md). **Never** point this runner at production infrastructure or provide production secrets.

## Documentation

| Document | Purpose |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Component boundaries and system design. |
| [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Environment preparation and deployment considerations. |
| [Operations Guide](docs/OPERATIONS.md) | Monitoring, logs, recovery, and operator practices. |
| [API Documentation](docs/API_DOCUMENTATION.md) | Service and API reference material. |
| [Event Bus Schema](docs/EVENT_BUS_SCHEMA.md) | Event-routing and schema conventions. |
| [Governed Correlation Engineering](docs/governed-correlation-engineering.md) | Versioned deterministic rules, immutable revisions, offline fixtures, MITRE coverage, and bounded analyst-alert suppression. |
| [Phase 4 Evidence Integration](docs/PHASE_4_EVIDENCE_INTEGRATION.md) | Tenant-scoped asset, endpoint, Wazuh, identity, intelligence, and graph evidence with explicit read-only provenance and canonical correlation projection. |
| [Governed Response and Replication](docs/governed-response-and-regional-replication.md) | Response governance and telemetry replication contracts. |
| [Tenant Isolation and Audit Integrity](docs/tenant-isolation-and-audit-integrity.md) | Isolation checks and tamper-evident audit verification. |
| [AWS Security Group Containment](docs/aws-security-group-containment.md) | Cloud firewall adapter safety and validation boundary. |
| [Docker Topology Validation](docs/DOCKER_TOPOLOGY_VALIDATION.md) | Live internal PostgreSQL, Redis, Redpanda, and Neo4j round-trip proof. |
| [Docker Recovery Validation](docs/DOCKER_RECOVERY_VALIDATION.md) | Isolated broker/database restart test runbook. |
| [Production-Readiness Validation](docs/PRODUCTION_READINESS_VALIDATION.md) | Executed evidence, corrected findings, and remaining live-validation boundaries. |
| [SOC and SIEM Comparison](docs/PHANTOMNET_SOC_SIEM_COMPARISON.md) | Evidence-based positioning against Splunk, Wazuh, Sentinel, Elastic, and Security Onion. |
| [Wazuh Integration and Migration Guide](docs/WAZUH_INTEGRATION_AND_MIGRATION_GUIDE.md) | Phased telemetry-first pairing plan, governed-response boundaries, validation gates, and rollback procedure. |
| [Wazuh Telemetry Pilot Deployment](docs/WAZUH_TELEMETRY_PILOT_DEPLOYMENT.md) | Phase 1 sidecar and manager-integrated manifests, secret handling, verification, and rollback. |
| [Wazuh Governed Response Bridge Design](docs/WAZUH_GOVERNED_RESPONSE_BRIDGE.md) | Phase 2 approval, command-binding, verification-receipt, audit, and rollback model. |
| [Wazuh Governed Response Deployment](docs/WAZUH_GOVERNED_RESPONSE_DEPLOYMENT.md) | Disabled-by-default bridge activation, agent staging, lab acceptance gates, failure injection, and emergency stop procedure. |
| [Wazuh Governed-Response Operational Dry-Run](docs/WAZUH_GOVERNED_RESPONSE_DRY_RUN.md) | Safe isolated and Docker-host proof of approval, signed execution receipts, governed release, and HMAC audit-chain verification. |
| [Core-First Platform Roadmap](docs/core-first-platform-roadmap.md) | Current engineering sequence and remaining platform work. |

## Current Engineering Focus

The core detection-to-governed-response path is implemented and continuously regression-tested. The next operational milestones focus on validating the Compose deployment on a Docker-capable host, expanding production-backed endpoint response through an EDR integration, maturing interaction-capture honeypots, and completing an operator security review before any production deployment.

| Priority | Next milestone | Intended outcome |
|---|---|---|
| 1 | Docker-host deployment and recovery validation | Demonstrate restart behavior with real ephemeral Redpanda and PostgreSQL containers. |
| 2 | EDR integration boundary | Replace stub-only host isolation paths with validated EDR or osquery/Wazuh capability. |
| 3 | Honeypot interaction capture | Add production-oriented SSH and HTTP interaction evidence collection. |
| 4 | Operator documentation and security review | Prepare a defensible deployment and incident-operations package. |

## Contributing

Contributions should preserve PhantomNet's security invariants. Do not add code that bypasses approval gates, omits audit records, hardcodes secrets, or silently converts an adapter failure into a successful containment result. Every change should include focused tests and must pass the Python, dashboard, and portal quality gates described above.

For security-sensitive changes, prioritize the following order:

1. Security correctness and auditability.
2. Automated tests and isolation.
3. Functional correctness and clear failure handling.
4. Performance and cleanup.

## Project Positioning

PhantomNet does not claim to replace every function of a large commercial SIEM, EDR, or SOAR product. Its purpose is narrower and practical: provide a **self-hosted, composable SOC foundation** that teams can inspect, operate, extend, and retain control over.
