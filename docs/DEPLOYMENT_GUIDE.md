# PhantomNet Deployment Guide

This document provides comprehensive instructions for deploying the PhantomNet backend and agent, covering various environments and scenarios.

## Quick Start (Development)

This section outlines the basic steps to get the PhantomNet development environment up and running.

1.  **Clone the repository**
    ```bash
    git clone git@github.com:saiarjunkoyalkar756-sudo/PhantomNet-v2.0.git
    cd PhantomNet-v2.0
    ```

### Backend Setup

To set up and run the backend microservices for development:

1.  **Create a virtual environment**
    ```bash
    cd backend_api
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Run backend tests**
    ```bash
    pytest -q
    ```

### Frontend Setup

To set up and run the React/Tailwind dashboard for development:

1.  **Navigate to frontend directory**
    ```bash
    cd dashboard_frontend
    ```
2.  **Install Node.js dependencies**
    ```bash
    npm install
    ```
3.  **Start the frontend development server**
    ```bash
    npm start
    ```
    The dashboard typically runs on: `http://localhost:3000`

## Full Stack Deployment with Docker Compose

The recommended way to deploy the entire PhantomNet platform (backend, frontend, database, message bus, etc.) is using Docker Compose.

### Prerequisites
-   Docker
-   Docker Compose

### Installation Steps

1.  **Copy environment template**
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file to configure your database passwords, API keys, and other settings.

2.  **Start the platform**
    ```bash
    docker-compose up --build
    ```

### Services Overview (Docker Compose)
-   **Frontend**: Accessible at `http://localhost:3000`
-   **API Gateway**: Accessible at `http://localhost:8000`
-   **Blockchain Node**: (Local instance)
-   **Message Bus**: (Redis + Postgres)

## Agent Deployment

The PhantomNet Agent can be installed on Windows, mainstream Linux distributions, and Termux (Android aarch64). This section details the deployment process for each platform.

### Windows Agent Installation
*   **Prerequisites**:
    *   Windows 10/11 (64-bit)
    *   Python 3.11 (manual installation from python.org is required)
    *   Visual C++ Redistributable (latest version recommended)
    *   Administrator privileges to run the installer.
*   **Installation Steps**:
    1.  Download the `install_windows.ps1` script from the repository.
    2.  Open PowerShell as Administrator.
    3.  Navigate to the directory containing the script.
    4.  Execute: `./install_windows.ps1`
    5.  The script will:
        *   Check for Python 3.11 and the Visual C++ Redistributable.
        *   Install Npcap (required for network monitoring).
        *   Set up a Python virtual environment and install dependencies from `requirements-windows.txt`.
        *   Register the agent as a Windows Service.
        *   Configure basic Windows Firewall rules.
*   **Usage**:
    *   Start Service: `Start-Service PhantomNetAgent`
    *   Stop Service: `Stop-Service PhantomNetAgent`
    *   Logs: `phantomnet_agent\logs\phantomnet_agent_service_stdout.log`

### Linux Agent Installation
*   **Prerequisites**:
    *   Mainstream Linux Distribution (Debian, Ubuntu, CentOS, Fedora, Arch)
    *   Python 3.11 (usually available via package manager)
    *   Root privileges (`sudo`) to run the installer.
*   **Installation Steps**:
    1.  Download the `install_linux.sh` script from the repository.
    2.  Open a terminal.
    3.  Navigate to the directory containing the script.
    4.  Execute: `sudo bash ./install_linux.sh`
    5.  The script will:
        *   Install system prerequisites (python3-venv, dev headers, clang, llvm, etc.).
        *   Set up a Python virtual environment and install dependencies from `requirements-linux.txt`.
        *   Create and enable a `systemd` unit file (`phantomnet-agent.service`).
*   **Usage**:
    *   Start Service: `sudo systemctl start phantomnet-agent.service`
    *   Stop Service: `sudo systemctl stop phantomnet-agent.service`
    *   Status: `sudo systemctl status phantomnet-agent.service`
    *   Logs: `sudo journalctl -u phantomnet-agent.service`

### Termux Agent Installation (Android aarch64)
*   **Prerequisites**:
    *   Termux app installed on Android (aarch64 device recommended).
    *   Internet connection.
*   **Installation Steps**:
    1.  Open Termux.
    2.  Download the `install_termux.sh` script from the repository.
    3.  Navigate to the directory containing the script.
    4.  Execute: `bash ./install_termux.sh`
    5.  The script will:
        *   Update Termux packages and install prerequisites (python, clang, git, openssl, etc.).
        *   Set up a Python virtual environment and install dependencies from `requirements-termux.txt`.
        *   Create a helper script (`~/bin/start-phantomnet-agent.sh`) to run the agent in the background.
*   **Usage**:
    *   Start Agent: `~/bin/start-phantomnet-agent.sh`
    *   Stop Agent: `kill $(cat phantomnet_agent/agent.pid)`
    *   Autostart: Copy/link `~/bin/start-phantomnet-agent.sh` to `~/.termux/boot/`
    *   Logs: `phantomnet_agent/logs/<agent_id>_stdout.log`
*   **Caveats**:
    *   Raw socket operations (e.g., Scapy) and some advanced features may require root access or special Android permissions.
    *   eBPF is generally not supported on Termux/Android.

## Deployment Options
PhantomNet offers flexible deployment:

*   **Option 1 — Docker Compose**:
    As detailed above, this is the quickest way to get the full stack running.

*   **Option 2 — Kubernetes / Helm**:
    (Planned for v2.1)

---
