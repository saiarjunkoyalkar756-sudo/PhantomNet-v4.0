[![Release v2.0](https://img.shields.io/badge/release-v2.0-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-%233776AB.svg)]()
[![Node](https://img.shields.io/badge/node-18-%234CC61E.svg)]()
[![Build Status](https://img.shields.io/github/actions/workflow/status/saiarjunkoyalkar756-sudo/PhantomNet-v2.0/ci.yml?branch=main)]()
[![Issues](https://img.shields.io/github/issues/saiarjunkoyalkar756-sudo/PhantomNet-v2.0)]()
[![Contributors](https://img.shields.io/github/contributors/saiarjunkoyalkar756-sudo/PhantomNet-v2.0)]()
![PhantomNet Image](docs/images/file_000000004544720988d35dea5d77e630.png)

---

📘 PhantomNet — v2.0

AI-Driven Autonomous Cybersecurity Framework

PhantomNet is an advanced, distributed cybersecurity platform powered by AI, behavioral analytics, blockchain-backed auditing, and modular microservices.
It is designed to simulate, detect, analyze, and neutralize cyber threats in real time—functioning as an autonomous SOC (Security Operations Center).

This repository includes the backend microservices, neural threat analysis engine, federated blockchain layer, React/Tailwind dashboard, full documentation, and deployment instructions.

For a detailed overview of the project's features, repository structure, and system architecture, please refer to the [Architecture Documentation](docs/ARCHITECTURE.md).
For comprehensive deployment instructions for both backend and agent, consult the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md).
For API details and specifications, refer to the [API Documentation](docs/API_DOCUMENTATION.md).

---
---
🚀 Agent Installation

The PhantomNet Agent can be installed on Windows, mainstream Linux distributions (Debian/Ubuntu/CentOS/Arch), and Termux (Android aarch64).

1.  **Windows Agent Installation**
    *   **Prerequisites**:
        *   Windows 10/11 (64-bit)
        *   Python 3.11 (manual installation from python.org is required)
        *   Visual C++ Redistributable (latest version recommended)
        *   Administrator privileges to run the installer.
    *   **Installation Steps**:
        1.  Download the `install_windows.ps1` script.
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

2.  **Linux Agent Installation**
    *   **Prerequisites**:
        *   Mainstream Linux Distribution (Debian, Ubuntu, CentOS, Fedora, Arch)
        *   Python 3.11 (usually available via package manager)
        *   Root privileges (`sudo`) to run the installer.
    *   **Installation Steps**:
        1.  Download the `install_linux.sh` script.
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

3.  **Termux Agent Installation (Android aarch64)**
    *   **Prerequisites**:
        *   Termux app installed on Android (aarch64 device recommended).
        *   Internet connection.
    *   **Installation Steps**:
        1.  Open Termux.
        2.  Download the `install_termux.sh` script.
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

---
---
🤖 CI / CD (GitHub Actions)

Your repo includes:

.github/workflows/build-and-test.yml

This pipeline:

Installs dependencies (platform-specific)
Runs unit tests across Linux, Windows, and emulated Termux environments.
Builds PyInstaller executables for Linux and Windows agents as artifacts.
Prevents broken PRs.

---
**Platform Abstraction Layer:**
The PhantomNet Agent now incorporates a robust platform abstraction layer (`phantomnet_agent/platform_compatibility/`) to centralize OS-specific operations. This ensures that core agent logic remains cross-platform while leveraging native system capabilities where necessary.

---

**Cross-Platform Agent Packaging (PyInstaller):**
PyInstaller spec files (`phantomnet_agent/pyinstaller/`) are provided for creating standalone executables for Linux and Windows.

To cross-build Linux executables from a Docker environment (e.g., on a Windows/macOS host):
1. Ensure Docker is running.
2. Build a Docker image with Python and PyInstaller:
   `docker build -t pyinstaller-builder -f Dockerfile.pyinstaller .` (You would need to create this Dockerfile)
3. Run the build:
   `docker run --rm -v $(pwd):/src pyinstaller-builder "pyinstaller phantomnet_agent/pyinstaller/agent-linux.spec"`

---

🔐 Security Practices
