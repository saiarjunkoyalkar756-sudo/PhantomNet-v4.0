#!/bin/bash

# Ensure the script exits if any command fails
set -e

# Define a temporary file to store PIDs
PID_FILE="/data/data/com.termux/files/home/.gemini/tmp/10524129f4dfffeb3eb20fa05f2616bdadbaeed2d7d07dc8014a2c2bf113b35a/honeypot_pids.tmp"

# Clean up previous PID file if it exists
if [ -f "$PID_FILE" ]; then
    rm "$PID_FILE"
fi

echo "Starting backend gateway service..."
cd backend_api/gateway_service
export PYTHONPATH="$(pwd)/..:$PYTHONPATH"
export JWT_SECRET_KEY="super_secret_key_change_me"
uvicorn gateway_service.main:app --host 0.0.0.0 --port 8000 --reload &
GATEWAY_PID=$!
echo "$GATEWAY_PID" >> "$PID_FILE"
cd ../..

echo "Starting honeypot service..."
cd backend_api/honeypot_service
uvicorn main:app --host 0.0.0.0 --port 8100 --reload &
HONEYPOT_SERVICE_PID=$!
echo "$HONEYPOT_SERVICE_PID" >> "$PID_FILE"
cd ../..

echo "Waiting for services to start..."
sleep 5

echo "Creating a default low-interaction SSH honeypot via API..."
curl -X POST http://localhost:8100/honeypots \
     -H "Content-Type: application/json" \
     -d '{ "honeypot_id": "default_ssh_honeypot", "type": "ssh", "port": 2222, "host": "127.0.0.1", "capture_level": "low", "tags": ["default", "test"] }'

echo "Services and default SSH honeypot started. PIDs stored in $PID_FILE"
echo "To stop services, run 'bash scripts/honeypot_stop.sh'"

# Keep the script running to keep the background processes alive,
# This script is intended to be run in the background or a separate terminal,
# so not using `wait` here.
# If this script is run as part of CI, then `wait` might be useful.
# wait $GATEWAY_PID $HONEYPOT_SERVICE_PID
