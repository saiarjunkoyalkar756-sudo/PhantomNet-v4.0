#!/bin/bash
#
# PhantomNet Backend Runner
#
# This script starts the PhantomNet backend services using docker-compose.
#
# Usage: ./run_backend.sh [dev|prod]
#
# dev:  Starts services in attached mode with hot-reloading where applicable.
# prod: Starts services in detached mode for production.
#

# --- Helper Functions ---
function print_info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

function print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

# --- Main Script ---
MODE=$1
if [ -z "$MODE" ]; then
    MODE="dev"
fi

print_info "Starting PhantomNet Backend in '$MODE' mode..."

if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

if [ "$MODE" == "prod" ]; then
    print_info "Building and starting services in detached mode..."
    docker compose -f docker-compose.yml up --build -d
    print_info "To view logs, run: docker-compose logs -f"
    print_info "To stop services, run: docker-compose down"
else
    print_info "Building and starting services in attached mode..."
    docker compose -f docker-compose.yml up --build
fi

if [ $? -ne 0 ]; then
    print_error "docker-compose failed to start. Please check the output for errors."
    exit 1
fi