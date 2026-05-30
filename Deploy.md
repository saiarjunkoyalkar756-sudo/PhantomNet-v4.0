# PhantomNet v4.0 — Deployment & Setup Guide

This guide outlines the systematic procedure to deploy and run **PhantomNet v4.0** (including containerized databases, unified FastAPI backend microservices, Vite dashboard, and validation campaigns).

---

## 1. Prerequisites

Before starting, ensure your host machine has the following tools installed:
* **Docker & Docker Compose** (v2.0 or higher)
* **Python 3.12+** & virtual environment utility (`venv`)
* **Node.js** (v18.0+) & **npm**

---

## 2. Environmental Configuration

The platform reads credentials and service locations from an environment configuration file:

1. Copy the example environment file to create your active `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and verify the passwords and connection strings (defaults are pre-configured for local developer setups):
   * `DB_PASSWORD=changeme`
   * `NEO4J_PASSWORD=super_secret_neo4j_password_random_string_abcde`
   * `REDIS_URL=redis://localhost:6379/0`
   * `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`

---

## 3. Quick Start: Running the Whole Project

There are two recommended methodologies to deploy and run the entire multi-tier stack:

### Option A: Optimized Local-Hybrid Setup (Recommended)
This is the most efficient developer setup. It runs the persistent databases and message queues inside Docker containers (taking 5 seconds to download and boot) and launches the unified backend services grid locally on port `8000` (taking 2 seconds to boot and dynamically mounting all 28 microservices under a single process space).

1. **Start the Infrastructure (Docker):**
   ```bash
   DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" docker compose up -d postgres redis redpanda neo4j
   ```
2. **Start the Backend Services Grid (Python):**
   ```bash
   source .venv_phantomnet/bin/activate
   DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" REDIS_HOST="localhost" KAFKA_BOOTSTRAP_SERVERS="localhost:9092" python main.py
   ```
3. **Start the User Dashboard Console (Vite):**
   ```bash
   cd dashboard_frontend && npm run dev -- --port 3000 --host 0.0.0.0
   ```

### Option B: Fully Containerized Dev Stack (Docker Only)
This runs the databases, queue brokers, and all modular backend services completely inside containerized environments via Docker Compose.

1. **Build and start the entire multi-container stack in the background:**
   ```bash
   # Starts databases, redpanda, and all 28 FastAPI microservices
   DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" docker compose up -d
   ```
2. **Start the User Dashboard Console (Vite):**
   ```bash
   cd dashboard_frontend && npm run dev -- --port 3000 --host 0.0.0.0
   ```

---

## 4. Run Threat Stress Validation Campaigns

Once the three core deployment steps are active, validate the end-to-end telemetry pipelines and defensive response logic by launching the automated threat scripts:

### A. Run gradated 3-Phase Campaign
```bash
./simulate_attacks.sh
```
*Triggers SQL Injection (Low) $\rightarrow$ Ransomware mimic with automated SOAR EDR process kill (Medium) $\rightarrow$ automated Volatility memory forensics capture (Advanced).*

### B. Run 100-Campaign Stress Test
```bash
python simulate_load_attacks.py
```
*Floods the API gateways with 100 concurrent asynchronous threats to verify message broker offsets under load.*

### C. Run 130-Scenario MITRE ATT&CK Matrix Suite
```bash
python simulate_comprehensive_attacks.py
```
*Spawns 130 distinct threat scenarios across 11 advanced categories (AD Golden Tickets, supply chain bypasses, logical IAM compromises) mapped to MITRE ATT&CK patterns to test platform categorization resilience.*

---

## 5. Port Mappings & Reference Directory

| Service / Port | Connection Protocol | Purpose |
| :--- | :--- | :--- |
| **Vite Dashboard** (Port `3000`) | HTTP | Main Web UI dashboard console |
| **FastAPI Core Gateway** (Port `8000`) | HTTP / WS | Mounted backend services router (`/docs` available) |
| **PostgreSQL** (Port `5432`) | `postgresql://` | Persistent SQL database tracking logs and SOAR runs |
| **Redis Cache** (Port `6379`) | `redis://` | High-speed cache for dynamic IP rate limiting bans |
| **Redpanda** (Port `9092`) | TCP / PLAINTEXT | Ingestion telemetry event stream message bus |
| **Neo4j DB** (Port `7687` / `7474`) | Bolt / HTTP | Graph database charting credential and network attack paths |

---

## 6. Logs & Diagnostics

All real-time actions and defensive counter-measure logs are written under the local `logs/` directory:
* `logs/attack_simulation.log`: Real-time entries documenting simulated threat scores and blocker decisions.
* `logs/soar_execution.log`: Automated active defense actions (firewall blocks, process terminations, host isolation).
* `logs/forensics_vault.log`: Preserved forensics memory dumps and zip file collections.
* `logs/comprehensive_test_results.json`: JSON output of all completed validation runs.

---

## 7. Operational & Diagnostic Commands (Cheat Sheet)

Use these standard commands to manage the state of the active deployment:

### A. Managing Container States
```bash
# Check status of running databases/message broker containers
docker compose ps

# View real-time aggregated logs of the database stack
docker compose logs -f

# Stop and remove database containers, preserving volumes
docker compose down

# Stop and wipe database containers AND all active data volumes (Dangerous!)
docker compose down -v
```

### B. Testing and Verification Targets
```bash
# Run all backend and agent unit test suites with coverage report
.venv_phantomnet/bin/python -m pytest tests/

# Run specific EDR agent test suite
.venv_phantomnet/bin/python -m pytest phantomnet_agent/tests/ -v

# Run threat playbook syntax checks
make test-playbooks
```

### C. Git and Code Synchronization
```bash
# Verify modified and untracked validation scripts
git status

# Stage changes for deployment guide and test modules
git add Deploy.md simulate_comprehensive_attacks.py simulate_load_attacks.py

# Commit staged scripts with descriptive message
git commit -m "docs: Add Deploy.md and comprehensive simulation testing scripts"

# Push the committed changes to your main branch on GitHub
git push origin main

---

## 8. Frontend Deployment via Vercel

The User Dashboard Console can be easily deployed to Vercel for hosting and collaboration.

### A. Prerequisites
Verify that the Vercel CLI is installed globally:
```bash
vercel --version
```

### B. Deploying to Vercel
To link and deploy the frontend dashboard to Vercel, navigate to the `dashboard_frontend` directory and invoke Vercel CLI commands:

```bash
# Navigate to the frontend directory
cd dashboard_frontend

# Log in to your Vercel Account
vercel login

# Initialize/Link and deploy the project to a preview environment
vercel

# Deploy the project to production
vercel --prod
```

```
