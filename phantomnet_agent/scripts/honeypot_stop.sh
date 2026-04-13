#!/bin/bash

# Ensure the script exits if any command fails
set -e

PID_FILE="/data/data/com.termux/files/home/.gemini/tmp/10524129f4dfffeb3eb20fa05f2616bdadbaeed2d7d07dc8014a2c2bf113b35a/honeypot_pids.tmp"

if [ ! -f "$PID_FILE" ]; then
    echo "PID file not found: $PID_FILE. No services to stop."
    exit 0
fi

echo "Stopping honeypots via API..."
# First, try to stop any running honeypots gracefully via the API
# This assumes the honeypot_service is still running
curl -X GET http://localhost:8100/honeypots 2>/dev/null | jq -r '.[].honeypot_id' | while read -r HONEYPOT_ID; do
    if [ -n "$HONEYPOT_ID" ]; then
        echo "Stopping honeypot: $HONEYPOT_ID"
        curl -X POST http://localhost:8100/honeypots/"$HONEYPOT_ID"/stop 2>/dev/null
    fi
done

echo "Stopping backend services..."
PIDS=$(cat "$PID_FILE")

for PID in $PIDS; do
    if ps -p "$PID" > /dev/null; then
        echo "Killing process $PID..."
        kill "$PID"
    else
        echo "Process $PID not found, skipping."
    fi
done

echo "Waiting for processes to terminate..."
# Give processes some time to shut down
sleep 2

# Check if any processes are still running and force kill if necessary
for PID in $PIDS; do
    if ps -p "$PID" > /dev/null; then
        echo "Process $PID still running, force killing..."
        kill -9 "$PID"
    fi
done

rm "$PID_FILE"
echo "Services stopped and PID file removed."