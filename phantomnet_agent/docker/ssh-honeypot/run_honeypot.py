# docker/ssh-honeypot/run_honeypot.py
import asyncio
import sys
import os
import threading
import json
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from honeypots.ssh_honeypot import SSHHoneypot
# Assuming these can be imported directly or made available in the path
from backend_api.honeypot_service.forwarder import forward_event # This will use its own print now
from backend_api.honeypot_service.metrics import honeypot_sessions_total, honeypot_events_total, honeypot_errors_total

logger = logging.getLogger(__name__)

async def main():
    honeypot_id = os.getenv("HONEYPOT_ID", "default-docker-ssh-honeypot")
    honeypot_port = int(os.getenv("HONEYPOT_PORT", "2222"))
    honeypot_host = os.getenv("HONEYPOT_HOST", "0.0.0.0") # Bind to all interfaces in Docker

    print(f"Starting standalone SSH Honeypot (ID: {honeypot_id}) on {honeypot_host}:{honeypot_port}")

    # For standalone honeypot, event_forwarder will print to stdout
    async def standalone_event_forwarder(event: dict):
        # In a real deployed scenario, this would send to a central API or message bus
        # For this Docker image, we print to stdout to be collected by Docker logs
        print(json.dumps(event))
        # Update local metrics as well
        if event.get("event_type") == "auth_attempt":
            honeypot_events_total.labels(
                honeypot_id=honeypot_id,
                honeypot_type="ssh",
                event_type="auth_attempt"
            ).inc()
        # Add other event types if necessary

    shutdown_event = threading.Event() # Not directly used in asyncio loop but passed to Honeypot base

    honeypot_instance = SSHHoneypot(
        honeypot_id=honeypot_id,
        port=honeypot_port,
        event_forwarder=standalone_event_forwarder,
        shutdown_event=shutdown_event # Pass the event, even if not directly used in run()
    )

    try:
        await honeypot_instance.run()
    except asyncio.CancelledError:
        print(f"Honeypot {honeypot_id} cancelled.")
    except Exception as e:
        print(f"Error running honeypot {honeypot_id}: {e}")
        honeypot_errors_total.labels(
            honeypot_id=honeypot_id,
            honeypot_type="ssh",
            error_type=e.__class__.__name__
        ).inc()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
