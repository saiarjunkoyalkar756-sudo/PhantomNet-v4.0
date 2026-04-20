# CLAUDE.md — PhantomNet v4.0 Reception Desk

> **Purpose:** This file is the single entry point for AI assistants (Claude, Gemini, etc.).
> Do NOT load every file in the repo. Instead, read this file first to understand the
> project map, then navigate to the specific "room" (directory/file) you need.
> Load code files only on demand, scoped to the task at hand.

---

## 🏢 What Is PhantomNet?

PhantomNet is a **production-grade, autonomous cybersecurity platform** built as a distributed
microservice grid. It provides XDR-level endpoint visibility, AI-driven behavioral analysis,
SOAR automation, blockchain audit trails, and a React-based SOC dashboard.

**Stack:** Python 3.11 (FastAPI) · React 18 (Vite + Tailwind) · PostgreSQL · Redis/Kafka · Docker

---

## 🗺️ Project Code-Review Graph

A token-efficient map of every major component. Read depth = need.

```
PhantomNet-v4.0/
│
├── 📋 CLAUDE.md                    ← YOU ARE HERE (reception desk)
├── 📋 README.md                    ← High-level overview + install guide
├── 📋 CHANGELOG.md                 ← Version history
├── 📋 docker-compose.yml           ← Full service orchestration (12 services)
├── 📋 .env / .env.example          ← All environment variables (secrets template)
├── 📋 alembic.ini                  ← DB migration config
├── 📋 requirements.txt             ← Root-level Python deps
├── 🖥️  run_all.py                   ← Dev launcher (starts all services locally)
├── 🖥️  run_manual.ps1               ← Windows manual runner
├── 🖥️  Start-PhantomNet.ps1         ← Quick start (Windows)
├── 🖥️  Stop-PhantomNet.ps1          ← Quick stop (Windows)
│
├── backend_api/                    ← [ROOM 1] All Python microservices
├── dashboard_frontend/             ← [ROOM 2] React SOC dashboard
├── phantomnet_agent/               ← [ROOM 3] Endpoint agent (cross-platform)
├── blockchain_layer/               ← [ROOM 4] Immutable audit chain
├── features/                       ← [ROOM 5] Advanced AI/research modules
├── infra/                          ← [ROOM 6] Docker + Postgres infra configs
├── DOCS/                           ← [ROOM 7] All documentation
├── tests/                          ← [ROOM 8] Integration & unit test suites
├── plugins/                        ← [ROOM 9] Plugin marketplace modules
└── mitre_data/                     ← [ROOM 10] MITRE ATT&CK datasets
```

---

## 🚪 Room Directory — Navigate by Task

### [ROOM 1] `backend_api/` — Microservice Grid

The heart of PhantomNet. Each subdirectory is a self-contained FastAPI microservice.

| Service Directory | Port | Responsibility |
|---|---|---|
| `gateway_service/` | 8000 | API Gateway — auth, routing, rate-limiting |
| `ai_behavioral_engine/` | 8001 | UEBA + ML anomaly detection |
| `soar_engine/` / `soar_playbook_engine/` | 8002 | SOAR automation + playbook execution |
| `correlation_engine/` | 8003 | Multi-event threat correlation |
| `threat_intelligence_service/` | 8004 | MISP/OSINT enrichment |
| `mitre_attack_mapper/` | 8005 | ATT&CK TTP tagging |
| `siem_ingest_service/` | 8006 | Raw log ingestion |
| `log_normalizer/` | 8007 | Log normalization → common schema |
| `phantomql_engine/` / `pnql_engine/` | 8008 | PNQL query engine |
| `alert_storage/` | 8009 | Alert persistence + retrieval |
| `blockchain_service/` | 8010 | Blockchain write client |
| `event_stream_processor/` | 8011 | Kafka/Redis event pipeline |
| `asset_inventory_service/` | 8012 | Asset + attack surface mapping |
| `dfir_toolkit/` | 8013 | YARA, memory forensics, PCAP |
| `bas_engine/` | 8014 | Breach & Attack Simulation |
| `autonomous_blue_team/` | 8015 | Autonomous defensive AI |
| `plugin_marketplace/` | 8016 | Plugin registry + loader |
| `iam_service/` | 8017 | Identity & access management |
| `case_management_service/` | 8018 | Incident case tracking |
| `compliance_service/` | 8019 | Compliance reporting |
| `vulnerability_scanner_service/` | 8020 | Vuln discovery + CVE mapping |
| `soc_copilot_service/` | 8021 | AI SOC analyst assistant |
| `attack_graph_engine/` | 8022 | Live attack path graph |
| `lateral_movement_detector/` | 8023 | Lateral movement detection |
| `forensics_engine/` | 8024 | Automated forensics orchestration |
| `dashboard_service/` | 8025 | Dashboard data aggregator |
| `chatbot_service/` | 8026 | NLP chatbot interface |
| `shared/` | — | Shared utilities: `logger_config.py`, `db.py`, models |
| `schemas/` | — | Pydantic request/response schemas |
| `routes/` | — | Shared route definitions |

**Key shared files (load these for cross-service work):**
- `backend_api/shared/logger_config.py` — Logging setup (known bug: pass string, not int, to log level)
- `backend_api/core_config.py` — Global config constants
- `backend_api/requirements.txt` — All Python dependencies

---

### [ROOM 2] `dashboard_frontend/` — React SOC Dashboard

**Stack:** React 18 · Vite · Tailwind CSS · Redux Toolkit

```
dashboard_frontend/src/
├── pages/          ← Route-level page components (Dashboard, Alerts, SIEM, SOAR…)
├── components/     ← Reusable UI components (charts, tables, modals)
├── features/       ← Redux slices (state management per domain)
├── services/       ← Axios API client + WebSocket hooks
├── store/          ← Redux store setup
├── router/         ← React Router v6 routes (index.jsx)
├── styles/         ← Global CSS + Tailwind overrides
└── lib/            ← Utility helpers
```

**Entry points:**
- `dashboard_frontend/src/main.jsx` — App bootstrap
- `dashboard_frontend/src/router/index.jsx` — All routes (currently open in editor)
- `dashboard_frontend/package.json` — npm scripts: `npm run dev`, `npm run build`
- `dashboard_frontend/vite.config.js` — Vite config + proxy settings

---

### [ROOM 3] `phantomnet_agent/` — Endpoint Agent

Cross-platform (Windows / Linux / Android Termux) telemetry + response agent.

```
phantomnet_agent/
├── main.py             ← Agent entry point (33 KB — load only when modifying agent)
├── agent.py            ← Core agent loop
├── orchestrator.py     ← Collector/action orchestration (19 KB)
├── collectors/         ← Host telemetry collectors (process, network, file, etc.)
├── actions/            ← Response actions (kill, quarantine, block IP)
├── analyzers/          ← Local analysis modules
├── ebpf_*.py           ← eBPF kernel monitors (Linux only)
├── config/             ← Agent config files
├── platform_compatibility/ ← OS abstraction layer
├── pyinstaller/        ← PyInstaller spec files for binary builds
├── tests/              ← Agent-specific tests
└── docs/               ← Agent usage docs
```

**Install scripts (root level):**
- `install_windows.ps1` — Windows agent service installer
- `install_linux.sh` — Linux systemd service installer
- `install_termux.sh` — Android Termux installer

---

### [ROOM 4] `blockchain_layer/` — Audit Chain

```
blockchain_layer/
├── blockchain.py           ← Core chain logic (hashing, block creation)
├── blockchain_client.py    ← Client for writing audit events
├── test_blockchain.py      ← Full unit test suite
└── schemas/                ← Block data schemas
```

---

### [ROOM 5] `features/` — Advanced Research Modules

Advanced capabilities. Load only when working on specific modules.

| Directory | What it actually does |
|---|---|
| `behavioral_biometrics/` | Continuous auth via keystroke dynamics + pointer telemetry (UEBA) |
| `snapshot_recovery/` | Timestamped file/dir snapshots with ring-buffer rotation + rollback |
| `pqc_readiness/` | Post-Quantum Crypto audit: ML-KEM/Kyber, ML-DSA/Dilithium readiness |
| `device_fingerprint/` | Hardware-bound 128-bit identity hash (hostname, MAC, arch, FQDN) |
| `self_evolving_threat_brain/` | Adaptive threat model with self-learning feedback loop |
| `ai_autonomy_levels/` | Configurable AI autonomy tiers (passive → active response) |
| `ai_threat_marketplace/` | Threat intel sharing marketplace logic |
| `phantom_os/` | Hardened OS baseline enforcement layer |
| `cognitive_core_intelligence/` | Multi-modal cognitive reasoning engine |
| `phantom_chain/` | Extended blockchain features (multi-node, federation) |
| `synthetic_cyber_twin_universe/` | Digital twin simulation for pre-deployment testing |
| `neural_federation_council/` | Federated learning coordination across agent nodes |

---

### [ROOM 6] `infra/` — Infrastructure

```
infra/
├── docker/       ← Service-specific Dockerfiles
└── postgres/     ← Postgres init scripts + schema seeds
```

**Root-level Docker files:**
- `docker-compose.yml` — Full 12-service stack (primary deployment)
- `Dockerfile.backend` — Backend image
- `Dockerfile.event_stream_processor` — Event pipeline image
- `Dockerfile.orchestrator` — Agent orchestrator image

---

### [ROOM 7] `DOCS/` — Documentation

| File | Contents |
|---|---|
| `ARCHITECTURE.md` | System architecture + data flow |
| `API_DOCUMENTATION.md` | REST API reference |
| `DEPLOYMENT_GUIDE.md` | Docker + bare-metal deployment |
| `DEVELOPER_GUIDE.md` | Dev setup + contribution guide |
| `EVENT_BUS_SCHEMA.md` | Kafka/Redis topic schemas |
| `database_schemas.md` | PostgreSQL table definitions |
| `NETWORKING_ARCHITECTURE.md` | Network topology + security |
| `OPERATIONS.md` | Runbook + ops procedures |
| `deployment_strategy.md` | Multi-env deployment strategy |
| `multi_tenancy_plan.md` | Multi-tenant architecture plan |

---

### [ROOM 8] `tests/` — Test Suites

```
tests/                  ← Root integration tests
backend_api/tests/      ← Service-level unit tests
phantomnet_agent/tests/ ← Agent unit tests
blockchain_layer/test_blockchain.py ← Blockchain tests
```

**Run tests:**
```bash
pytest tests/ -v
pytest backend_api/tests/ -v
```

---

### [ROOM 9] `plugins/` — Plugin System

Loadable plugin modules that extend PhantomNet via the plugin marketplace.

---

### [ROOM 10] `mitre_data/` — ATT&CK Data

MITRE ATT&CK enterprise matrices, tactic/technique JSON used by `mitre_attack_mapper/`.

---

## 🔑 Key Configuration Files

| File | When to Load |
|---|---|
| `.env` | Any service startup or secrets issue |
| `.env.example` | Onboarding / environment setup |
| `docker-compose.yml` | Container orchestration changes |
| `alembic.ini` | Database migration work |
| `pytest.ini` | Test configuration |
| `requirements.txt` (root) | Root-level dependency changes |
| `backend_api/requirements.txt` | Backend-specific dep changes |

---

## 📡 Service Communication Map

```
[React Dashboard] ←HTTP/WS→ [API Gateway :8000]
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                       ▼
    [AI Behavioral :8001]  [SOAR Engine :8002]   [Threat Intel :8004]
              │                     │                       │
              └─────────────────────┴───────────────────────┘
                                    │
                         [Message Bus: Redis/Kafka]
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                       ▼
    [Event Stream :8011]  [Alert Storage :8009]  [Blockchain :8010]
              │
     [PhantomNet Agent] ←──── [Command Dispatcher]
```

---

## ⚡ Quick Task Router

Use this table to jump directly to the right room for your task.

| Task | Go To |
|---|---|
| Fix API endpoint / add route | `backend_api/gateway_service/` + `backend_api/routes/` |
| Add/fix a microservice | `backend_api/<service_name>/main.py` |
| Fix shared logging bug | `backend_api/shared/logger_config.py` |
| Modify DB schema | `backend_api/alembic/` + `DOCS/database_schemas.md` |
| Add Kafka/Redis topic | `DOCS/EVENT_BUS_SCHEMA.md` + `backend_api/event_stream_processor/` |
| Change frontend route | `dashboard_frontend/src/router/index.jsx` |
| Add dashboard page | `dashboard_frontend/src/pages/` |
| Add Redux state | `dashboard_frontend/src/features/` + `dashboard_frontend/src/store/` |
| Fix agent collector | `phantomnet_agent/collectors/` |
| Add agent action | `phantomnet_agent/actions/` |
| Modify blockchain log | `blockchain_layer/blockchain.py` |
| Add SOAR playbook | `backend_api/soar_playbook_engine/` |
| Add YARA rule | `backend_api/dfir_toolkit/` + `phantomnet_agent/yara_rules.yar` |
| MITRE mapping | `backend_api/mitre_attack_mapper/` + `mitre_data/` |
| Add plugin | `plugins/` + `backend_api/plugin_marketplace/` |
| Run full stack | `docker-compose.yml` → `docker-compose up -d` |
| Run locally (Windows) | `Start-PhantomNet.ps1` or `python run_all.py` |
| View/add docs | `DOCS/` |
| Run tests | `pytest tests/ -v` |

---

## 🧠 Known Issues & Gotchas

1. **Logger bug** — `backend_api/shared/logger_config.py`: Always pass a `str` to
   `.upper()`, never an `int`. Log level env var must be a string like `"INFO"`.

2. **Import paths** — All services use absolute imports from `backend_api.` prefix.
   Relative imports (`from . import …`) will fail on Windows.

3. **Duplicate directories** — `event-normalizer/` and `event_normalizer/` both exist.
   The canonical one is `event_normalizer/` (underscore). The hyphenated version is legacy.

4. **Agent eBPF** — `ebpf_*.py` files only function on Linux with kernel ≥ 5.8 and
   BCC installed. They silently no-op on Windows/Termux.

5. **Port collisions** — Services claim sequential ports 8000–8025. Check
   `docker-compose.yml` for the authoritative port map before adding a new service.

6. **PNQL duplication** — Both `phantomql_engine/` and `pnql_engine/` exist.
   `pnql_engine/` is the current implementation; `phantomql_engine/` is legacy.

---

## 🔒 Security Notes

- **Never commit** `.env` with real secrets.
- JWT secret is in `.env` → `JWT_SECRET_KEY`.
- Blockchain keys are in `phantomnet_agent/certs/`.
- All inter-service calls use bearer tokens validated by `gateway_service/`.

---

## 📌 Gemini Feature Implementation Map

When a Gemini-style feature number is selected, use this map to find the right rooms:

| Feature # | Feature | Primary Rooms |
|---|---|---|
| #1 | XDR-Level Agent | `phantomnet_agent/` |
| #2 | Threat Correlation Engine | `backend_api/correlation_engine/` |
| #3 | AI Behavioral Engine (UEBA) | `backend_api/ai_behavioral_engine/`, `features/behavioral_biometrics/` |
| #4 | SOAR Automation Engine | `backend_api/soar_engine/`, `soar_playbook_engine/` |
| #5 | Real-Time Event Pipeline | `backend_api/event_stream_processor/`, `DOCS/EVENT_BUS_SCHEMA.md` |
| #6 | Asset Inventory & Attack Surface | `backend_api/asset_inventory_service/`, `attack_graph_engine/` |
| #7 | Threat Intelligence Engine | `backend_api/threat_intelligence_service/` |
| #8 | MITRE ATT&CK Mapping | `backend_api/mitre_attack_mapper/`, `mitre_data/` |
| #9 | Dashboard Upgrades | `dashboard_frontend/src/pages/`, `dashboard_frontend/src/components/` |
| #10 | DFIR Toolkit | `backend_api/dfir_toolkit/`, `phantomnet_agent/yara_rules.yar` |
| #11 | BAS Engine | `backend_api/bas_engine/`, `phantomnet_agent/red_teaming/playbooks/` |
| #12 | Autonomous Blue Team | `backend_api/autonomous_blue_team/`, `features/snapshot_recovery/` |
| #13 | Plugin Marketplace | `backend_api/plugin_marketplace/`, `plugins/` |
| #14 | PNQL Query Language | `backend_api/pnql_engine/` |
| #15 | Blockchain Audit Layer | `blockchain_layer/`, `backend_api/blockchain_service/` |
| — | PQC Readiness Audit | `features/pqc_readiness/quantum_defense.py` |
| — | Device Identity / Zero-Trust | `features/device_fingerprint/evolutionary_genetics.py` |

---

*Last updated: 2026-04-19 | PhantomNet v4.0 — post code-review hardening*

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
