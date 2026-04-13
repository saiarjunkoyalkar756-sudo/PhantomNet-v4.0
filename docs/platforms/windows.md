# Windows Installation Guide

This document provides a comprehensive guide for installing and configuring the PhantomNet Agent and Backend on Windows 10/11 (x64) systems.

## 1. Prerequisites

*   **Operating System:** Windows 10/11 (64-bit).
*   **Privileges:** Administrator privileges are required for installation and service management.
*   **Internet Connectivity:** Required for downloading packages and dependencies.
*   **Python:** Python 3.11 (64-bit) installed and added to your system's PATH.
    *   **Note:** The installer *does not* automatically install Python. You must install it manually from [python.org](https://www.python.org/downloads/windows/). Ensure "Add Python to PATH" is selected during installation.
*   **Windows Defender/Antivirus:** Temporarily disable or add exceptions for PhantomNet installation directories to prevent interference during setup.

## 2. Installation Steps

### Step 2.1: Clone the PhantomNet Repository

Open PowerShell as Administrator and clone the repository:

```powershell
# Open PowerShell as Administrator
git clone https://github.com/PhantomNet/PhantomNet.git
cd PhantomNet
```
*(Replace `https://github.com/PhantomNet/PhantomNet.git` with the actual repository URL if different.)*

### Step 2.2: Run the Unified Windows Installer

The `install_windows.ps1` script automates the setup of Python virtual environments, installs Python dependencies, and configures Windows Services using `sc.exe`.

```powershell
# In the same Administrator PowerShell window
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force # Allow script execution
.\install_windows.ps1
```

The installer performs the following actions:
*   **Npcap Installation:** Attempts to download and silently install Npcap (required for Scapy's packet capture). You may need to manually confirm installation or restart your system if prompted.
*   **Python Virtual Environment Setup:** Creates a virtual environment named `.venv_phantomnet` in the project root.
*   **Python Dependency Installation:** Installs all Python libraries listed in `requirements-windows.txt` into the virtual environment. This includes `pywin32`, `wmi`, `scapy`, and `yara-python`.
*   **Windows Service Registration:** Registers `PhantomNetAgent` and `PhantomNetBackend` as Windows Services, configured to start automatically on system boot.

## 3. Managing PhantomNet Services

Use the provided PowerShell scripts `Start-PhantomNet.ps1` and `Stop-PhantomNet.ps1` to manage the services.

*   **Start All Services:**
    ```powershell
    .\Start-PhantomNet.ps1
    ```
*   **Stop All Services:**
    ```powershell
    .\Stop-PhantomNet.ps1
    ```
*   **Start Individual Service (e.g., Agent):**
    ```powershell
    Start-Service PhantomNetAgent
    ```
*   **Stop Individual Service (e.g., Backend):**
    ```powershell
    Stop-Service PhantomNetBackend
    ```
*   **Check Status of Services:**
    ```powershell
    Get-Service PhantomNetAgent
    Get-Service PhantomNetBackend
    ```
*   **View Agent Logs:**
    Agent logs are located at `phantomnet_agent\logs\phantomnet_agent_service_wrapper.log`.
*   **View Backend Logs:**
    Backend logs are located at `backend_api\logs\phantomnet_backend_service_wrapper.log`.

## 4. Verification

After starting the backend service, you can check its health endpoint using PowerShell:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```
This should return a JSON response indicating the backend's health status.

## 5. Troubleshooting

*   **Python Not Found / Incorrect Version:**
    *   **Issue:** The installer script cannot find Python or detects an incompatible version.
    *   **Solution:** Manually install Python 3.11 (64-bit) from [python.org](https://www.python.org/downloads/windows/) and ensure it's added to your system's PATH.
*   **Npcap Installation Issues:**
    *   **Issue:** Npcap silent installation failed or Scapy cannot capture packets.
    *   **Solution:** Download and install Npcap manually from [npcap.com](https://npcap.com/). Ensure you select "Install Npcap in WinPcap API-compatible Mode" during installation. Scapy requires Npcap to function.
*   **Service Startup Failures:**
    *   **Issue:** PhantomNet services fail to start.
    *   **Solution:** Check the service wrapper logs (`phantomnet_agent\logs\phantomnet_agent_service_wrapper.log` and `backend_api\logs\phantomnet_backend_service_wrapper.log`) for detailed error messages. Ensure all Python dependencies were installed correctly.
*   **TensorFlow/ML Libs Failures:**
    *   **Issue:** Some complex ML libraries may have specific hardware or Python version requirements not met.
    *   **Solution:** PhantomNet's AI components are designed with graceful fallbacks. If a full TensorFlow installation fails, the `ml_adapter.py` will automatically switch to a lighter `tflite` model (if available) or a simulated heuristic mode (`SAFE_MODE`). Check service wrapper logs for messages indicating AI mode.
*   **PostgreSQL/Redis/Kafka Connection Issues:**
    *   **Issue:** Backend microservices might fail to connect to their respective databases or message brokers.
    *   **Solution:** Ensure these services are running and accessible on your network. If running them locally in Docker, verify your Docker setup.

## 6. Security Guidance

*   **Secrets Management:** Never store sensitive information (API keys, database passwords) directly in configuration files within the repository. Use environment variables (e.g., set via PowerShell `$env:VARIABLE_NAME = "value"`) or secure vaults.
*   **Production Deployment:**
    *   **HTTPS:** Always deploy the backend with HTTPS enabled using a reverse proxy (e.g., IIS with ARR, Nginx, Caddy).
    *   **Firewall Rules:** Configure Windows Firewall to restrict access to PhantomNet's backend ports (e.g., 8000 for FastAPI) only from trusted sources.
    *   **Dedicated Service Accounts:** For enhanced security, configure the Windows Services to run under dedicated, unprivileged service accounts with the minimum necessary permissions instead of `LocalSystem`. This often requires creating specific group policies or local user accounts.
    *   **Database Security:** Secure your PostgreSQL, Redis, and Neo4j instances with strong passwords and network access controls.

## 7. Feature Gating & Fallbacks

The PhantomNet Agent is designed to be resilient. Upon startup, it detects the OS and its capabilities. Features that are not supported or for which dependencies cannot be met will be automatically disabled or switch to a `SAFE_MODE` with graceful fallbacks (e.g., passive monitoring instead of active packet capture, heuristic AI instead of full ML models). This ensures continuous operation with reduced functionality rather than outright failure.
