from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Header, # Add Header here
)
from sqlalchemy.orm import Session
from typing import (
    Optional,
    List,
    Dict,  # Added Dict for type hinting
    Any,   # Added Any for type hinting
) # Import Optional for global type hints, List for OsintResult list
from pydantic import BaseModel, Field # Import BaseModel, Field
from datetime import datetime # Import datetime for utcnow
from datetime import datetime
import asyncio
from loguru import logger
import json
import os
import concurrent.futures

from backend_api.core_config import SAFE_MODE
import logging # Import standard logging module
from backend_api.shared.logger_config import setup_logging # Import shared logger setup

# --- Setup Logging ---
logger = setup_logging(name="gateway_agent_api", level="INFO")

from backend_api.shared.database import get_db, Agent, AgentCredential, SessionLocal
from backend_api.shared.schemas import (
    AgentRegistration,
    AgentHeartbeat,
    GossipMessage,
    BootstrapToken,
    SecurityEvent,
)
from cryptography.hazmat.primitives import serialization
from backend_api.shared.security_utils import (
    generate_key_pair,
    sign_certificate,
    create_inter_node_jwt,
    verify_inter_node_jwt,
    sign_data,
    verify_signature,
    generate_self_signed_ca,
)
from backend_api.shared.message_bus import message_bus
# from features.cognitive_core_intelligence.cognitive_core import CognitiveCore
# from features.synthetic_cognitive_memory.cognitive_memory import CognitiveMemory
import backend_api.shared.database as database

# Import EventStreamProcessor and PluginManager
from backend_api.shared.event_stream_processor import EventStreamProcessor
from backend_api.shared.plugin_manager import (
    PluginManager,
)  # Assuming plugin_manager.py exists

from backend_api.shared.telemetry_ingest import TelemetryIngestService, TelemetryIngestConfig
import httpx # Import httpx for sending heartbeats to telemetry-ingestor
from backend_api.iam_service.auth_methods import get_current_user, UserRole, has_role # Import to get current user and check roles
from backend_api.shared.database import User # Import User model for type hinting

# Conditional import for Kafka
if not SAFE_MODE:
    from kafka import KafkaProducer
else:
    # Define a dummy KafkaProducer if SAFE_MODE is enabled
    class KafkaProducer:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: KafkaProducer is a dummy object.")
        def send(self, *args, **kwargs):
            pass
        def flush(self):
            pass

router = APIRouter()

# --- Configuration for Telemetry Ingestor ---
TELEMETRY_INGESTOR_URL = os.getenv("TELEMETRY_INGESTOR_URL", "http://telemetry-ingestor:8000/ingest")

# Create a CognitiveMemory instance with a new DB session
# cognitive_memory_instance = CognitiveMemory(db_session=database.get_session_local("operational")())
# cognitive_core_instance = CognitiveCore(cognitive_memory=cognitive_memory_instance)

# Initialize PluginManager and MessageBus
plugin_manager = PluginManager()

# Mock CA key and cert for testing
ca_key, ca_cert = generate_self_signed_ca()


# Mock WebSocket Broadcaster for EventStreamProcessor (as it's usually managed elsewhere)
async def mock_websocket_broadcaster(data: dict):
    # In a real setup, this would send data to connected WebSocket clients
    logger.debug(f"Mock WebSocket Broadcast: {data}")
    await message_bus.publish("websocket_broadcasts", data)

# Initialize raw event queue for TelemetryIngestService
raw_event_queue_instance = asyncio.Queue()

# Initialize TelemetryIngestService
telemetry_ingest_config_instance = TelemetryIngestConfig()
telemetry_ingest_service_instance = TelemetryIngestService(raw_event_queue=raw_event_queue_instance, config=telemetry_ingest_config_instance)

# Initialize EventStreamProcessor
event_stream_processor = EventStreamProcessor(
    websocket_broadcaster=mock_websocket_broadcaster,
    plugin_manager=plugin_manager,
    db_session_generator=lambda: get_db("operational"),  # Pass the get_db function as the session generator
    telemetry_ingest_service=telemetry_ingest_service_instance,
    kafka_bootstrap_servers=telemetry_ingest_config_instance.kafka_bootstrap_servers,
    raw_telemetry_topic=telemetry_ingest_config_instance.raw_telemetry_topic,
    cassandra_contact_points=telemetry_ingest_config_instance.cassandra_contact_points,
    cassandra_keyspace=telemetry_ingest_config_instance.cassandra_keyspace,
)

# Initialize Kafka producer for agent status updates
try:
    agent_status_producer = KafkaProducer(bootstrap_servers="localhost:9092".split(','))
except Exception as e:
    logger.warning(f"Could not connect to Kafka, agent status updates will not be published: {e}")
    agent_status_producer = None

if not SAFE_MODE:
    agent_status_producer_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
else:
    agent_status_producer_executor = None

import secrets
import time

# ... (existing imports)

# In-memory store for bootstrap tokens. In a real-world scenario, use Redis or a database.
# Store as a dictionary: {token: expiration_timestamp}
bootstrap_tokens = {}


@router.post("/agents/bootstrap-token")
async def create_bootstrap_token(db: Session = Depends(lambda: get_db("operational"))):
    """
    Generates a single-use, time-expired bootstrap token for agent registration.
    """
    token = secrets.token_hex(32)
    # Token expires in 5 minutes
    expiration = time.time() + 300
    bootstrap_tokens[token] = expiration
    logger.info(f"Generated bootstrap token: {token}")
    return {"bootstrap_token": token, "expires_in": 300}


import hashlib
from cryptography import x509

# ... (existing code)


@router.post("/agents/register")
async def register_agent(agent_data: AgentRegistration, db: Session = Depends(lambda: get_db("operational"))):
    # ... (bootstrap token validation)

    # Generate key pair and store public key
    private_key_pem, public_key_pem = generate_key_pair()

    # Sign the agent's public key with our CA
    signed_cert_pem = sign_certificate(
        public_key_pem=public_key_pem,
        ca_private_key_pem=ca_key.decode("utf-8"),
        ca_certificate_pem=ca_cert.decode("utf-8"),
        common_name=f"agent-{agent_data.public_key[:10]}",
    )

    # Load the signed certificate to extract information
    signed_cert = x509.load_pem_x509_certificate(signed_cert_pem.encode("utf-8"))

    # Generate public key fingerprint
    public_key_bytes = signed_cert.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    fingerprint = hashlib.sha256(public_key_bytes).hexdigest()

    new_agent = Agent(
        public_key=public_key_pem,
        public_key_fingerprint=fingerprint,
        cert_serial=str(signed_cert.serial_number),
        role=agent_data.role,
        version=agent_data.version,
        location=agent_data.location,
        status="online",
        last_seen=datetime.utcnow(),
        quarantined=True,  # New agents are quarantined by default
        configuration=agent_data.configuration.model_dump_json() if agent_data.configuration else None, # Store initial configuration
        os=agent_data.os, # Store agent's OS
        capabilities=json.dumps(agent_data.capabilities) if agent_data.capabilities else None, # Store agent's capabilities
        self_healing_enabled=agent_data.self_healing_enabled,
        safe_mode_active=agent_data.safe_mode_active,
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)

    agent_credential = AgentCredential(
        agent_id=new_agent.id, public_key_pem=public_key_pem
    )
    db.add(agent_credential)
    db.commit()
    db.refresh(agent_credential)

    logger.info(
        "Agent registered successfully",
        agent_id=new_agent.id,
        role=new_agent.role,
        location=new_agent.location,
        os=agent_data.os,
        capabilities=agent_data.capabilities,
        self_healing_enabled=agent_data.self_healing_enabled,
        safe_mode_active=agent_data.safe_mode_active
    )
    # Return the signed certificate to the agent
    return {"agent": new_agent, "certificate": signed_cert_pem}


from backend_api.shared.crl_utils import is_certificate_revoked, revoke_certificate
from backend_api.shared.schemas import AgentConfiguration # Import AgentConfiguration
from pydantic import BaseModel # Import BaseModel

# ... (existing code)


@router.post("/agents/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: int, 
    heartbeat: AgentHeartbeat, 
    current_user: User = Depends(has_role([UserRole.ADMIN, UserRole.ANALYST])), # RBAC applied
    db: Session = Depends(lambda: get_db("operational"))
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning("Agent heartbeat failed: Agent not found", agent_id=agent_id)
        raise HTTPException(status_code=404, detail="Agent not found")

    # Ensure agent belongs to the current user's tenant
    if agent.tenant_id != current_user.tenant_id:
        logger.warning(
            f"Unauthorized heartbeat attempt for agent {agent_id} by user from tenant {current_user.tenant_id}.",
            extra={"agent_id": agent_id, "user_tenant_id": current_user.tenant_id, "agent_tenant_id": agent.tenant_id}
        )
        raise HTTPException(status_code=403, detail="Agent does not belong to your tenant.")

    # CRL Check
    if is_certificate_revoked(db, agent.cert_serial):
        logger.warning(
            "Agent heartbeat denied: Certificate has been revoked",
            agent_id=agent_id,
            cert_serial=agent.cert_serial,
        )
        raise HTTPException(status_code=403, detail="Certificate has been revoked")

    agent.status = heartbeat.status
    agent.last_seen = datetime.utcnow()
    # Update agent OS and capabilities from heartbeat if provided
    if heartbeat.os:
        agent.os = heartbeat.os
    if heartbeat.capabilities:
        agent.capabilities = json.dumps(heartbeat.capabilities)
    if heartbeat.health_metrics:
        agent.last_reported_health = json.dumps(heartbeat.health_metrics)
    if heartbeat.recent_errors:
        agent.last_reported_errors = json.dumps(heartbeat.recent_errors)
    if heartbeat.self_healing_active is not None:
        agent.self_healing_enabled = heartbeat.self_healing_active
    if heartbeat.safe_mode_active is not None:
        agent.safe_mode_active = heartbeat.safe_mode_active
    db.commit()

    # --- Send heartbeat data to Telemetry Ingestor ---
    try:
        telemetry_event_data = heartbeat.model_dump()
        
        # Directly use telemetry_ingest_service_instance instead of HTTP POST
        await telemetry_ingest_service_instance.ingest_raw_log(
            log_entry=telemetry_event_data,
            source="agent_heartbeat",
            agent_id=str(agent.id),
            agent_os=agent.os,
            agent_capabilities=agent.capabilities, # Pass stored capabilities
            # New self-healing fields
            agent_self_healing_active=heartbeat.self_healing_active,
            agent_safe_mode_active=heartbeat.safe_mode_active
        )
        logger.info(f"Agent {agent.id} heartbeat sent to Telemetry Ingestor.", extra={"agent_id": agent.id, "tenant_id": str(agent.tenant_id)})
    except Exception as e:
        logger.error(f"Error ingesting agent heartbeat directly: {e}", exc_info=True)

    # ... (rest of the function)


@router.get("/agents/{agent_id}/config", response_model=AgentConfiguration)
async def get_agent_config(agent_id: int, db: Session = Depends(lambda: get_db("operational"))):
    """
    Allows an agent to pull its specific configuration from the Agent Manager.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.configuration:
        # Return a default configuration if none is set
        return AgentConfiguration() 
    
    try:
        return AgentConfiguration.model_validate_json(agent.configuration)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding agent {agent_id} configuration: {e}")
        raise HTTPException(status_code=500, detail="Invalid agent configuration stored.")

@router.post("/agents/{agent_id}/revoke-certificate")
async def revoke_agent_certificate(agent_id: int, db: Session = Depends(lambda: get_db("operational"))):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    revoke_certificate(
        db, agent.cert_serial, reason="Manual revocation by administrator"
    )
    logger.info(f"Certificate for agent {agent_id} has been revoked.")
    return {"message": "Certificate revoked successfully."}


@router.get("/agents")
async def get_agents(db: Session = Depends(lambda: get_db("operational"))):
    agents = db.query(Agent).all()
    return agents


class AgentStatusSummary(BaseModel):
    total_agents: int
    online_agents: int
    offline_agents: int
    quarantined_agents: int
    active_threats_agents: int # Placeholder for agents reporting active threats


@router.get("/agents/status/summary", response_model=AgentStatusSummary)
async def get_agent_status_summary(db: Session = Depends(lambda: get_db("operational"))):
    """
    Retrieves a summary of the status of all registered agents.
    """
    total_agents = db.query(Agent).count()
    online_agents = db.query(Agent).filter(Agent.status == "online").count()
    offline_agents = db.query(Agent).filter(Agent.status == "offline").count()
    quarantined_agents = db.query(Agent).filter(Agent.quarantined == True).count()
    
    # Placeholder for active threats agents - in a real scenario, this might involve
    # querying the alerts database or having a specific agent status for threats.
    active_threats_agents = 0 

    return AgentStatusSummary(
        total_agents=total_agents,
        online_agents=online_agents,
        offline_agents=offline_agents,
        quarantined_agents=quarantined_agents,
        active_threats_agents=active_threats_agents,
    )


@router.post("/agents/{agent_id}/gossip")
async def agent_gossip(
    agent_id: int, gossip: GossipMessage, db: Session = Depends(lambda: get_db("operational"))
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning("Agent gossip failed: Agent not found", agent_id=agent_id)
        raise HTTPException(status_code=404, detail="Agent not found")

        # In a real implementation, you would implement a gossip protocol to propagate and average trust scores.
        # For now, we'll just log the received trust map.
        logger.info(
            "Received gossip from agent", agent_id=agent_id, trust_map=gossip.trust_map
        )
        # Metrics: Increment agent_gossip_received_total
        return {"message": "Gossip received"}


@router.post("/agents/{agent_id}/rotate-key")
async def rotate_agent_key(agent_id: int, db: Session = Depends(lambda: get_db("operational"))):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning("Agent key rotation failed: Agent not found", agent_id=agent_id)
        raise HTTPException(status_code=404, detail="Agent not found")

    # Generate new key pair
    private_key_pem, public_key_pem = generate_key_pair()

    # Mark old credential as rotated
    old_credential = (
        db.query(AgentCredential)
        .filter(
            AgentCredential.agent_id == agent_id, AgentCredential.revoked_at == None
        )
        .first()
    )
    if old_credential:
        old_credential.rotated_at = datetime.utcnow()
        db.add(old_credential)

    # Create new credential
    new_credential = AgentCredential(
        agent_id=agent.id, public_key_pem=public_key_pem, created_at=datetime.utcnow()
    )
    db.add(new_credential)

    # Simulate certificate signing for the new public key
    dummy_ca_private_key = "-----BEGIN PRIVATE KEY-----\n...DUMMY_CA_PRIVATE_KEY...\n-----END PRIVATE KEY-----"
    dummy_ca_certificate = "-----BEGIN CERTIFICATE-----\n...DUMMY_CA_CERTIFICATE...\n-----END CERTIFICATE-----"

    signed_cert = sign_certificate(
        public_key_pem=public_key_pem,
        ca_private_key_pem=dummy_ca_private_key,
        ca_certificate_pem=dummy_ca_certificate,
        common_name=f"agent-{agent.public_key[:10]}-rotated",  # New common name for rotated key
    )
    agent.public_key = public_key_pem  # Update agent's public key
    agent.public_key_fingerprint = "DUMMY_FINGERPRINT_ROTATED"  # Placeholder
    agent.cert_serial = "DUMMY_CERT_SERIAL_ROTATED"  # Placeholder
    db.add(agent)

    db.commit()
    db.refresh(agent)
    db.refresh(new_credential)

    logger.info("Agent key rotated successfully", agent_id=agent.id)
    # Metrics: Increment agent_key_rotation_success_total
    # Audit: Record cert.rotated event
    return {"message": "Key rotated successfully"}


@router.post("/agents/{agent_id}/approve")
async def approve_agent(agent_id: int, db: Session = Depends(lambda: get_db("operational"))):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        logger.warning("Agent approval failed: Agent not found", agent_id=agent_id)
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.quarantined = False
    db.add(agent)
    db.commit()
    db.refresh(agent)

    logger.info("Agent approved successfully", agent_id=agent.id)
    # Audit: Record agent.approved event
    return {"message": "Agent approved successfully"}

# --- New Endpoints for Self-Healing AI Layer ---

class RegisterIssueRequest(BaseModel):
    agent_id: str
    error_fingerprint: str
    error_details: Dict[str, Any]
    classified_severity: str
    root_cause_prediction: str
    fix_suggestion: List[str]

@router.post("/ai/self_healing/register_issue")
async def register_issue(request: RegisterIssueRequest, db: Session = Depends(lambda: get_db("operational"))):
    """
    Endpoint for agents to register detected issues with the backend.
    """
    # In a real system, this would store the issue in a dedicated issues/error DB
    # For now, we'll append to the agent's recent_errors in the agent table.
    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    current_errors = json.loads(agent.last_reported_errors or "[]")
    current_errors.append({
        "timestamp": datetime.utcnow().isoformat(),
        "fingerprint": request.error_fingerprint,
        "details": request.error_details,
        "severity": request.classified_severity,
        "root_cause": request.root_cause_prediction,
        "suggestion": request.fix_suggestion,
        "status": "detected"
    })
    agent.last_reported_errors = json.dumps(current_errors)
    db.commit()
    logger.info(f"Issue registered for agent {request.agent_id}: {request.error_fingerprint}")
    return {"status": "success", "message": "Issue registered."}

class ReportFixRequest(BaseModel):
    agent_id: str
    error_fingerprint: str
    fix_attempted: str
    fix_success: bool
    fix_log: str

@router.post("/ai/self_healing/report_fix")
async def report_fix(request: ReportFixRequest, db: Session = Depends(lambda: get_db("operational"))):
    """
    Endpoint for agents to report on fix attempts.
    """
    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    current_errors = json.loads(agent.last_reported_errors or "[]")
    # Find the error and update its status
    for error in current_errors:
        if error.get("fingerprint") == request.error_fingerprint and error.get("status") == "detected":
            error["status"] = "fixed" if request.fix_success else "fix_failed"
            error["fix_attempted"] = request.fix_attempted
            error["fix_log"] = request.fix_log
            error["fixed_at"] = datetime.utcnow().isoformat()
            break
    agent.last_reported_errors = json.dumps(current_errors)
    db.commit()
    logger.info(f"Fix reported for agent {request.agent_id}: {request.error_fingerprint} - Success: {request.fix_success}")
    return {"status": "success", "message": "Fix reported."}

@router.get("/ai/self_healing/get_patch")
async def get_patch(agent_id: str, current_version: str, db: Session = Depends(lambda: get_db("operational"))):
    """
    Endpoint for agents to request available patches.
    """
    # In a real system, this would query a patch management system.
    # For now, simulate patch availability.
    # Check if a patch is available for this agent_id/version
    if agent_id == "test-agent-123" and current_version == "0.0.1":
        patch_info = {
            "id": "patch-001",
            "url": "http://example.com/patches/patch-001.zip", # URL to download patch
            "hash": "a1b2c3d4e5f6...", # SHA256 hash of the patch file
            "version": "0.0.2",
            "description": "Fixes critical import error in telemetry module."
        }
        return {"status": "available", "patch": patch_info}
    return {"status": "no_patch_available", "message": "No new patches available."}

@router.post("/agent/health/live")
async def post_agent_live_health(
    agent_id: str, 
    health_data: Dict[str, Any], 
    db: Session = Depends(lambda: get_db("operational"))
):
    """
    Endpoint for agents to report detailed live health metrics, beyond heartbeats.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.last_reported_health = json.dumps(health_data)
    db.commit()
    logger.debug(f"Agent {agent_id} live health reported.")
    return {"status": "success", "message": "Live health reported."}

# --- End New Endpoints ---

@router.post("/analyze-threat")
async def analyze_threat_endpoint(threat_data: dict):
    """
    Endpoint to analyze threat data using the Cognitive Core.
    Expects a JSON body with a "threat_string" key.
    """
    threat_string = threat_data.get("threat_string")
    if not threat_string:
        raise HTTPException(
            status_code=400, detail="'threat_string' not provided in request body"
        )

    # analysis_result = cognitive_core_instance.analyze_threat(threat_string)
    return {"detail": "Cognitive threat analysis is currently disabled."}


@router.post("/api/v1/logs/ingest")
async def ingest_logs_http(
    request: Request,
    source: str = "http_collector",
    agent_id: Optional[str] = Header(None),
    agent_os: Optional[str] = Header(None),
    agent_capabilities: Optional[str] = Header(None) # JSON string of capabilities
):
    """
    Universal HTTP endpoint for ingesting raw log data.
    Accepts any payload and passes it to the event stream processor.
    The 'source' parameter can be used to identify the log origin (e.g., 'nginx', 'syslog', 'filebeat').
    Agent ID, OS, and capabilities can optionally be passed via headers.
    """
    try:
        # Attempt to read as JSON first, if not, read as plain text
        try:
            log_data = await request.json()
        except json.JSONDecodeError:
            log_data = await request.body()
            log_data = log_data.decode("utf-8")  # Decode bytes to string
        
        parsed_agent_capabilities = None
        if agent_capabilities:
            try:
                parsed_agent_capabilities = json.loads(agent_capabilities)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse agent_capabilities header: {agent_capabilities}")

        await event_stream_processor.ingest_raw_log(
            log_entry=log_data,
            source=source,
            agent_id=agent_id,
            agent_os=agent_os,
            agent_capabilities=parsed_agent_capabilities
        )
        logger.info(f"Successfully ingested log via HTTP from source: {source} (Agent ID: {agent_id})")
        return {"status": "success", "message": "Log ingested successfully"}
    except Exception as e:
        logger.error(f"Error ingesting log via HTTP from source: {source} (Agent ID: {agent_id}) - {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest log: {e}")


@router.websocket("/ws/agent-events")
async def websocket_agent_events(websocket: WebSocket):
    await websocket.accept()
    pubsub = message_bus.subscribe("agent-events")

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                jwt_token = data.get("jwt")
                event_data = data.get("data")

                if jwt_token:
                    try:
                        # In a real scenario, you would retrieve the public key of the sending agent
                        # from the database based on the 'iss' claim in the JWT.
                        # For now, we'll use a dummy public key for verification.
                        dummy_public_key = "-----BEGIN PUBLIC KEY-----\n...DUMMY_PUBLIC_KEY...\n-----END PUBLIC KEY-----"

                        verified_payload = verify_inter_node_jwt(
                            jwt_token, dummy_public_key, "default_cluster"
                        )
                        logger.info(
                            "JWT verified successfully", payload=verified_payload
                        )
                        # Metrics: Increment jwt_verification_success_total

                        # Verify agent's signature on event data
                        agent_signature = event_data.get("agent_signature")
                        heartbeat_data = {
                            "agent_id": event_data.get("agent_id"),
                            "status": event_data.get("status"),
                        }
                        heartbeat_data_bytes = json.dumps(heartbeat_data).encode(
                            "utf-8"
                        )

                        if agent_signature and verify_signature(
                            heartbeat_data_bytes, agent_signature, dummy_public_key
                        ):
                            logger.info("Agent signature verified successfully")
                            # Attest the event (sign with receiving node's private key)
                            # For now, use a dummy private key for attestation
                            dummy_private_key = "-----BEGIN PRIVATE KEY-----\n...DUMMY_PRIVATE_KEY...\n-----END PRIVATE KEY-----"
                            node_attestation = sign_data(
                                heartbeat_data_bytes, dummy_private_key
                            )
                            event_data["node_attestation"] = node_attestation
                            event_data["receiving_node_id"] = 1  # Dummy node ID
                            await websocket.send_text(json.dumps(event_data))
                        else:
                            logger.warning(
                                "Agent signature verification failed or missing",
                                agent_id=event_data.get("agent_id"),
                            )

                    except HTTPException as e:
                        logger.error("JWT verification failed", error=e.detail)
                        # Metrics: Increment jwt_verification_failure_total (by reason)
                        # Audit: Record jwt.verify_failed event
                    except Exception as e:
                        logger.error("Error during JWT verification", error=str(e))
                        # Metrics: Increment jwt_verification_failure_total (by reason)
                        # Audit: Record jwt.verify_failed event
                else:
                    logger.warning("Message received without JWT", data=event_data)
                    await websocket.send_text(json.dumps(event_data))
            await asyncio.sleep(0.1)  # Prevent busy-waiting
    except WebSocketDisconnect:
        pubsub.close()
