#!/bin/bash
#
# PhantomNet Agent Installer for Linux
#
# This script automates the installation and setup of the PhantomNet agent
# as a systemd service.
#

# --- Helper Functions ---
function print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

function print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

function print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

function check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 could not be found. Please install it before proceeding."
        exit 1
    fi
}

# --- Main Script ---

print_info "Starting PhantomNet Agent Installation for Linux..."

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  print_error "Please run as root."
  exit 1
fi

# 1. Check for dependencies
print_info "Checking for dependencies (python3, pip)..."
check_command python3
check_command pip3

print_success "All dependencies are installed."

# 2. Create installation directory
AGENT_DIR="/opt/phantomnet-agent"
print_info "Creating installation directory at $AGENT_DIR..."
mkdir -p $AGENT_DIR
cp -r ../phantomnet_agent/* $AGENT_DIR/
print_success "Agent files copied to $AGENT_DIR."

# 3. Create virtual environment and install dependencies
print_info "Creating Python virtual environment..."
python3 -m venv $AGENT_DIR/venv
source $AGENT_DIR/venv/bin/activate

print_info "Installing Python dependencies..."
pip3 install -r $AGENT_DIR/requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install Python dependencies."
    exit 1
fi
print_success "Python dependencies installed."

# 4. Set up systemd service
print_info "Setting up systemd service..."
SERVICE_FILE="/etc/systemd/system/phantomnet-agent.service"
cp $AGENT_DIR/scripts/phantomnet-agent.service $SERVICE_FILE

print_info "Reloading systemd daemon..."
systemctl daemon-reload

print_info "Enabling and starting PhantomNet agent service..."
systemctl enable phantomnet-agent.service
systemctl start phantomnet-agent.service

if systemctl is-active --quiet phantomnet-agent.service; then
    print_success "PhantomNet agent service started successfully."
    print_info "To check the status, run: systemctl status phantomnet-agent.service"
    print_info "To view logs, run: journalctl -u phantomnet-agent -f"
else
    print_error "Failed to start PhantomNet agent service."
    journalctl -u phantomnet-agent.service --no-pager
    exit 1
fi

exit 0
