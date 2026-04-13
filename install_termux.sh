#!/data/data/com.termux/files/usr/bin/bash
# install_termux.sh
# Unified installer script for PhantomNet Agent on Termux (Android environment)

# --- Configuration ---
AGENT_DIR="phantomnet_agent"
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

install_termux_prerequisites() {
    log_info "Updating Termux packages and installing prerequisites..."
    pkg update -y || log_error "Failed to update Termux packages."
    pkg upgrade -y || log_error "Failed to upgrade Termux packages."
    pkg install -y python python-pip rust libpcap libxml2 libxslt openssl git || log_error "Failed to install Termux prerequisites."
    log_info "Termux prerequisites installed."
}

setup_python_env() {
    log_info "Setting up Python virtual environment..."
    python -m venv ${VENV_DIR} || log_error "Failed to create virtual environment."
    # Source the activate script within this shell to make PYTHON_BIN and PIP_BIN directly available for the current script execution.
    # Note: 'source' command is shell-specific, so if running with 'bash -c', it needs to be adapted or full paths used explicitly.
    source "${VENV_DIR}/bin/activate" || log_error "Failed to activate virtual environment."
    
    # Use Termux-specific pip upgrade guidance
    log_warn "On Termux, avoid 'pip install --upgrade pip'. Termux maintains its own patched pip."
    ${PIP_BIN} install wheel || log_error "Failed to install wheel."
}

install_python_deps() {
    log_info "Installing Python dependencies for the agent (lightweight mode for Termux)..."
    # Use the platform-specific requirements file
    ${PIP_BIN} install -r "requirements-termux.txt" || log_error "Failed to install Python dependencies for agent."
    
    log_warn "eBPF (bcc, pyroute2) and advanced memory scanning (yara-python) are typically not supported or difficult to install on Termux."
    log_warn "PhantomNet agent will automatically disable or operate these features in limited mode."
    log_warn "Raw socket operations (e.g., Scapy's full functionality) may require root/special permissions on Android/Termux."
}

create_termux_startup_script() {
    log_info "Creating Termux startup script for PhantomNet Agent..."
    STARTUP_SCRIPT="$HOME/bin/start-phantomnet-agent.sh"
    mkdir -p "$HOME/bin"
    cat << EOF | tee ${STARTUP_SCRIPT}
#!/data/data/com.termux/files/usr/bin/bash
# Script to start PhantomNet Agent in Termux
# To run automatically on Termux startup, ensure this script is in ~/.termux/boot/

log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: \$1"
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: \$1" >&2
}

cd "$(dirname "\$0")/../../${AGENT_DIR}" || { log_error "Failed to change to agent directory."; exit 1; }

VENV_PATH="${PWD}/../${VENV_DIR}"
PYTHON_EXE="${VENV_PATH}/bin/python"
AGENT_MAIN="main.py"

if [ ! -f "\${PYTHON_EXE}" ]; then
    log_error "Python executable not found at \${PYTHON_EXE}. Please re-run installer."
    exit 1
fi

log_info "Starting PhantomNet Agent..."
# Run in background and redirect output to agent logs directory
# Using a placeholder for AGENT_ID that should be replaced during actual agent startup or read from config
AGENT_ID_PLACEHOLDER="termux_agent_$(hostname | tr -d ' ' | tr '[:upper:]' '[:lower:]')" 
mkdir -p "${PWD}/logs" # Ensure logs directory exists
nohup "\${PYTHON_EXE}" "\${AGENT_MAIN}" > "logs/\${AGENT_ID_PLACEHOLDER}_stdout.log" 2> "logs/\${AGENT_ID_PLACEHOLDER}_stderr.log" &
echo \$! > agent.pid
log_info "PhantomNet Agent started with PID \$!."
log_info "Logs: \$PWD/logs/\${AGENT_ID_PLACEHOLDER}_stdout.log, \$PWD/logs/\${AGENT_ID_PLACEHOLDER}_stderr.log"
log_info "To stop: kill \$(cat agent.pid)"
EOF
    chmod +x ${STARTUP_SCRIPT}
    log_info "Termux startup script created: ${STARTUP_SCRIPT}"
    log_info "To run on Termux boot, copy/link this script to ~/.termux/boot/"
}

# --- Main script execution ---
install_termux_prerequisites
setup_python_env
install_python_deps
create_termux_startup_script

log_info "Termux Agent installation complete. Please review any warnings."
log_info "To start the agent: ${HOME}/bin/start-phantomnet-agent.sh"
log_info "To stop the agent: kill \$(cat phantomnet_agent/agent.pid)"
log_warn "Remember to enable storage permissions for Termux and provide necessary network/root access if advanced features are desired (e.g., packet capture with root)."
