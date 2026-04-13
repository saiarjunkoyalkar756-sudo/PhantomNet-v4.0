# Linux Installation Guide

This document provides a comprehensive guide for installing and configuring the PhantomNet Agent and Backend on Linux distributions such as Ubuntu, Debian, Kali, Fedora, and Arch.

## 1. Prerequisites

*   **Operating System:** Ubuntu 20.04+, Debian 10+, Kali Linux, Fedora 36+, Arch Linux.
*   **Privileges:** `sudo` access is required for installing system packages and managing services.
*   **Internet Connectivity:** Required for downloading packages and dependencies.
*   **Python:** Python 3.11 or newer is recommended.
*   **Git:** Installed for cloning the PhantomNet repository.

## 2. Installation Steps

### Step 2.1: Clone the PhantomNet Repository

Open a terminal and clone the repository:

```bash
git clone https://github.com/PhantomNet/PhantomNet.git
cd PhantomNet
```
*(Replace `https://github.com/PhantomNet/PhantomNet.git` with the actual repository URL if different.)*

### Step 2.2: Run the Unified Linux Installer

The `install_linux.sh` script will automate the setup of Python virtual environments, install Python dependencies, and configure systemd services.

```bash
chmod +x install_linux.sh
sudo ./install_linux.sh
```

The installer performs the following actions:
*   **System Package Installation:** Detects your package manager (`apt`, `dnf`, `pacman`) and installs essential build tools, Python development headers, `libpcap-dev` (for network sniffing), `clang`, `llvm` (for eBPF compilation), `nmap` (for network scanning), and PostgreSQL client libraries.
*   **Python Virtual Environment Setup:** Creates a virtual environment named `.venv_phantomnet` in the project root.
*   **Python Dependency Installation:** Installs all Python libraries listed in `requirements-linux.txt` into the virtual environment. This includes `scapy`, `bcc` (eBPF tools), and `yara-python`.
*   **Systemd Service Creation:** Installs `phantomnet-backend.service` and `phantomnet-agent.service` into `/etc/systemd/system/` and enables them for automatic startup on boot.
*   **CLI Shim Installation:** Installs the `phantomnet-cli` script to `/usr/local/bin` for easy management of services.

## 3. Managing PhantomNet Services

Use the `phantomnet-cli` shim to manage the backend and agent services.

*   **Start Backend:**
    ```bash
    sudo phantomnet-cli start backend
    ```
*   **Start Agent:**
    ```bash
    sudo phantomnet-cli start agent
    ```
*   **Stop Backend:**
    ```bash
    sudo phantomnet-cli stop backend
    ```
*   **Stop Agent:**
    ```bash
    sudo phantomnet-cli stop agent
    ```
*   **Restart Backend/Agent:**
    ```bash
    sudo phantomnet-cli restart backend
    sudo phantomnet-cli restart agent
    ```
*   **Check Status:**
    ```bash
    sudo phantomnet-cli status backend
    sudo phantomnet-cli status agent
    ```
*   **View Logs (Backend):**
    ```bash
    journalctl -u phantomnet-backend.service -f
    ```
*   **View Logs (Agent):**
    ```bash
    journalctl -u phantomnet-agent.service -f
    ```

## 4. Verification

After starting the backend, you can check its health endpoint:

```bash
curl http://localhost:8000/health
```
This should return a JSON response indicating the backend's health status.

## 5. Troubleshooting

*   **`PermissionError` with Scapy/Network Sensors:**
    *   **Issue:** Scapy requires raw socket access, which typically needs root privileges or specific capabilities.
    *   **Solution 1 (Recommended for Agent):** Ensure the agent service is running as `root` (the installer configures it this way).
    *   **Solution 2 (Advanced):** Grant `CAP_NET_RAW` capability to the Python executable within the virtual environment. **Caution:** This is generally less secure than running as root for a security agent, as it makes the Python executable itself privileged.
        ```bash
        sudo setcap cap_net_raw+ep /path/to/PhantomNet/.venv_phantomnet/bin/python
        ```
*   **eBPF Monitor Initialization Errors:**
    *   **Issue:** `bcc` (eBPF tools) require matching Linux kernel headers and specific build tools.
    *   **Solution:** Ensure `linux-headers-$(uname -r)`, `clang`, `llvm`, and `bpfcc-tools` (or equivalent development packages) are installed. The `install_linux.sh` script attempts to do this.
        ```bash
        sudo apt-get install -y linux-headers-$(uname -r) bpfcc-tools # Debian/Ubuntu
        # or dnf install -y kernel-devel clang llvm bcc # Fedora
        ```
*   **TensorFlow/ML Libs Failures:**
    *   **Issue:** Some complex ML libraries may have specific hardware or Python version requirements not met.
    *   **Solution:** PhantomNet's AI components are designed with graceful fallbacks. If a full TensorFlow installation fails, the `ml_adapter.py` will automatically switch to a lighter `tflite` model (if available) or a simulated heuristic mode (`SAFE_MODE`). Check agent logs for messages indicating AI mode.
*   **PostgreSQL/Redis/Kafka Connection Issues:**
    *   **Issue:** Backend microservices might fail to connect to their respective databases or message brokers.
    *   **Solution:** Ensure your Docker Compose services (PostgreSQL, Redis, Redpanda/Kafka) are running correctly.
        ```bash
        sudo docker compose ps
        ```
        Check container logs for errors.

## 6. Security Guidance

*   **Secrets Management:** Never store sensitive information (API keys, database passwords) directly in configuration files within the repository. Use environment variables (`.env` files) and ensure they are properly secured (e.g., restricted file permissions).
*   **Production Deployment:**
    *   **HTTPS:** Always deploy the backend with HTTPS enabled using a reverse proxy (e.g., Nginx, Caddy) and valid SSL certificates.
    *   **Firewall Rules:** Configure your server's firewall (e.g., `ufw` on Linux) to restrict access to PhantomNet's backend ports (e.g., 8000 for FastAPI) only from trusted sources.
    *   **Dedicated User:** Although the installer uses `sudo`, for production, consider running the agent and backend services under dedicated, unprivileged system users with minimum necessary permissions. Modify the `User=` directive in the systemd unit files accordingly.
    *   **Database Security:** Secure your PostgreSQL, Redis, and Neo4j instances with strong passwords and network access controls.

## 7. Feature Gating & Fallbacks

The PhantomNet Agent is designed to be resilient. Upon startup, it detects the OS and its capabilities (e.g., eBPF support, raw socket availability, root privileges). Features that are not supported or for which dependencies cannot be met will be automatically disabled or switch to a `SAFE_MODE` with graceful fallbacks (e.g., passive monitoring instead of active packet capture, heuristic AI instead of full ML models). This ensures continuous operation with reduced functionality rather than outright failure.
