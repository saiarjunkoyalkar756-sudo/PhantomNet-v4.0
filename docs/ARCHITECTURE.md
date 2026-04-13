# PhantomNet Architecture

This document provides a high-level overview of the PhantomNet platform architecture.

## Repository Structure

PhantomNet-v2.0/
│
├── backend_api/                # Python microservices
│   ├── analyzer/
│   ├── api_gateway/
│   ├── collector/
│   ├── blockchain_service/
│   └── report_service.py
│
├── blockchain_layer/           # Blockchain client + chain logic
│
├── dashboard_frontend/         # React + Tailwind dashboard
│   ├── src/
│   └── public/
│
├── features/                   # Advanced AI/cyber modules
│   ├── ai_autonomy_levels/
│   ├── ai_threat_marketplace/
│   ├── phantom_os/
│   └── self_evolving_threat_brain/
│
├── docs/                       # User and marketing docs
│
├── microservices/              # Additional distributed components
│
├── run_all.py                  # Starter script for manual execution
│
├── .env.example                # Template env vars
├── docker-compose.yml          # Deployment stack
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md


## System Architecture

PhantomNet is built on a distributed microservice model orchestrated through a message bus and secured via blockchain-based logging.

                               +-------------------------+
                               |                         |
                               |      React Dashboard    |
                               | (SOC + Admin Console)   |
                               |                         |
                               +-----------+-------------+
                                           |
                                           | REST / WebSocket
                                           |
                         +-----------------v-----------------+
                         |                                   |
                         |           API Gateway             |
                         |      (FastAPI, Authentication)    |
                         |                                   |
                         +--+--------------+--------------+--+
                            |              |              |
      +---------------------+              |              +---------------------+
      |                                    |                                    |
+-----v-----+                      +-------v-------+                      +-----v-----+
|           |                      |               |                      |           |
| Collector |                      |   Analyzer    |                      | Orchestrator|
| (Ingest)  |                      | (Neural Brain)|                      | (Control) |
|           |                      |               |                      |           |
+-----+-----+                      +-------+-------+                      +-----+-----+
      |                                    |                                    |
      |                                    |                                    |
      +---------------------+--------------+------------------------------------+
                            |
                            |
                 +----------v----------+
                 |                     |
                 |     Message Bus     |
                 | (Redis/RabbitMQ/Kafka)|
                 |                     |
                 +----------+----------+
                            |
                            |
      +---------------------+---------------------+
      |                                           |
+-----v-----------+                       +-------v--------+
|                 |                       |                |
|  Report Service |                       |Blockchain Service|
| (Logging)       |                       | (Audit Trail)  |
|                 |                       |                |
+-----------------+                       +----------------+

---

## Overview

PhantomNet is a microservices-based, autonomous cyber defense platform. It consists of three main components:

1.  **PhantomNet Agent:** A lightweight agent that runs on endpoints (Windows, Linux, Termux) to collect telemetry, execute response actions, and perform local analysis.
2.  **PhantomNet Backend:** A collection of microservices that provide the core logic for data ingestion, analysis, storage, and orchestration.
3.  **PhantomNet Dashboard:** A web-based user interface for interacting with the platform.

## Features

*   **Neural Threat Brain**: ML-based threat classification, adaptive defense behavior, cognitive reasoning patterns, synthetic behavioral modeling.
*   **Distributed Microservices**: Collector (ingest agent), Analyzer (AI/ML brain), API Gateway, Report service, Security utilities, Orchestrator controls.
*   **Blockchain Audit Layer**: Immutable logs, federated data trails, tamper-resistant event storage.
*   **Full React Dashboard**: Real-time attack map, health monitoring, admin console, SOC interface, security insights with charts.
*   **Security Enhancements**: JWT auth, 2FA, CRL validation, secure message bus.

## Backend Architecture

The PhantomNet backend is designed as a set of containerized microservices that communicate via a message bus (Kafka or Redis) and REST APIs. The main services include:

-   **Gateway Service:** The main entry point for the backend, which routes requests to the appropriate microservices.
-   **SOAR Playbook Engine:** Manages and executes SOAR playbooks.
-   **Playbook Flow Builder:** Provides logic for building and managing playbook flows.
-   **Auto Response Engine:** Executes automated response actions.
-   **Vulnerability Management Service:** Manages asset inventory and vulnerability data.
-   **SIEM Ingest Service:** Ingests raw log data from various sources.
-   **Log Normalizer:** Normalizes raw logs into a common schema.
-   **PhantomQL Engine:** Provides query and analytics capabilities for the SIEM.
-   **SOC AI Copilot:** Provides AI-powered assistance to SOC analysts.
-   **Attack Graph Engine:** Builds and maintains a real-time attack graph.
-   **Lateral Movement Detector:** Detects lateral movement attempts.
-   **Forensics Engine:** Orchestrates automated forensic data collection and analysis.
-   **Compliance Service:** Manages compliance assessments and findings.
-   **Audit Log Collector:** Collects and stores audit logs.

## Agent Architecture

The PhantomNet agent is a modular application that consists of:

-   **Collectors:** Responsible for gathering telemetry from the host (e.g., process creation, file access, network connections, software inventory).
-   **Actions:** Responsible for executing response actions on the host (e.g., kill process, quarantine file, block IP).
-   **Orchestrator:** The central component of the agent that manages collectors and actions.
-   **Transport:** The component responsible for communicating with the backend.

## Data Flow

1.  **Telemetry Collection:** The agent's collectors gather telemetry from the host and send it to the backend via the configured transport (HTTP, Redis, or Kafka).
2.  **Ingestion and Normalization:** The `siem_ingest_service` receives the raw telemetry and stores it. The `log_normalizer` then processes the raw data, normalizes it into a common schema, and stores it in the `phantomql_engine`'s database.
3.  **Analysis and Detection:** The `lateral_movement_detector`, `ai_behavioral_engine`, and other analysis services process the normalized data to detect threats.
4.  **Alerting:** When a threat is detected, an alert is generated and stored in the `alert_storage` service.
5.  **Response:** The `soar_playbook_engine` can be triggered to execute a playbook in response to an alert. The `auto_response_engine` then executes the response actions, which may involve sending commands to the agent.
6.  **Visualization:** The `dashboard_frontend` provides a user interface for viewing alerts, dashboards, and interacting with the platform's various features.