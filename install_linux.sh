#!/bin/bash
# install_linux.sh
# Unified installer script for PhantomNet Agent on Linux (Ubuntu/Debian/Kali/Fedora/Arch)

# --- Configuration ---
AGENT_DIR="phantomnet_agent"
PYTHON_VERSION="3.11" # Ensure this matches your Python environment
VENV_DIR=".venv_phantomnet"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"

# --- Functions ---
log_info() {
    echo "INFO: $1"
}

log_warn() {
    echo "WARN: $1"
}

log_error() {
    echo "ERROR: $1"
    exit 1
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This script must be run as root. Please use 'sudo bash $0'."
    fi
}

install_prerequisites() {
    log_info "Installing system prerequisites..."
    if command -v apt >/dev/null; then
        # Debian/Ubuntu/Kali
        apt update && apt install -y python3-venv python3-dev libelf-dev libpcap-dev clang llvm libxml2-dev libxslt1-dev zlib1g-dev nmap
    elif command -v dnf >/dev/null; then
        # Fedora
        dnf install -y python3 python3-devel libbpf-devel libcap-devel clang llvm libxml2-devel libxslt-devel zlib-devel nmap
    elif command -v pacman >/dev/null; then
        # Arch Linux
        pacman -Sy --noconfirm python python-pip python-virtualenv base-devel libelf libpcap clang llvm libxml2 libxslt zlib nmap
    else
        log_warn "Unsupported package manager. Please manually install python3-venv, development headers (python3-dev, libelf-dev, libpcap-dev), clang, llvm, and nmap."
    fi
}

setup_python_env() {
    log_info "Setting up Python virtual environment..."
    python3 -m venv ${VENV_DIR} || log_error "Failed to create virtual environment."
    source ${VENV_DIR}/bin/activate
    ${PIP_BIN} install --upgrade pip || log_error "Failed to upgrade pip."
    ${PIP_BIN} install wheel || log_error "Failed to install wheel."
    # Install httpx for telemetry-ingestor post requests from agent
    ${PIP_BIN} install httpx || log_error "Failed to install httpx."
}

install_python_deps() {
    log_info "Installing Python dependencies for the agent..."
    ${PIP_BIN} install -r requirements-linux.txt || log_error "Failed to install Python dependencies for agent."
    
    log_info "Attempting to install BCC (eBPF) and YARA Python bindings..."
    log_warn "BCC and YARA Python installation may fail if system dependencies (kernel headers, libbcc-dev, libyara-dev) are not met."
    # These are now in requirements-linux.txt, but keeping the warning
}

create_systemd_services() {
    log_info "Creating systemd service file for PhantomNet Agent..."
    
    CURRENT_DIR=$(pwd) # Get current working directory

    # Agent Service
    AGENT_SERVICE_FILE="/etc/systemd/system/phantomnet-agent.service"
    cp "${CURRENT_DIR}/files/systemd/phantomnet-agent.service" "${AGENT_SERVICE_FILE}"
    sed -i "s|/path/to/phantomnet|${CURRENT_DIR}|g" "${AGENT_SERVICE_FILE}"
    sed -i "s|User=\$(whoami)|User=${SUDO_USER:-$(whoami)}|g" "${AGENT_SERVICE_FILE}" # Set user correctly

    systemctl daemon-reload
    systemctl enable phantomnet-agent.service
    log_info "PhantomNet agent systemd service created and enabled."
}

# --- Main script execution ---
check_root
install_prerequisites
setup_python_env
install_python_deps
create_systemd_services

log_info "Linux Agent installation complete. Please review any warnings."
log_info "To start/stop/manage the agent service, use 'sudo systemctl <start|stop|status|restart> phantomnet-agent.service'."
log_warn "If eBPF or YARA components failed to install, those specific features will be disabled or operate in limited mode."
