# PhantomNet Autonomous Cyber Defense Platform - Platform Support

This document outlines the cross-platform compatibility of the PhantomNet Agent and provides installation guides for supported operating systems, along with a feature matrix detailing capabilities.

## Supported Operating Systems

The PhantomNet Agent is designed to operate on the following platforms:

*   **Linux**: Ubuntu / Debian / Kali / Fedora / Arch (Full Feature Set)
*   **Windows**: Windows 10/11 (Partial Feature Set)
*   **Termux**: Android Environment (Limited Feature Set)

## Agent Feature Matrix by Operating System

| Feature                     | Linux (Full)         | Windows 10/11 (Partial)      | Termux (Limited)             | Notes                                                              |
| :-------------------------- | :------------------- | :--------------------------- | :--------------------------- | :----------------------------------------------------------------- |
| **OS Detection**            | ✔ Full               | ✔ Full                       | ✔ Full                       | Handled by `phantomnet_core/os_adapter.py`                         |
| **Automatic Capability Negotiation** | ✔ Full               | ✔ Full                       | ✔ Full                       | Agent dynamically adapts features based on detected OS capabilities. |
| **Network Sensors**         |                      |                              |                              |                                                                    |
| Packet Capture (Scapy)      | ✔ Full (eBPF + Scapy)| ✔ Full (Npcap/WinPcap + Scapy)| ✖ Limited (Scapy without raw sockets, simulated) | Requires appropriate drivers and privileges.                       |
| **Process Monitoring**      |                      |                              |                              |                                                                    |
| Core (psutil)               | ✔ Full (`/proc`)     | ✔ Full (Win32 API + psutil)  | ✔ Full (`/proc` + toybox)    | `psutil` provides cross-platform basic info.                     |
| eBPF Process Monitor        | ✔ Full               | ✖ Not Available              | ✖ Not Available              | Requires Linux kernel support for eBPF.                            |
| **File Monitoring**         |                      |                              |                              |                                                                    |
| Core (watchdog)             | ✔ Full (inotify)     | ✔ Full (Windows API)         | ✔ Full (polling fallback or inotify-lite) | Watchdog provides cross-platform event handling.                     |
| eBPF File Monitor           | ✔ Full               | ✖ Not Available              | ✖ Not Available              | Requires Linux kernel support for eBPF.                            |
| **Registry Monitoring**     |                      |                              |                              |                                                                    |
| Windows Registry Monitor    | ✖ Not Available      | ✔ Full (pywin32)             | ✖ Not Available              | Windows-specific feature.                                          |
| **Driver Monitoring**       |                      |                              |                              |                                                                    |
| eBPF Driver Monitor         | ✔ Full               | ✖ Not Available              | ✖ Not Available              | Monitors Linux kernel module loading.                              |
| **Memory Scanning**         |                      |                              |                              |                                                                    |
| YARA Engine                 | ✔ Full (yara-python) | ✔ Full (yara-python)         | ✖ Limited (simulated)        | Requires `yara-python` and appropriate memory access privileges.     |
| **AI Engine Mode**          | ✔ Full               | ✔ Full                       | ✔ TensorLite Mode            | Termux operates in a resource-constrained "TensorLite" mode.       |

## Installation Guides

---

### Linux Installation

This guide covers installation on Ubuntu, Debian, Kali, Fedora, and Arch Linux distributions.

**Prerequisites:**

*   `sudo` privileges.
*   Internet connectivity.
*   Python 3.11 installed.

**Installation Steps:**

1.  **Download the Installer:**
    ```bash
    git clone https://github.com/PhantomNet/PhantomNet.git
    cd PhantomNet
    ```
    *(Assuming your project is in a `PhantomNet` directory)*
2.  **Run the Installer Script:**
    ```bash
    chmod +x install_linux.sh
    sudo ./install_linux.sh
    ```
    The script will:
    *   Install necessary system packages (Python development headers, `libpcap`, `clang`, `llvm`, `libelf-dev`, `nmap`).
    *   Set up a Python virtual environment.
    *   Install Python dependencies including `scapy`, `bcc` (eBPF tools), and `yara-python`. Note that `bcc` and `yara-python` may require additional system development headers and tools to compile.
    *   Create a `systemd` service for the PhantomNet Agent for automatic startup.
3.  **Start the Agent Service:**
    ```bash
    sudo systemctl start phantomnet-agent.service
    ```
4.  **Verify Status and Logs:**
    ```bash
    sudo systemctl status phantomnet-agent.service
    journalctl -u phantomnet-agent.service -f
    ```

---

### Windows Installation

This guide covers installation on Windows 10/11.

**Prerequisites:**

*   Administrator privileges.
*   Internet connectivity.
*   Python 3.11 installed and added to PATH. (Automatic installation not yet implemented).
*   Disable Windows Defender or add exceptions for PhantomNet directories to prevent interference.

**Installation Steps:**

1.  **Download the Installer:**
    ```powershell
    # Open PowerShell as Administrator
    git clone https://github.com/PhantomNet/PhantomNet.git
    cd PhantomNet
    ```
    *(Assuming your project is in a `PhantomNet` directory)*
2.  **Run the Installer Script:**
    ```powershell
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser # If not already set
    .\install_windows.ps1
    ```
    The script will:
    *   Attempt to install Npcap silently (required for Scapy's packet capture). You may need to manually confirm installation or restart.
    *   Set up a Python virtual environment.
    *   Install Python dependencies including `pywin32`, `wmi`, `scapy`, and `yara-python`.
    *   Register the PhantomNet Agent as a Windows Service for automatic startup.
3.  **Start the Agent Service:**
    ```powershell
    Start-Service PhantomNetAgent
    ```
4.  **Verify Status:**
    ```powershell
    Get-Service PhantomNetAgent
    ```
    Agent logs will be located in `phantomnet_agent\logs\phantomnet_agent_service_stdout.log` and `phantomnet_agent\logs\phantomnet_agent_service_stderr.log`.

---

### Termux Installation (Android)

This guide covers installation on Termux within an Android environment. Due to the nature of Android and Termux, many kernel-level features available on traditional Linux are restricted or unavailable. The agent will adapt to these limitations.

**Prerequisites:**

*   A rooted Android device is highly recommended for advanced features (e.g., raw sockets for Scapy).
*   Termux app installed.
*   Internet connectivity.
*   Storage permissions granted to Termux (`termux-setup-storage`).

**Installation Steps:**

1.  **Open Termux and Install Git:**
    ```bash
    pkg update && pkg upgrade -y
    pkg install git -y
    ```
2.  **Download the Installer:**
    ```bash
    git clone https://github.com/PhantomNet/PhantomNet.git
    cd PhantomNet
    ```
    *(Assuming your project is in a `PhantomNet` directory)*
3.  **Run the Installer Script:**
    ```bash
    chmod +x install_termux.sh
    ./install_termux.sh
    ```
    The script will:
    *   Install Termux packages (`python`, `rust`, `libpcap`, `libxml2`, `libxslt`).
    *   Set up a Python virtual environment.
    *   Install Python dependencies. Problematic libraries (`bcc`, `pyroute2`, `yara-python`) are excluded, and the agent will use its capability negotiation to disable or operate features in limited mode.
    *   Create a simple startup script for the PhantomNet Agent.
4.  **Start the Agent:**
    ```bash
    ~/bin/start-phantomnet-agent.sh
    ```
5.  **Verify Status and Logs:**
    ```bash
    ps aux | grep main.py
    tail -f phantomnet_agent/logs/agent_stdout.log
    ```
    To stop the agent, use `kill $(cat phantomnet_agent/agent.pid)`.
    To have the agent start automatically on Termux boot, copy or link `~/bin/start-phantomnet-agent.sh` to `~/.termux/boot/`.

---

## Conclusion

The PhantomNet Agent is designed with a layered approach to ensure functionality across diverse operating environments. While core monitoring capabilities are maintained across all platforms, specialized kernel-level and deeply integrated features will be dynamically enabled or disabled based on the host OS's capabilities and available system-level tools. This ensures a robust and adaptive defense posture regardless of the deployment environment.
