import asyncio
import json
import os
import ssl
from pathlib import Path

import uvicorn
from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# --- Configuration ---

# Define paths to the certificates
CERT_PATH = Path(__file__).parent.parent / "phantomnet_agent" / "certs"
CA_CERT = CERT_PATH / "ca.crt"
SERVER_CERT = CERT_PATH / "server" / "server.crt"
SERVER_KEY = CERT_PATH / "server" / "server.key"

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")

# Mock database of registered agents and their expected attestation hashes
# In a real system, this would be a secure database.
# The hash would be pre-calculated and stored during agent deployment.
REGISTERED_AGENTS = {
    "AGENT-001": {
        "platform_id_hash": "a_pre_calculated_hash_for_agent_001"
    },
    # This is a placeholder for the agent you are currently running
    "my_test_agent": {
         # Replace this with the actual hash your test agent generates on startup
        "platform_id_hash": "a_pre_calculated_hash_for_my_test_agent"
    }
}


# --- Global Services ---

producer: KafkaProducer = None
app = FastAPI()
router = APIRouter()
manager = ConnectionManager()

# --- WebSocket Logic ---

class ConnectionManager:
    # ... (existing class) ...

async def _handle_attestation(websocket: WebSocket) -> bool:
    """
    Handles the initial agent identity attestation.
    Returns True if approved, False otherwise.
    """
    try:
        message = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        payload = json.loads(message)

        if payload.get("event_type") == "agent_attestation":
            agent_id = payload.get("agent_id")
            client_hash = payload.get("data", {}).get("platform_id_hash")
            
            # 1. Check if agent is registered
            agent_registration = REGISTERED_AGENTS.get(agent_id)
            if not agent_registration:
                await websocket.send_text(json.dumps({"status": "attestation_failed", "reason": "Agent ID not registered."}))
                return False

            # 2. Verify the platform hash
            # In a real system, you'd use a constant-time comparison
            if agent_registration["platform_id_hash"] != client_hash:
                await websocket.send_text(json.dumps({"status": "attestation_failed", "reason": "Platform attestation mismatch."}))
                return False
            
            # 3. Attestation successful
            await websocket.send_text(json.dumps({"status": "attestation_approved"}))
            print(f"Agent '{agent_id}' successfully attested.")
            return True
        else:
            await websocket.send_text(json.dumps({"status": "attestation_failed", "reason": "First message must be attestation."}))
            return False

    except asyncio.TimeoutError:
        print("Attestation failed: Timeout waiting for attestation payload.")
        return False
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Attestation failed: Invalid payload format. Error: {e}")
        return False

@router.websocket("/ws/network")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    if not producer:
        await websocket.close(code=1011, reason="Backend service unavailable")
        return

    # Phase 1: Agent Identity Attestation
    is_attested = await _handle_attestation(websocket)
    if not is_attested:
        await websocket.close(code=4003, reason="Attestation Failed")
        manager.disconnect(websocket)
        return

    # Phase 2: Continuous Event Streaming (only if attested)
    try:
        while True:
            data = await websocket.receive_text()
            producer.send("normalized-events", value=json.loads(data))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"An error occurred post-attestation: {e}")
        manager.disconnect(websocket)

# --- Application Setup ---

app.include_router(router)

if __name__ == "__main__":
    # ... (existing SSL and Uvicorn startup logic) ...
    # This part remains the same.
    pass