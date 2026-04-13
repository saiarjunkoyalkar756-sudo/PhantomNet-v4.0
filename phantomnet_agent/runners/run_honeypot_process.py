# runners/run_honeypot_process.py
import asyncio
import sys
import os
import json
import logging
import argparse
import threading # For the shutdown_event

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import modules needed by the honeypots
# These are relative imports if run from the project root, but absolute if run from runners dir
from honeypots.ssh_honeypot import SSHHoneypot
# Assuming these can be imported directly or made available in the path
from backend_api.honeypot_service.forwarder import forward_event # This will use its own print now
from backend_api.honeypot_service.metrics import honeypot_sessions_total, honeypot_events_total, honeypot_errors_total


logger = logging.getLogger(__name__)

async def run_honeypot_instance(honeypot_id: str, honeypot_type: str, port: int):
    # Dynamically import the honeypot module
    try:
        honeypot_module = __import__(f"honeypots.{honeypot_type}_honeypot", fromlist=[f"{honeypot_type.capitalize()}Honeypot"])
        HoneypotClass = getattr(honeypot_module, f"{honeypot_type.capitalize()}Honeypot")
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load honeypot type {honeypot_type}: {e}")
        return

    shutdown_event = threading.Event()

    # For local process runner, the event_forwarder is the same as the service's one
    # as this process is part of the same Python environment
    honeypot_instance = HoneypotClass(
        honeypot_id=honeypot_id,
        port=port,
        event_forwarder=forward_event, # Use the actual forwarder
        shutdown_event=shutdown_event
    )

    try:
        await honeypot_instance.run()
    except asyncio.CancelledError:
        logger.info(f"Honeypot {honeypot_id} (type: {honeypot_type}) cancelled.")
    except Exception as e:
        logger.error(f"Error running honeypot {honeypot_id} (type: {honeypot_type}): {e}")
        honeypot_errors_total.labels(
            honeypot_id=honeypot_id,
            honeypot_type=honeypot_type,
            error_type=e.__class__.__name__
        ).inc()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Run a honeypot instance.")
    parser.add_argument("--honeypot_id", required=True, help="Unique ID for the honeypot.")
    parser.add_argument("--honeypot_type", required=True, help="Type of the honeypot (e.g., ssh, ftp).")
    parser.add_argument("--port", type=int, required=True, help="Port for the honeypot to listen on.")
    
    args = parser.parse_args()

    asyncio.run(run_honeypot_instance(args.honeypot_id, args.honeypot_type, args.port))
