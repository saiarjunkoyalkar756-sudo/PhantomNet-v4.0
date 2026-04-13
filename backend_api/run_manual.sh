#!/bin/bash

# This script starts all backend services.
# Make sure you have PostgreSQL and Redis running before executing this script.

# Function to set up venv and install dependencies for a service
setup_service_venv() {
  local service_dir=$1
  
  echo "--- Setting up venv and dependencies for $service_dir ---"
  
  (
    cd "$service_dir" || exit
    
    # Create venv and install dependencies if it doesn't exist
    if [ ! -d ".venv" ]; then
      echo "Creating virtual environment for $service_dir..."
      python -m venv .venv
    fi
    source .venv/bin/activate
    echo "Installing dependencies for $service_dir..."
    pip install -r requirements.txt
    deactivate # Deactivate after installation
  )
}

# Function to run a service as a Python module from the project root
run_service_module() {
  local service_dir=$1
  local module_name=$2
  local env_vars=$3 # All environment variables as a single string
  
  echo "--- Starting $service_dir/$module_name ---"
  
  # Activate the virtual environment for the service in a subshell
  (
    source "$service_dir/.venv/bin/activate"

    # Set PYTHONPATH to include the project root (current directory of run_manual.sh)
    # This allows Python to resolve relative imports from the service directories.
    export PYTHONPATH="$(pwd):$PYTHONPATH"

    eval "$env_vars uvicorn $service_dir.$module_name:app --host 0.0.0.0 --port $(get_service_port "$service_dir")"
  ) &
}

# Function to get service port (placeholder - usually defined in main.py or config)
# For now, we'll hardcode based on common FastAPI patterns or assign sequentially
get_service_port() {
  local service_name=$1
  case "$service_name" in
    "gateway_service")
      echo "8000"
      ;;
    "analyzer")
      echo "8001" # Example port
      ;;
    "asset_inventory")
      echo "8002" # Example port
      ;;
    *)
      echo "8080" # Default or other logic
      ;;
  esac
}

# --- Setup Virtual Environments (Run once for all services) ---
setup_service_venv "analyzer"
setup_service_venv "asset_inventory"
setup_service_venv "gateway_service"

# --- Service Definitions ---
# Note: The actual Python module name for each service.
# The 'app' object is assumed to be named 'app' in the main FastAPI file.

ANALYZER_ENV="LOG_LEVEL=INFO LOG_FORMAT=json REDIS_HOST=localhost"
ASSET_INVENTORY_ENV="LOG_LEVEL=INFO LOG_FORMAT=json DATABASE_URL=postgresql://user:password@localhost:5432/maindb"
GATEWAY_ENV="LOG_LEVEL=DEBUG LOG_FORMAT=json OPERATIONAL_DB_URL=postgresql://user:password@localhost:5432/maindb POLICY_DB_URL=postgresql://user:password@localhost:5432/maindb REDIS_HOST=localhost SECRET_KEY=a_much_better_secret_key_that_is_still_not_for_production"

# --- Start Services ---
run_service_module "analyzer" "app" "$ANALYZER_ENV"
run_service_module "asset_inventory" "app" "$ASSET_INVENTORY_ENV"
run_service_module "gateway_service" "main" "$GATEWAY_ENV"

echo "All services are starting in the background."
echo "API Gateway should be available at http://localhost:8000 shortly."
echo "Press Ctrl+C to stop all services."

# Wait for all background processes to finish
wait
