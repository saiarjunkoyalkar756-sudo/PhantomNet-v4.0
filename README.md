# 🌌 PhantomNet v4.0 — Autonomous SOC & XDR Platform

[![Release v4.0](https://img.shields.io/badge/release-v4.0-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-%233776AB.svg)]()
[![Node](https://img.shields.io/badge/node-18-%234CC61E.svg)]()
[![Build Status](https://img.shields.io/github/actions/workflow/status/saiarjunkoyalkar756-sudo/PhantomNet-v4.0/ci.yml?branch=main)]()

![PhantomNet Image](docs/images/file_000000004544720988d35dea5d77e630.png)

---

PhantomNet v4.0 is a production-grade, distributed autonomous cyber defense, Breach and Attack Simulation (BAS), and XDR operations grid. It automates high-speed threat ingestion, correlates security events with a custom query AST compiler, logs integrity audits onto an immutable blockchain ledger, and deploys cross-platform telemetry endpoint agents.

---

## 🌌 What is PhantomNet v4.0?

PhantomNet is a state-of-the-art security control validation and autonomous response architecture designed to defend modern enterprise infrastructure. It allows organizations to simulate complex adversary campaigns in a safe sandbox while actively validating and calibrating their production-grade defense pipelines (WAFs, EDRs, firewalls, and SIEMs).

### 🛡️ Core Defensive Pillars
* **Breach & Attack Emulation:** Automates continuous, gradated simulations from simple SQL injections and link-based phishing campaigns up to advanced Golden Ticket Active Directory takeovers, supplying the exact threat profile to the sensors.
* **Autonomous SOAR Orchestration:** Parses threat vectors dynamically to calculate risk exposures. If the defense evaluation drops below strict thresholds, the SOAR engine executes dynamic containment countermeasures (including host network isolation, active malicious process terminations, and firewall IP blockades).
* **Automated Volatile Forensics:** Immediately compiles forensic capture jobs (e.g. Volatility RAM memory dumps, syslog archives) the moment a high-risk alert triggers, preserving volatile artifact evidence in the Forensics Vault.
* **Immutable Security Ledgers:** Cryptographically logs alert audits onto an immutable blockchain ledger to enforce absolute accountability and audit compliance, preventing internal tampering.

### ⛓️ The Telemetry Pipeline (Under the Hood)
When a threat is simulated or detected, the event traverses a real-time production data stack:
1. **Dynamic Rate Limiting (Redis):** The API Gateway checks the source IP against blocked IP lists and limits socket rates via Redis pipeline counters to prevent ingestion flooding.
2. **Telemetry Ingestion Bus (Redpanda):** Structured events are published to Redpanda/Kafka queues (`normalized_events`) to absorb high-frequency thread spikes.
3. **AI Analysis & Correlation Core (PostgreSQL):** The Event Normalizer and AI Core parse the stream, mapping alerts to PostgreSQL relation schemas and storing transactional SOAR states.
4. **Attack Path Mapping (Neo4j):** Mapped relations are evaluated inside a Bolt graph database to visualize adversary lateral movements and directory privilege escalations.

---

## ⚡ What's New in v4.0

### 🎨 1. Enterprise Next.js Marketing & User Portals
We have integrated a comprehensive Next.js 16 (App Router + Turbopack + Tailwind v4) large-scale marketing and interactive portals portal:
* **🛡️ User Shield Portal (`/user`):** Manage host endpoint posture scores, check active network decoy honeypot statuses, stream live security telemetry event logs, and rotate ephemeral Zero-Trust session handshake tokens.
* **🎛️ Admin Commander Portal (`/admin`):** Supervise microservice infrastructure grids, query live node cluster load averages, manage firewall IP bans interactively with real database synchronization, and launch Breach & Attack Simulations (BAS) to test playbook automations.
* **🔑 Quantum Cryptographic Audit:** Interacts directly with backend APIs to assess post-quantum readiness (Kyber-1024/Dilithium) and check Shor-vulnerable asymmetric algorithms.

### ⚙️ 2. Core Backend Enhancements
* **Gateway Ingestor Decoupling:** Re-engineered HTTP logging sinks using background-daemon thread buffers, resulting in a **100x test suite speedup (from 60s to 0.6s)** under network IO latency.
* **Authenticated Database Blacklisting APIs:** Expanded administrative routers to support GET `/admin/blacklist/list` queries alongside existing POST blocks, connecting real Postgres data directly with our frontend dashboard interface.
* **Python 3.11/3.12 Docker Upgrades:** Built and configured all microservice containers (including the custom `phantomql-engine`) using modern base layers to bypass legacy version locks.

---

## 📂 Repository Structure

```
PhantomNet-v4.0/
├── 📡 backend_api/                  # FastAPI python microservices grid (ports 8000–8025)
├── 🌐 phantomnet-website/           # Next.js 16 marketing site, Admin Portal & User Shield
├── 🖥️  dashboard_frontend/           # React 18 + Vite live SOC threat graph dashboard
├── 🔗 blockchain_layer/             # Immutable blockchain ledger audit trail client
├── 🕵️  phantomnet_agent/             # Cross-platform telemetry & response endpoint agent
├── 📝 task.md                       # Core development track and task checklists
└── 🧪 tests/                        # 100% verified unit and integration test suites
```

---

## 🚪 Quick Start (Development)

The complete deployment instructions including databases, API gateways, and user dashboard setups are structured in the [Deploy.md](Deploy.md) guide.

### Option A: Optimized Local-Hybrid Setup (Recommended)
```bash
# 1. Start postgres, redis, redpanda, and neo4j in Docker
DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" docker compose up -d postgres redis redpanda neo4j

# 2. Start the unified FastAPI Backend Core
source .venv_phantomnet/bin/activate
DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" REDIS_HOST="localhost" KAFKA_BOOTSTRAP_SERVERS="localhost:9092" python main.py

# 3. Start the User Dashboard Console (Vite)
cd dashboard_frontend && npm run dev -- --port 3000 --host 0.0.0.0
```

### Option B: Fully Containerized Dev Stack (Docker Only)
```bash
# 1. Start all 28 microservices + databases in Docker
DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" docker compose up -d

# 2. Start the User Dashboard Console (Vite)
cd dashboard_frontend && npm run dev -- --port 3000 --host 0.0.0.0
```

---

## 🛸 Agent Installation

The cross-platform agent compiles cleanly and runs across multiple host architectures:

### 1. Windows Installation
1. Open PowerShell as Administrator.
2. Navigate to root and run: `./install_windows.ps1`
3. The script will initialize a local Python virtual environment, install requirements from `requirements-windows.txt`, register the agent as a Windows Service, and configure firewall rules.

### 2. Linux Installation
1. Open a terminal.
2. Execute with root privileges: `sudo bash ./install_linux.sh`
3. This installs native system prerequisites, sets up the virtual environment, and enables a `systemd` service (`phantomnet-agent.service`).
   * Start: `sudo systemctl start phantomnet-agent.service`
   * Status: `sudo systemctl status phantomnet-agent.service`

### 3. Termux Installation (Android aarch64)
1. Open Termux on your Android device.
2. Execute: `bash ./install_termux.sh`
3. Installs requirements and compiles the startup helper (`~/bin/start-phantomnet-agent.sh`).

---

## 🛡️ Security Practices

* JWT validation relies on secure keys managed in environment settings (`JWT_SECRET_KEY`).
* All sensitive network metrics and agent operations require validated token authorization.
* Inter-service transactions use credentials audited cryptographically by the local blockchain ledger.

---

## 📖 Operational Documentation

* **[Production Runbook](docs/runbook.md):** System monitoring, database scaling, backup and recovery operations, and incident response procedures.
* **[API Reference](docs/api-reference.md):** Complete developer REST API specifications for authentication, agents, SOAR execution, and forensics triggers.
* **[Deploy.md Reference](Deploy.md):** Full setup guide, operational cheat sheets, and active testing targets.


## Why PhantomNet?

PhantomNet is a research and engineering platform for defensive security validation, breach-and-attack simulation, telemetry collection, automated response, and auditability. It is most useful to security engineers, detection-and-response researchers, and developers building controlled SOC automation experiments.

## Start with a Safe Local Check

For a lightweight dependency and import check, use the repository’s Python environment and run:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

Full deployments require the services described in [`Deploy.md`](Deploy.md). Use isolated test networks and synthetic data; do not point simulations at systems you do not own or have explicit permission to test.

## Contributing

Contributions are welcome in detection rules, safe-mode behavior, test coverage, documentation, and platform adapters. Please explain the defensive use case, identify the affected service or feature, include tests, and document any required infrastructure. Stars help other security practitioners find the project, while forks are encouraged for clearly scoped research and lab environments.
