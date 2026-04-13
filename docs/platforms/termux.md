# Termux (Android) Installation Guide

This document provides a guide for installing and configuring the PhantomNet Agent on Termux, an Android terminal emulator. Due to the inherent restrictions of the Android operating system and the user-space nature of Termux, many kernel-level features available on traditional Linux are restricted or unavailable. The PhantomNet Agent is designed to adapt to these limitations by enabling `SAFE_MODE` for certain functionalities.

## 1. Prerequisites

*   **Android Device:** A smartphone or tablet running Android.
*   **Termux App:** Installed from F-Droid (recommended for up-to-date packages) or Google Play Store.
*   **Internet Connectivity:** Required for `pkg` commands and downloading dependencies.
*   **Storage Permissions:** Grant Termux access to storage by running `termux-setup-storage`.
*   **Root (Optional but Recommended for Advanced Features):** A rooted Android device provides more extensive capabilities, especially for network monitoring (raw sockets) and system-level diagnostics. Without root, many features will operate in a `SAFE_MODE` or be disabled.

## 2. Installation Steps

### Step 2.1: Open Termux and Install Git

Open the Termux app and run:

```bash
pkg update && pkg upgrade -y
pkg install git -y
```

### Step 2.2: Clone the PhantomNet Repository

```bash
git clone https://github.com/PhantomNet/PhantomNet.git
cd PhantomNet
```
*(Replace `https://github.com/PhantomNet/PhantomNet.git` with the actual repository URL if different.)*

### Step 2.3: Run the Unified Termux Installer

The `install_termux.sh` script automates the setup of Python virtual environments and installs Python dependencies adapted for the Termux environment.

```bash
chmod +x install_termux.sh
./install_termux.sh
```

The installer performs the following actions:
*   **Termux Package Installation:** Installs essential packages (`python`, `rust`, `libpcap`, `clang`, `make`, `libcrypt-dev`, `libxml2`, `libxslt`).
*   **Python Virtual Environment Setup:** Creates a virtual environment named `.venv_phantomnet` in the project root.
*   **Python Dependency Installation:** Installs Python libraries listed in `requirements-termux.txt`. This file minimizes problematic compiled packages. Specialized libraries like `bcc` (eBPF) and `yara-python` are deliberately excluded or their installation is skipped, as these generally do not work or are heavily restricted in Termux.

## 3. Managing PhantomNet Agent

Termux does not use `systemd`. The agent will be managed using a `nohup` script.

### Step 3.1: Start the PhantomNet Agent

```bash
./run_agent_termux.sh
```
This script will start the agent in the background (`nohup`) and redirect its output to log files within the `phantomnet_agent/logs/` directory. It will also create a `phantomnet_agent/agent.pid` file containing the process ID.

### Step 3.2: Check Agent Status and Logs

*   **Check if Agent is Running:**
    ```bash
    ps aux | grep main.py
    ```
    You should see an entry for `python phantomnet_agent/main.py`.
*   **Tail Agent Logs:**
    ```bash
    tail -f phantomnet_agent/logs/agent_stdout.log
    ```

### Step 3.3: Stop the Agent

```bash
kill $(cat phantomnet_agent/agent.pid)
```

### Step 3.4: Autostart Agent on Termux Boot (Optional)

To have the agent automatically start when Termux launches:
1.  Ensure you have the `Termux:Boot` add-on app installed from F-Droid or Google Play Store.
2.  Create a `~/.termux/boot/` directory if it doesn't exist: `mkdir -p ~/.termux/boot/`.
3.  Copy or link the `run_agent_termux.sh` script to this directory:
    ```bash
    cp run_agent_termux.sh ~/.termux/boot/
    ```
    The script will then execute automatically when Termux starts.

## 4. Troubleshooting

*   **`PermissionError` for Raw Sockets / Network Monitoring:**
    *   **Issue:** Scapy's full packet capture functionality often requires `CAP_NET_RAW` capability, which is usually unavailable in Termux unless the device is rooted and the Termux environment is specifically configured for it.
    *   **Solution:** The PhantomNet Agent will automatically detect this limitation and operate its network sensor in a `SAFE_MODE` (limited mode) or fallback to alternative methods like parsing `netstat` output if available.
*   **eBPF / Kernel Features Not Working:**
    *   **Issue:** eBPF and other kernel-level features are generally not supported in Termux, as they require direct interaction with the Linux kernel, which is restricted on Android.
    *   **Solution:** eBPF-dependent modules will be automatically disabled by the agent's capability negotiation layer.
*   **TensorFlow/ML Libs Failures:**
    *   **Issue:** Some complex ML libraries or their compiled binaries (`wheels`) might not be available for the `aarch64` architecture used by Android/Termux, or might be too resource-intensive.
    *   **Solution:** PhantomNet's AI components will fall back to a lighter "TensorLite Mode" or a simulated heuristic mode (`SAFE_MODE`) if full TensorFlow or other heavy ML dependencies cannot be met or installed.
*   **"Command not found" for `pkg` installed tools:**
    *   **Issue:** The script might fail to find a package even after `pkg install`.
    *   **Solution:** Ensure your Termux `$PATH` is correctly configured or restart Termux.

## 5. Security Guidance

*   **Secrets Management:** Never store sensitive information directly in configuration files. Use environment variables.
*   **Termux Permissions:** Be mindful of the permissions granted to the Termux app on your Android device. Avoid granting unnecessary access.
*   **Rooted Devices:** If running on a rooted device, exercise extreme caution. Root access grants significant power and potential for system compromise if not managed securely.
*   **Backend Connectivity:** Ensure the Termux agent can securely communicate with your PhantomNet Backend instance (e.g., via HTTPS if the backend is internet-facing).

## 6. Feature Gating & Fallbacks

The PhantomNet Agent for Termux is designed for resilience. Upon startup, it detects the Android/Termux environment and its specific capabilities. Features that are not supported (e.g., eBPF, raw sockets without root) or for which dependencies cannot be met will be automatically disabled or switch to a `SAFE_MODE` with graceful fallbacks (e.g., passive monitoring using user-space tools). This ensures continuous operation with reduced functionality tailored to the mobile environment.
