# PhantomNet Honeypot Subsystem

## Overview
The PhantomNet Honeypot Subsystem is designed to deploy and manage decoy systems (honeypots) to attract and observe attackers. It collects attacker telemetry, enriches events, generates alerts, and integrates with the broader PhantomNet platform for threat intelligence and SOAR (Security Orchestration, Automation, and Response) playbooks.

This document outlines the current state of the MVP (Minimum Viable Product) implementation.

## Features (MVP)

### Honeypot Management Service
A FastAPI-based microservice (`backend_api/honeypot_service`) for:
*   **Honeypot Lifecycle Management:** Start, stop, and list honeypot instances via RESTful API endpoints.
*   **Prometheus Metrics:** Exposes `/metrics` endpoint for operational monitoring (active instances, sessions, events, errors).
*   **OpenAPI Documentation:** Self-generating API documentation available at `/docs` (Swagger UI) and `/openapi.json`.

### Event Pipeline & Enrichment
*   **Event Normalization:** Raw honeypot events are converted into a standardized platform schema.
*   **Event Enrichment:** Normalized events are enriched with additional context such as:
    *   Reverse DNS lookups.
    *   Geolocation (placeholder).
    *   Passive DNS lookups (placeholder).
    *   Threat Intelligence lookups (placeholder).
*   **Alert Generation:** Based on enriched events, security alerts (e.g., SSH authentication attempts) are generated, designed to trigger SOAR playbooks.

### Honeypots
*   **Low-interaction SSH Honeypot:** An `asyncio`-based SSH honeypot (`honeypots/ssh_honeypot.py`) that emulates an SSH server, captures connection attempts and credentials, and forwards them for processing.

### Testing
*   **Unit Tests:** For individual components of the honeypot service.
*   **Integration Tests:** Simulate SSH attacks against a deployed honeypot and assert event capture, normalization, enrichment, and metric updates.

## Architecture (High-Level)
```
[ Attacker ]
     |
     v
[ Honeypot Instance (e.g., SSH Honeypot) ]
     | (Events via `forward_event` function)
     v
[ Honeypot Service (FastAPI) ]
  - Lifecycle Manager
  - Event Normalizer
  - Event Enricher
  - Alert Generator
  - Prometheus Metrics
     |
     v
[ Message Bus / Telemetry Ingest (Future Integration) ]
     |
     v
[ PhantomNet Platform (Threat Intel, SOAR, UI) ]
```

## Setup (Local Development)

### Prerequisites
*   Python 3.12+
*   `pip`
*   `uvicorn`
*   `paramiko`
*   `fastapi`
*   `prometheus_client`
*   `httpx` (for TestClient)

### Install Python Dependencies
From the project root:
```bash
pip install -r requirements.txt
```

## Running Services (Local Development)

### Start Honeypot Service & a Default SSH Honeypot
Navigate to the project root and execute the start script:
```bash
bash scripts/honeypot_start.sh
```
This script will:
*   Start the `gateway_service` (if not already running) on `http://localhost:8000`.
*   Start the `honeypot_service` on `http://localhost:8100`.
*   Create a default low-interaction SSH honeypot (`honeypot_id: "default_ssh_honeypot"`) listening on `127.0.0.1:2222`.

### Verify Services
*   **Honeypot Service API Docs:** Open your browser to `http://localhost:8100/docs`.
*   **Honeypot Service Metrics:** Open your browser to `http://localhost:8100/metrics`.

### Simulate an Attack (in a new terminal)
```bash
ssh -p 2222 attacker@127.0.0.1
```
You will see enriched events and potential alerts printed in the console where `honeypot_service` is running.

### API Examples (using `curl`)

#### List all deployed honeypots
```bash
curl -s http://localhost:8100/honeypots | jq .
```

#### Create and start a new honeypot
```bash
curl -X POST http://localhost:8100/honeypots \
     -H "Content-Type: application/json" \
     -d '{
           "honeypot_id": "my_custom_ftp_honeypot",
           "type": "ftp",
           "port": 2121,
           "host": "127.0.0.1",
           "capture_level": "medium",
           "tags": ["dev", "ftp"]
         }' | jq .
```
*(Note: An actual FTP honeypot implementation would be required for this to function beyond registration)*

#### Stop a running honeypot
```bash
curl -X POST http://localhost:8100/honeypots/default_ssh_honeypot/stop | jq .
```

## Docker Usage

### Build the Honeypot Service Image
Navigate to the project root:
```bash
docker build -t phantomnet-honeypot-service -f backend_api/honeypot_service/Dockerfile .
```

### Run the Honeypot Service Container
```bash
docker run -d --name phantomnet-honeypot-service -p 8100:8100 phantomnet-honeypot-service
```
After running, you can interact with the API at `http://localhost:8100`.

### Build a Standalone SSH Honeypot Image
Navigate to the project root:
```bash
docker build -t phantomnet-ssh-honeypot -f docker/ssh-honeypot/Dockerfile .
```

### Run a Standalone SSH Honeypot Container
```bash
docker run -d --name phantomnet-ssh-honeypot -p 2222:2222 phantomnet-ssh-honeypot
```
Simulate an attack against `localhost:2222`. Events will be printed to the container's logs (view with `docker logs phantomnet-ssh-honeypot`).

## Prometheus Metrics
The `honeypot_service` exposes Prometheus metrics at `http://localhost:8100/metrics`. These metrics provide insights into:
*   `honeypot_sessions_total`: Total sessions initiated.
*   `honeypot_events_total`: Total events captured (by type).
*   `honeypot_errors_total`: Total errors encountered (by type).
*   `honeypot_active_instances`: Number of currently active honeypot instances.

## Safety Notes
*   **Network Isolation:** Always run honeypots in isolated network segments (e.g., dedicated VLANs, Docker networks) to prevent them from affecting your production environment.
*   **Binding to `0.0.0.0`:** While Docker containers often bind to `0.0.0.0` internally, ensure proper firewall rules are in place on the host to limit exposure. For local development, prefer `127.0.0.1` unless explicitly needed.
*   **Low-Interaction First:** This MVP focuses on low-interaction honeypots. High-interaction honeypots require significantly more robust sandboxing and security controls.
*   **Data Handling:** Captured events and potential malware samples should be handled with extreme care. Implement strict access controls and retention policies. The current implementation prints events to logs; in a production system, these should go to a secure telemetry pipeline.
*   **Legal & Ethical Considerations:** Be aware of the legal and ethical implications of running honeypots, especially if deployed in publicly accessible environments. Ensure compliance with relevant laws and regulations (e.g., GDPR, CCPA).

## Future Work
*   Persistence for honeypot configurations and events.
*   Robust message bus integration (Kafka/Redis).
*   Advanced event enrichment (e.g., real-time threat intel feeds).
*   SOAR playbook integration.
*   High-interaction honeypot support with secure sandboxing (Docker/K8s).
*   User Interface (UI) for management and visualization.
*   Comprehensive CI/CD pipeline.
