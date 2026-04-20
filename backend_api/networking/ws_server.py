from backend_api.shared.service_factory import create_phantom_service
import asyncio
import json
import os
import ssl
from pathlib import Path
from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from loguru import logger
from typing import Optional, List, Dict, Any

# --- Configuration ---
CERT_PATH = Path(__file__).parent.parent / "phantomnet_agent" / "certs"
CA_CERT = CERT_PATH / "ca.crt"
SERVER_CERT = CERT_PATH / "server" / "server.crt"
SERVER_KEY = CERT_PATH / "server" / "server.key"

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")

REGISTERED_AGENTS = {
    "AGENT-001": {
        "platform_id_hash": "a_pre_calculated_hash_for_agent_001"
    },
    "my_test_agent": {
        "platform_id_hash": "a_pre_calculated_hash_for_my_test_agent"
    }
}

# --- Global Services ---
producer: Optional[KafkaProducer] = None
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

manager = ConnectionManager()

async def _handle_attestation(websocket: WebSocket) -> bool:
    try:
        message = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        payload = json.loads(message)

        if payload.get("event_type") == "agent_attestation":
            agent_id = payload.get("agent_id")
            client_hash = payload.get("data", {}).get("platform_id_hash")
            
            agent_registration = REGISTERED_AGENTS.get(agent_id)
            if not agent_registration:
                await websocket.send_text(json.dumps({"status": "attestation_failed", "reason": "Agent ID not registered."}))
                return False

            if agent_registration["platform_id_hash"] != client_hash:
                await websocket.send_text(json.dumps({"status": "attestation_failed", "reason": "Platform attestation mismatch."}))
                return False
            
            await websocket.send_text(json.dumps({"status": "attestation_approved"}))
            logger.info(f"Agent '{agent_id}' successfully attested.")
            return True
        else:
            await websocket.send_text(json.dumps({"status": "attestation_failed", "reason": "First message must be attestation."}))
            return False
    except Exception as e:
        logger.error(f"Attestation failed: {e}")
        return False

@router.websocket("/ws/network")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    if not producer:
        await websocket.close(code=1011, reason="Backend service unavailable")
        return

    is_attested = await _handle_attestation(websocket)
    if not is_attested:
        await websocket.close(code=4003, reason="Attestation Failed")
        manager.disconnect(websocket)
        return

    try:
        while True:
            data = await websocket.receive_text()
            producer.send("normalized-events", value=json.loads(data))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def ws_startup(app: FastAPI):
    global producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        logger.info("WebSocket Server: Kafka producer connected.")
    except NoBrokersAvailable:
        logger.error("WebSocket Server: No Kafka brokers available.")

async def ws_shutdown(app: FastAPI):
    global producer
    if producer:
        producer.close()
        logger.info("WebSocket Server: Kafka producer closed.")

app = create_phantom_service(
    name="Networking WebSocket Server",
    description="Secure WebSocket server for agent communication.",
    version="1.0.0",
    custom_startup=ws_startup,
    custom_shutdown=ws_shutdown
)
app.include_router(router)