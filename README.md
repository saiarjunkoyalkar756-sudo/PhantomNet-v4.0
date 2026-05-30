# 🌌 PhantomNet v4.0 — Autonomous SOC & XDR Platform

[![Release v4.0](https://img.shields.io/badge/release-v4.0-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-%233776AB.svg)]()
[![Node](https://img.shields.io/badge/node-18-%234CC61E.svg)]()
[![Build Status](https://img.shields.io/github/actions/workflow/status/saiarjunkoyalkar756-sudo/PhantomNet-v4.0/ci.yml?branch=main)]()

![PhantomNet Image](docs/images/file_000000004544720988d35dea5d77e630.png)

---

PhantomNet v4.0 is a production-grade, distributed autonomous cyber defense and XDR operations grid. It automates high-speed threat ingestion, correlates security events with a custom query AST compiler, logs integrity audits onto an immutable blockchain ledger, and deploys cross-platform telemetry endpoint agents.

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

### 1. Backend Microservices Stack
Configure your secrets template inside `.env`:
```bash
cp .env.example .env
docker compose up -d --build
```

### 2. Next.js Marketing & Portals
Navigate to the web portal directory, install packages, and spin up the hot-reload Turbopack compiler:
```bash
cd phantomnet-website
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to browse the marketing pages or go to `/admin` and `/user` to access the dashboards.

### 3. Run Test Suite
Provide your credentials and execute unit/integration test suites on the host:
```bash
PYTHONPATH=.:phantomnet_agent JWT_SECRET_KEY=changeme DB_PASSWORD=changeme NEO4J_PASSWORD=changeme pytest tests/
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
