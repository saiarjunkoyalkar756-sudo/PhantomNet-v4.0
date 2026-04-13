#!/bin/bash
#
# PhantomNet Backend Installer
#
# This script automates the setup and launch of the PhantomNet backend services
# using Docker and docker-compose.
#

# --- Helper Functions ---
function print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

function print_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

function print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
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

print_info "Starting PhantomNet Backend Installation..."

# 1. Check for dependencies
print_info "Checking for dependencies (Docker, docker-compose)..."
check_command docker
check_command docker-compose

print_success "All dependencies are installed."

# 2. Check for .env file
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Copying from .env.example."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env file. Please review and edit it before running in production."
    else
        print_error ".env.example not found. Cannot create .env file. Please create one manually."
        exit 1
    fi
fi

# 3. Create necessary directories
print_info "Creating necessary directories..."
mkdir -p /data/db # For databases
mkdir -p /forensics_repo # For forensics data

print_success "Directories created."

# 4. Build and launch Docker containers
print_info "Building and launching backend services with docker-compose..."
print_info "This may take a while on the first run..."

docker-compose up --build -d

if [ $? -eq 0 ]; then
    print_success "PhantomNet backend services started successfully."
    print_info "To view logs, run: docker-compose logs -f"
    print_info "To stop services, run: docker-compose down"
else
    print_error "docker-compose up failed. Please check the output for errors."
    exit 1
fi

exit 0
