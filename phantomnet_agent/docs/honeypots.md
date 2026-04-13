# Honeypot Subsystem (MVP)

## Overview
This document outlines the initial MVP (Minimum Viable Product) for the PhantomNet Honeypot subsystem. The goal of this phase is to establish a foundational, low-interaction honeypot service capable of capturing basic attack telemetry.

## Architecture (MVP)
The honeypot subsystem consists of:
- **Honeypot Service (FastAPI):** A backend service (`backend_api/honeypot_service`) providing RESTful endpoints to manage honeypot lifecycles (start, stop, list).
- **Honeypot Manager:** Manages the instantiation and termination of honeypot instances.
- **Honeypot Implementations:** Low-interaction honeypots (e.g., `honeypots/ssh_honeypot.py`) that emulate services and capture interaction data.
- **Event Forwarder:** A component (`backend_api/honeypot_service/forwarder.py`) responsible for normalizing captured events into a standard JSON format and "forwarding" them (currently prints to console, will integrate with message bus/telemetry ingest later).

## MVP Features
- **Low-interaction SSH Honeypot:** Emulates an SSH server to capture connection attempts and credentials.
- **API for Lifecycle Management:**
    - `POST /honeypots`: Create and start a new honeypot instance.
    - `GET /honeypots`: List all active honeypot instances.
    - `POST /honeypots/{id}/stop`: Stop a running honeypot instance.
    - `GET /honeypots/{id}/events`: Placeholder for streaming/paginating captured events (currently returns empty).
- **Event Capture:** Captured interactions (e.g., SSH login attempts) are formatted as JSON events and forwarded.

## Usage (Local Development)

### Prerequisites
- Python 3.12
- `uvicorn`
- `paramiko`
- `fastapi`

### Quick Start
1.  **Start the services and a default SSH honeypot:**
    ```bash
    bash scripts/honeypot_start.sh
    ```
    This script will:
    - Start the `gateway_service` (if not already running).
    - Start the `honeypot_service` on `http://localhost:8100`.
    - Create a default low-interaction SSH honeypot (`honeypot_id: "default_ssh_honeypot"`) listening on `127.0.0.1:2222`.

2.  **Simulate an attack (in a new terminal):**
    ```bash
    ssh -p 2222 attacker@127.0.0.1
    ```
    You will see login attempt events printed to the console where `honeypot_service` is running.

3.  **Check honeypot status (in a new terminal):**
    ```bash
    curl -s http://localhost:8100/honeypots | jq .
    ```

4.  **Check honeypot events (currently returns empty):**
    ```bash
    curl -s http://localhost:8100/honeypots/default_ssh_honeypot/events | jq .
    ```

5.  **Stop the honeypot:**
    ```bash
    curl -X POST http://localhost:8100/honeypots/default_ssh_honeypot/stop
    ```

6.  **Stop all services:**
    Note the PIDs printed by `honeypot_start.sh` and run:
    ```bash
    kill <GATEWAY_PID> <HONEYPOT_SERVICE_PID>
    ```

## Safety Notes
- **Local-only Binding:** By default, honeypots bind to `127.0.0.1`. Do not modify this to `0.0.0.0` or a public IP address without explicit understanding of the security implications.
- **Low-Interaction:** This MVP focuses on low-interaction honeypots, which pose minimal risk. High-interaction honeypots are more complex and require advanced isolation and security measures.
- **No Persistence:** Currently, honeypot configurations and events are stored in-memory. Restarting the service will clear all data.
- **No Evidence Vault Integration:** Evidence (e.g., captured files) is not yet stored in the `evidence_vault`.

## Next Steps
- Integrate with `telemetry_ingest` and message bus for persistent event storage.
- Implement UI for honeypot management and event visualization.
- Develop proper database persistence for honeypot configurations.
