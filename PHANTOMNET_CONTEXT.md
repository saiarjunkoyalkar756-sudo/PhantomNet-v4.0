# PHANTOMNET_CONTEXT.md
# Generated: 2026-05-28 | Phase 0 — Project Context File
# ═══════════════════════════════════════════════════════════════

---

## 1. PROJECT SUMMARY

**What PhantomNet Does:**
PhantomNet is an AI-driven autonomous cybersecurity platform (SOC-in-a-box). It ingests telemetry from distributed agents, normalizes and analyzes events using ML/AI engines, detects threats via behavioral analysis and rule-based IDS, triggers automated SOAR playbooks, and provides a React dashboard for SOC operators. It also includes red-teaming, forensics, compliance reporting, vulnerability management, blockchain audit trails, and honeypots.

**Technology Stack:**
- Backend: Python 3.11, FastAPI, SQLAlchemy (async), Pydantic v2, Loguru
- Message Bus: Apache Kafka (via Redpanda in Docker)
- Databases: PostgreSQL 15 (primary), Redis 7 (cache/rate-limit), Neo4j 5 (graph), SQLite (dev fallback)
- Frontend: React + Vite + Tailwind CSS
- Agent: Python 3.11, cross-platform (Linux/Windows/Termux/Android)
- Infrastructure: Docker Compose, Alembic migrations
- CI/CD: GitHub Actions (3 existing workflows)
- Security: JWT (RS256/HS256), mTLS, rate limiting (slowapi), PQC wrapper (conceptual)

**Total Services (docker-compose.yml):** 30 microservices + 4 infrastructure services (Redpanda, Postgres, Redis, Neo4j)

**Infrastructure Dependencies:**
- Redpanda (Kafka-compatible): port 9092/29092
- PostgreSQL: port 5432
- Redis: port 6379
- Neo4j: port 7474/7687

---

## 2. COMPLETE SERVICE MAP

| # | Service Name | Host Port | Entry Point | Purpose | Depends On | Kafka Topics (Produce→Consume) | DB |
|---|---|---|---|---|---|---|---|
| 1 | telemetry-ingestor | 8000 | `backend_api/telemetry_ingestor/main.py` | Receives agent telemetry, publishes to Kafka | Redpanda | → `telemetry-events` | None |
| 2 | gateway-service | 8001 | `backend_api/gateway_service/main.py` | Main API gateway, auth, routing, WebSocket | Postgres, Redis | ← `alerts` (WebSocket) | PostgreSQL |
| 3 | event-normalizer | 8002 | `backend_api/event_normalizer/main.py` | Normalizes raw telemetry events | Redpanda | `telemetry-events` → `normalized-events` | None |
| 4 | ai-behavioral-engine | 8003 | `backend_api/ai_behavioral_engine/main.py` | ML anomaly detection, UEBA, threat forecasting | Redpanda | `normalized-events` → `alerts`, `threat-predictions` | None |
| 5 | alert-storage | 8004 | `backend_api/alert_storage/main.py` | Persists alerts from Kafka to PostgreSQL | Redpanda, Postgres | ← `alerts` | PostgreSQL |
| 6 | command-dispatcher | 8005 | `backend_api/command_dispatcher/main.py` | Dispatches commands to agents | Redpanda | → `commands` | None |
| 7 | graph-intelligence-service | 8007 | `backend_api/graph_intelligence_service/main.py` | Graph-based threat analysis | Neo4j | ← `normalized-events` | Neo4j |
| 8 | vulnerability-management-service | 8019 | `backend_api/vulnerability_management_service/app.py` | CVE scanning, patch recommendations | Postgres | None | PostgreSQL |
| 9 | mitre-attack-mapper | 8009 | `backend_api/mitre_attack_mapper/app.py` | Maps events to MITRE ATT&CK techniques | None | None | None |
| 10 | cloud-security-service | 8010 | `backend_api/cloud_security_service/app.py` | Cloud posture management | None | None | None |
| 11 | siem-integration-service | 8011 | `backend_api/siem_integration_service/app.py` | SIEM log ingestion and normalization | None | None | None |
| 12 | sandbox-service | 8012 | `backend_api/sandbox_service/app.py` | Malware sandbox analysis | None | None | None |
| 13 | case-management-service | 8013 | `backend_api/case_management_service/app.py` | Security case/incident tracking | Postgres | None | PostgreSQL |
| 14 | compliance-reporting-service | 8014 | `backend_api/compliance_reporting_service/app.py` | Compliance report generation | None | None | None |
| 15 | threat-intelligence-service | 8015 | `backend_api/threat_intelligence_service/main.py` | OSINT, VirusTotal, MISP enrichment | Redis | None | Redis |
| 16 | soar-playbook-engine | 8016 | `backend_api/soar_playbook_engine/main.py` | SOAR playbook execution | Postgres, Redpanda | ← `soar-alerts` | PostgreSQL |
| 17 | playbook-flow-builder | 8017 | `backend_api/playbook_flow_builder/main.py` | Visual playbook builder | None | None | None |
| 18 | auto-response-engine | 8018 | `backend_api/auto_response_engine/main.py` | Automated response actions | soar-playbook-engine | None | None |
| 19 | siem-ingest-service | 8020 | `backend_api/siem_ingest_service/main.py` | SIEM event ingestion | Postgres | None | PostgreSQL |
| 20 | log-normalizer | 8021 | `backend_api/log_normalizer/main.py` | Log format normalization | None | None | None |
| 21 | phantomql-engine | 8022 | `backend_api/phantomql_engine/main.py` | Custom query language engine | Postgres | None | PostgreSQL |
| 22 | attack-graph-engine | 8023 | `backend_api/attack_graph_engine/main.py` | Attack path visualization | Neo4j | ← `normalized-events` | Neo4j |
| 23 | lateral-movement-detector | 8024 | `backend_api/lateral_movement_detector/main.py` | Detects lateral movement patterns | None | None | None |
| 24 | forensics-engine | 8025 | `backend_api/forensics_engine/main.py` | Digital forensics, timeline building | Postgres | None | PostgreSQL |
| 25 | compliance-service | 8026 | `backend_api/compliance_service/main.py` | Compliance checks (NIST, ISO, PCI) | Postgres | None | PostgreSQL |
| 26 | audit-log-collector | 8027 | `backend_api/audit_log_collector/main.py` | Collects and stores audit logs | Postgres | None | PostgreSQL |
| 27 | bas-engine | 8028 | `backend_api/bas_engine/main.py` | Breach & Attack Simulation | None | None | None |
| 28 | autonomous-blue-team | 8029 | `backend_api/autonomous_blue_team/main.py` | AI-driven defensive actions | soar-playbook-engine | ← `alerts` | None |
| 29 | ai-agent-orchestrator | 8030 | `backend_api/ai_agent_orchestrator/main.py` | Orchestrates AI agents | soar-playbook-engine, graph-intelligence | None | None |
| 30 | soar-engine (legacy) | N/A | `backend_api/soar_engine/app.py` | Full SOAR engine (older impl) | Postgres, Redpanda | ← `alerts` | PostgreSQL |

**Agent (phantomnet_agent):** Runs on endpoints. Collects telemetry, executes commands, runs honeypots, performs local analysis.

---

## 3. DATA FLOW MAP

### Flow 1 — Event Ingestion & Detection
```
Agent (endpoint)
  → POST /ingest to Telemetry Ingestor (:8000)
  → KafkaProducer → topic: "telemetry-events"
  → Event Normalizer consumes "telemetry-events"
      → Adds normalized_at, platform_schema_version, DNA tag
  → KafkaProducer → topic: "normalized-events"
  → AI Behavioral Engine consumes "normalized-events"
      → RuleBasedIDS + UEBAEngine + ThreatForecastingAI
      → If anomaly detected → KafkaProducer → topic: "alerts"
  → Alert Storage consumes "alerts" → INSERT INTO alerts (PostgreSQL)
  → Gateway WebSocket Manager consumes "alerts" → pushes to dashboard
  → SOAR Playbook Engine consumes "soar-alerts" (MISMATCH — see bugs)
      → Executes playbook steps (block_ip, isolate_host, create_ticket)
  → Auto Response Engine → executes response actions
  → Command Dispatcher → KafkaProducer → topic: "commands"
  → Agent receives command → executes countermeasure
```

### Flow 2 — Attack Graph
```
normalized-events → Attack Graph Engine (Neo4j)
                  → Graph Intelligence Service (Neo4j)
                  → Path Analyzer → attack paths stored
```

### Flow 3 — Vulnerability Management
```
CVE Scanner (asset_inventory) → PostgreSQL
  → Patch Recommendation AI scores CVEs
  → Case Management creates incident cases
  → Compliance Service updates compliance posture
```

### Flow 4 — Agent Registration
```
Agent starts → generates RSA key pair (stable from disk)
  → POST /api/agents/register to Gateway Service
  → Gateway validates, stores agent record in PostgreSQL
  → Returns signed JWT (RS256)
  → Agent uses JWT for all subsequent requests
  → Token refresh via /api/agents/refresh
```

---

## 4. CURRENT BUGS FOUND

### CRITICAL

| # | File | Line | Bug | Severity |
|---|---|---|---|---|
| C1 | `backend_api/gateway_service/main.py` | 349 | `redis_client` used in `rate_limit_middleware` but **never defined/initialized** — NameError on every request | CRITICAL |
| C2 | `backend_api/gateway_service/main.py` | 386 | `health_router` used in `app.include_router(health_router)` but **never imported** — NameError on startup | CRITICAL |
| C3 | `backend_api/gateway_service/main.py` | 382,385 | `app.include_router(iam_router)` called **twice** — duplicate route registration | CRITICAL |
| C4 | `backend_api/event_stream_processor/database.py` | 16 | **Hardcoded password** `password="password"` in database connection | CRITICAL |
| C5 | `phantomnet_agent/security/jwt_manager.py` | 54 | `hash(fingerprint)` used for JWT KID — Python `hash()` is **not stable across restarts** (randomized by PYTHONHASHSEED) — agents get new KID every restart, breaking token validation | CRITICAL |
| C6 | `backend_api/ai_behavioral_engine/consumer.py` | 19 | Kafka topic `'attack_logs'` (default) but `ai_behavioral_engine/main.py` uses `'normalized-events'` — **two different consumers for same engine, topic mismatch** | CRITICAL |
| C7 | `backend_api/soar_engine/consumer.py` | ~1 | SOAR engine consumes topic `'alerts'` but `soar-playbook-engine` in docker-compose is configured with `SOAR_ALERT_TOPIC: 'soar-alerts'` — **topic name mismatch breaks SOAR pipeline** | CRITICAL |
| C8 | `backend_api/shared/settings.py` | 22 | `SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"` — **hardcoded default secret key** in settings | CRITICAL |
| C9 | `backend_api/shared/database.py` | 14 | `DATABASE_URL` defaults to `"postgresql+asyncpg://phantomnet:changeme@localhost:5432/phantomnet"` — **hardcoded credentials in default** | CRITICAL |
| C10 | `docker-compose.yml` | multiple | `phantom_internal` and `phantom_frontend` networks are **referenced but never defined** at top-level `networks:` block — Docker Compose will fail to start | CRITICAL |

### HIGH

| # | File | Line | Bug | Severity |
|---|---|---|---|---|
| H1 | `backend_api/telemetry_ingestor/` | — | **Missing `__init__.py`** — breaks Python package imports | HIGH |
| H2 | `backend_api/alert_storage/` | — | **Missing `__init__.py`** — breaks Python package imports | HIGH |
| H3 | `backend_api/event_normalizer/` | — | **Missing `__init__.py`** — breaks Python package imports | HIGH |
| H4 | `backend_api/ai_behavioral_engine/` | — | **Missing `__init__.py`** — breaks Python package imports | HIGH |
| H5 | `backend_api/soar_engine/consumer.py` | 536,543,731,738 | `datetime.utcnow()` deprecated in Python 3.12+ — use `datetime.now(timezone.utc)` | HIGH |
| H6 | `backend_api/soar_engine/soar_playbook_engine.py` | 84,108 | `datetime.utcnow()` deprecated | HIGH |
| H7 | `backend_api/soar_engine/app.py` | 175,195 | `datetime.utcnow()` deprecated | HIGH |
| H8 | `backend_api/soar_engine/auto_response_engine.py` | 44,124,127 | `datetime.utcnow()` deprecated | HIGH |
| H9 | `backend_api/soar_engine/human_in_the_loop.py` | 54,79,105,151 | `datetime.utcnow()` deprecated | HIGH |
| H10 | `backend_api/siem_integration_service/log_normalizer.py` | 37,70 | `datetime.utcnow()` deprecated | HIGH |
| H11 | `backend_api/siem_integration_service/phantomql_engine.py` | 104 | `datetime.utcnow()` deprecated | HIGH |
| H12 | `backend_api/event_stream_processor/app.py` | 65 | **f-string SQL injection** — `f"SELECT * FROM events {where_sql}..."` — unsanitized input in SQL query | HIGH |
| H13 | `backend_api/case_management_service/database.py` | 141 | **f-string SQL** — `f"UPDATE cases SET {', '.join(set_clauses)}..."` — potential SQL injection | HIGH |
| H14 | `phantomnet_agent/security/jwt_manager.py` | 60 | `datetime.utcnow()` used in `get_token()` — deprecated | HIGH |
| H15 | `backend_api/shared/security_utils.py` | ~100 | `signer.update()` / `verifier.update()` / `signer.finalize()` / `verifier.verify()` — **deprecated cryptography API** (removed in cryptography>=40) — use `sign()` / `verify()` directly | HIGH |
| H16 | `backend_api/gateway_service/main.py` | ~200 | CORS only set for `gateway-service` via factory; most other services created with `create_phantom_service()` have **no CORS configured** | HIGH |
| H17 | `docker-compose.yml` | multiple | Most services (command-dispatcher, graph-intelligence, vuln-mgmt, etc.) have **no `networks:` assignment** — they cannot communicate with each other | HIGH |
| H18 | `docker-compose.yml` | alert-storage | `alert-storage` service has **no `networks:` assignment** — cannot reach Redpanda or Postgres | HIGH |

### MEDIUM

| # | File | Line | Bug | Severity |
|---|---|---|---|---|
| M1 | `backend_api/lateral_movement_detector/main.py` | 47 | Detection rule hardcodes `destination_host == "critical_server_prod"` — **placeholder hostname** | MEDIUM |
| M2 | `backend_api/lateral_movement_detector/main.py` | 48 | Source IP check uses string `"10.0.0.0/8"` instead of actual CIDR matching — **broken logic** | MEDIUM |
| M3 | `backend_api/soar_engine/consumer.py` | ~1 | `import os` present but `os.getenv("ORCHESTRATOR_API_URL")` uses `localhost:8000` default — **hardcoded localhost** | MEDIUM |
| M4 | `backend_api/shared/settings.py` | all | Settings class missing `KAFKA_BOOTSTRAP_SERVERS`, `JWT_SECRET_KEY`, `NEO4J_PASSWORD`, `DB_PASSWORD` — **incomplete settings** | MEDIUM |
| M5 | `backend_api/ai_behavioral_engine/main.py` | ~130 | `consume_and_process_kafka_messages()` has comment `# ... processing logic (UEBA, IDS, etc.) ...` — **stub/incomplete processing** | MEDIUM |
| M6 | `backend_api/shared/database.py` | ~50 | `created_at = Column(DateTime, default=datetime.datetime.utcnow)` — deprecated, not timezone-aware | MEDIUM |
| M7 | `features/phantom_chain/decentralized_trust_fabric.py` | 94,130 | `datetime.datetime.utcnow()` deprecated | MEDIUM |
| M8 | `backend_api/gateway_service/main.py` | ~380 | `# from .analyzer.neural_threat_brain import get_qa_pipeline` and multiple commented-out routers — dead code | MEDIUM |
| M9 | `infra/postgres/schema.sql` | all | Schema only has `alerts` table — **missing all other tables** (users, tenants, cases, compliance, forensics, etc.) | MEDIUM |
| M10 | `docker-compose.yml` | multiple | No `healthcheck:` defined for any service — `depends_on` without `condition: service_healthy` is unreliable | MEDIUM |
| M11 | `docker-compose.yml` | multiple | `alert-storage`, `command-dispatcher`, and many services missing `networks:` — isolated from each other | MEDIUM |
| M12 | `backend_api/soar_playbook_engine/main.py` | all | Separate `soar_playbook_engine` service exists alongside `soar_engine` — **duplicate/conflicting SOAR implementations** | MEDIUM |

### LOW

| # | File | Line | Bug | Severity |
|---|---|---|---|---|
| L1 | Multiple files | — | Missing type hints on many functions | LOW |
| L2 | `backend_api/gateway_service/main.py` | ~50 | `from typing import Optional, List, Dict, Any` imported **twice** | LOW |
| L3 | `backend_api/shared/settings.py` | 22 | `SECRET_KEY` field name conflicts with `JWT_SECRET_KEY` env var used in gateway | LOW |
| L4 | `backend_api/soc_copilot_service/models.py` | all | **Empty file** (0 bytes) | LOW |
| L5 | `backend_api/siem_integration_service/models.py` | all | **Empty file** (0 bytes) | LOW |
| L6 | `phantomnet_agent/analyzers/ai_client.py` | all | **Empty file** (0 bytes) | LOW |
| L7 | `phantomnet_agent/analyzers/local_rules_engine.py` | all | **Empty file** (0 bytes) | LOW |
| L8 | `backend_api/event-normalizer/` | — | Duplicate directory `event-normalizer` (hyphen) alongside `event_normalizer` (underscore) — **duplicate service** | LOW |

---

## 5. MISSING CONNECTIONS

### Kafka Topic Mismatches
| Producer Topic | Consumer Topic | Services Affected | Status |
|---|---|---|---|
| `telemetry-events` | `telemetry-events` | telemetry-ingestor → event-normalizer | ✅ CONNECTED |
| `normalized-events` | `normalized-events` | event-normalizer → ai-behavioral-engine (main.py) | ✅ CONNECTED |
| `normalized-events` | `attack_logs` (default) | event-normalizer → ai-behavioral-engine (consumer.py) | ❌ BROKEN |
| `alerts` | `soar-alerts` | ai-behavioral-engine → soar-playbook-engine | ❌ BROKEN |
| `alerts` | `alerts` | ai-behavioral-engine → alert-storage | ✅ CONNECTED |
| `alerts` | `alerts` | ai-behavioral-engine → autonomous-blue-team | ✅ CONNECTED |
| `alerts` | `alerts` | ai-behavioral-engine → gateway WebSocket | ✅ CONNECTED |
| `commands` | (no consumer defined) | command-dispatcher → agent | ❌ MISSING consumer |
| `threat-predictions` | (no consumer defined) | ai-behavioral-engine → ? | ❌ MISSING consumer |

### Missing Environment Variables (not in .env.example)
- `NEO4J_PASSWORD` — referenced in docker-compose but not in `.env.example`
- `ORCHESTRATOR_API_URL` — hardcoded `localhost:8000` in soar consumer
- `SOAR_ENGINE_URL` — auto-response-engine calls soar but URL not configurable
- `REDIS_URL` — in `.env.example` but `shared/settings.py` uses `REDIS_HOST`/`REDIS_PORT` separately

### Missing Database Tables (schema.sql only has `alerts`)
- `users`, `tenants` — used by gateway_service/database.py
- `cases` — used by case_management_service
- `compliance_findings` — used by compliance_service
- `forensics_jobs`, `forensics_evidence` — used by forensics_engine
- `audit_logs` — used by audit_log_collector
- `vulnerabilities`, `cve_records` — used by vulnerability_management_service
- `playbooks`, `playbook_runs` — used by soar_playbook_engine
- `assets` — used by asset_inventory_service
- `attack_logs`, `blacklisted_ips` — used by gateway_service

### Services Expecting Things That Don't Exist
- `gateway_service/main.py` imports `health_router` — not defined anywhere
- `gateway_service/main.py` uses `redis_client` — not initialized
- `backend_api/shared/database.py` defines `SessionLocal` (sync) but gateway imports it for async operations
- `backend_api/event-normalizer/` (hyphen dir) and `backend_api/event_normalizer/` (underscore dir) — both exist, docker-compose uses the hyphen version's Dockerfile but Python imports use underscore

---

## 6. CI/CD STATUS

### Existing Workflows
| File | Purpose | Status |
|---|---|---|
| `.github/workflows/ci.yml` | Backend tests, security audit, frontend build, playbook smoke test | ✅ EXISTS — functional but `|| true` on tests means failures don't block |
| `.github/workflows/build-and-test.yml` | Multi-platform agent build and test | ✅ EXISTS |
| `.github/workflows/platforms.yml` | Platform-specific tests | ✅ EXISTS |

### Missing Workflows
- **CD pipeline** — no deployment workflow (staging/production)
- **Security scan** — no weekly CVE/SAST/secrets scan
- **Docker image build & push** — no ECR push workflow
- **Integration tests** — no docker-compose spin-up + end-to-end test
- **Coverage enforcement** — `|| true` means broken tests pass CI

### CI Issues
- `ci.yml` uses `|| true` on pytest — broken tests never fail the build
- No minimum coverage threshold enforced
- No `bandit` or `mypy` static analysis
- No `trivy` container scanning
- No secrets detection (truffleHog/gitleaks)

---

## 7. TEST COVERAGE

### What Is Tested
- `backend_api/shared/test_auth.py` — auth utilities
- `backend_api/shared/test_security_utils.py` — security utils
- `backend_api/shared/test_threat_intelligence.py` — threat intel
- `backend_api/shared/test_pnql_engine.py` — PNQL query engine
- `backend_api/shared/test_asset_management.py` — asset management
- `backend_api/shared/test_report_service.py` — report service
- `backend_api/tests/test_soar_engine.py` — SOAR engine (basic)
- `backend_api/tests/test_ai_behavioral_engine.py` — behavioral engine
- `backend_api/tests/test_microsegmentation_service.py` — microsegmentation
- `backend_api/tests/test_zero_trust_manager.py` — zero trust
- `backend_api/gateway_service/test_app.py` — gateway app
- `backend_api/log_parsers/test_aws_cloudtrail_parser.py` — log parsers
- `phantomnet_agent/tests/` — collectors, bus, honeypots, plugins, network
- `tests/linux/`, `tests/windows/` — platform-specific agent tests
- `blockchain_layer/test_blockchain.py` — blockchain layer
- `features/*/test_*.py` — feature module tests

### What Has No Tests
- `telemetry_ingestor` — no tests
- `event_normalizer` — no tests
- `alert_storage` — no tests
- `ai_behavioral_engine` — minimal (no Kafka integration test)
- `forensics_engine` — no tests
- `compliance_service` — no tests
- `lateral_movement_detector` — no tests
- `vulnerability_management_service` — no tests
- `case_management_service` — no tests
- `audit_log_collector` — no tests
- `soar_playbook_engine` — no tests
- `attack_graph_engine` — no tests
- `graph_intelligence_service` — no tests
- `phantomql_engine` — no tests
- `command_dispatcher` — no tests
- `auto_response_engine` — no tests
- `dashboard_frontend` — no tests

### Broken Tests (likely)
- Any test importing from services with missing `__init__.py`
- Tests relying on `redis_client` in gateway (undefined)
- Tests using `datetime.utcnow()` on Python 3.12+

---

## 8. ARCHITECTURE DECISIONS

### Well Designed
- **`create_phantom_service()` factory** — standardizes all microservices with consistent middleware, health checks, logging, and error handling
- **`get_secret()` in secret_manager.py** — fails hard on missing secrets, preventing insecure startup
- **`JtiStore` for JWT replay protection** — pluggable, well-structured
- **Pydantic v2 settings** — type-safe configuration
- **Structured JSON logging** via Loguru — good for production observability
- **`backend_api/core/exceptions.py`** — standard exception hierarchy exists
- **Agent platform abstraction layer** — `platform_compatibility/` cleanly separates OS-specific code
- **Alembic migrations** — migration infrastructure exists

### Needs Refactoring
- **Duplicate SOAR implementations** — `soar_engine/` and `soar_playbook_engine/` overlap significantly
- **Duplicate event normalizer** — `event-normalizer/` (hyphen) and `event_normalizer/` (underscore) both exist
- **Kafka topic names scattered** — no single source of truth; topics defined as string literals in each service
- **`shared/settings.py` incomplete** — missing many env vars that services use directly via `os.environ.get()`
- **`infra/postgres/schema.sql` minimal** — only `alerts` table; most services create their own tables ad-hoc
- **`backend_api/shared/database.py` mixes sync/async** — `SessionLocal` (sync) and `AsyncSessionLocal` (async) both defined, causing confusion
- **`ai_behavioral_engine` has two files** — `consumer.py` (old) and `main.py` (new) with different topic names

### Security Risks
- **`hash()` for JWT KID** — Python hash is randomized per process; KID changes on every restart, breaking token validation across restarts
- **Hardcoded `password="password"`** in `event_stream_processor/database.py`
- **`SECRET_KEY` default** in `shared/settings.py` — if `.env` not set, uses weak default
- **f-string SQL** in `event_stream_processor/app.py` and `case_management_service/database.py` — SQL injection risk
- **Deprecated cryptography API** in `security_utils.py` — `signer.update()/finalize()` removed in newer cryptography versions
- **CORS not configured** on most microservices (only gateway has it)
- **No `networks:` top-level block** in docker-compose — `phantom_internal`/`phantom_frontend` networks referenced but not declared
- **`redis_client` undefined** in gateway — rate limiting middleware crashes on every request
- **`health_router` undefined** in gateway — service crashes on startup
- **Lateral movement detector** uses hardcoded hostname `"critical_server_prod"` and broken CIDR check

---

## 9. SUMMARY COUNTS

- **Total Python files:** ~280 (excluding PhantomNet-v3.0)
- **Total services in docker-compose:** 30
- **Critical bugs:** 10
- **High bugs:** 18
- **Medium bugs:** 12
- **Low bugs:** 8
- **Missing `__init__.py`:** 4 services
- **Kafka topic mismatches:** 2 broken, 2 missing consumers
- **Missing DB tables:** ~10
- **Test files:** 37
- **Services with zero tests:** ~17
- **CI/CD workflows:** 3 existing, 4 missing

---

*This file will be updated as fixes are applied in subsequent phases.*
