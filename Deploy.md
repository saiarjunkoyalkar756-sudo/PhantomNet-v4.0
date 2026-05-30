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

## 3. Step-by-Step Deployment

Follow these steps to launch the entire multi-tier stack:

### Step 1: Run Persistent Services (Docker Compose)
Spins up containerized instances of the databases, streaming caches, and message queues. Using Docker ensures data storage layers are managed cleanly without polluting the host OS.

```bash
# Build and start PostgreSQL, Redis, Redpanda (Kafka), and Neo4j in the background
DB_PASSWORD="changeme" NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" docker compose up -d postgres redis redpanda neo4j
```

### Step 2: Run Unified Backend Services Grid (API Core)
Rather than compiling 28 separate custom Python containers (which is memory-heavy and takes up to 20 minutes to build), the backend mounts **all 28 microservices dynamically** under a single, highly optimized process on port `8000`.

```bash
# 1. Activate virtual environment
source .venv_phantomnet/bin/activate

# 2. Start the unified FastAPI Gateway
DB_PASSWORD="changeme" \
NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde" \
REDIS_HOST="localhost" \
KAFKA_BOOTSTRAP_SERVERS="localhost:9092" \
python main.py
```
*The gateway will automatically initialize PostgreSQL tables via DDL parsing, establish Redis cache pools, connect to Redpanda topics, and listen on `http://localhost:8000`.*

### Step 3: Run User Dashboard (Vite Frontend)
Launches the interactive dashboard displaying threat events, SOAR mitigations, and MITRE maps.

```bash
# 1. Move to frontend workspace
cd dashboard_frontend

# 2. Start Vite dev server on port 3000
npm run dev -- --port 3000 --host 0.0.0.0
```
*Open `http://localhost:3000` in your web browser to access the management panel.*

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
