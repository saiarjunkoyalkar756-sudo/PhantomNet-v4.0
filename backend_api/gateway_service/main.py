from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    Header,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime  # Import timedelta and datetime
import sys
from backend_api.shared.plugin_manager import PluginManager
import pyotp  # Ensure pyotp is imported for 2FA setup
from backend_api.shared.blue_team_ai import BlueTeamAI  # Import BlueTeamAI
from backend_api.shared.pnql_engine import PnqlEngine  # Import PnqlEngine
from backend_api.shared.attack_path_generator import (
    generate_simulated_attack_path,
    AttackPathGraph,
)  # Import Attack Path Generator
from backend_api.shared.osint_engine import (
    OsintEngine,
    OsintQuery,
    OsintResult,
)  # Import OSINT Engine components
from backend_api.shared.event_stream_processor import (
    EventStreamProcessor,
    RawEvent,
)  # Import EventStreamProcessor components
from backend_api.shared.dfir_toolkit import (
    DFIRToolkit,
    ForensicResult,
    MemoryDumpAnalysisRequest,
    DiskForensicsRequest,
    LogTimeliningRequest,
    MalwareSandboxRequest,
    YARAScanRequest,
)  # Import DFIR Toolkit components
from backend_api.shared.compliance_engine import (
    ComplianceEngine,
    ComplianceReport,
)  # Import Compliance Engine components
from backend_api.shared.bas_simulator import (
    BASSimulator,
    AttackScenario,
    SimulationResult,
)  # Import BAS Simulator components
from typing import (
    Optional,
    List,
    Dict,  # Added Dict for type hinting
    Any,   # Added Any for type hinting
)  # Import Optional for global type hints, List for OsintResult list
from backend_api.shared.telemetry_ingest import TelemetryIngestService, TelemetryIngestConfig # Import TelemetryIngestService

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
import json
import asyncio
import httpx
import logging # Import standard logging module
from backend_api.shared.logger_config import setup_logging, async_log_sink, log_queue, broadcast_logs_from_queue # Import shared logger setup and async_log_sink
from backend_api.shared.secret_manager import get_secret, generate_strong_secret # Import secret manager
from loguru import logger

# Configure logging at the very top
setup_logging(level="INFO")

# Secrets are now fetched when needed and will fail on startup if not set,
# removing the need for the check_insecure_defaults function.
JWT_SECRET_KEY = get_secret("JWT_SECRET_KEY")
DB_PASSWORD = get_secret("DB_PASSWORD")
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD")
logger.info("Security-critical secrets loaded from environment.")

from backend_api.shared.database import (
    User,
    SessionLocal,
    SessionToken,
    PasswordResetToken,
    AttackLog,
    BlacklistedIP,
    Block, # Import Block
    get_db, # Import get_db from database
)  # Import User, SessionLocal, create_db_and_tables, SessionToken, PasswordResetToken, AttackLog
from backend_api.shared.schemas import (
    UserCreate,
    UserInDB,
    Token,
    TokenData,
    PasswordResetRequest,
    PasswordResetConfirm,
    RecoveryCodeResponse,
    TwoFACode,
    TwoFAChallenge,
    MFARequiredResponse,
    SecurityAlert,
    Webhook,
    AttackSimulation,
    LoginRequest,
)

from pydantic import BaseModel, Field, field_validator  # Import BaseModel, Field, validator
import redis  # Import redis
from backend_api.gateway_service.websocket_manager import manager # Import the WebSocket manager
from backend_api.gateway_service.api_ecosystem import (
    router as api_ecosystem_router,
)  # Import api_ecosystem_router
from backend_api.gateway_service.admin import router as admin_router
from backend_api.gateway_service.agent_api import router as agent_router  # Import admin_router
from backend_api.gateway_service.orchestrator_api import router as orchestrator_router
from backend_api.iam_service.api import router as iam_router
from backend_api.blockchain_service.blockchain import Blockchain
from starlette.datastructures import URL  # Import URL
from uuid import uuid4  # Import uuid4
from backend_api.shared.email_service import send_reset_email  # Import send_reset_email
from backend_api.shared.health_monitor import monitor_health  # Import health monitor
from jose import jwt, JWTError  # Import jwt for token decoding in logout
from backend_api.gateway_service.routes.default import router as default_router
from backend_api.gateway_service.websocket_api import router as websocket_api_router # Import the new WebSocket API router
from backend_api.gateway_service.routes.health import router as health_router


from backend_api.shared.services import start_services, stop_services

from contextlib import asynccontextmanager

from backend_api.shared.audit_log import AUDIT_LOG_QUEUE
# from blockchain_layer.blockchain import BlockchainNotary

# --- Notarization Worker Configuration ---
NOTARIZATION_BATCH_SIZE = 10
NOTARIZATION_BATCH_TIMEOUT = 60  # seconds

# async def notarization_worker(db_session: Session):
#     """
#     A background worker that collects audit logs and commits them
#     to the blockchain notary service in batches.

#     **NOTE:** This blockchain interaction is currently conceptual and simulated.
#     It does NOT interact with a real, deployed blockchain network.
#     """
#     blockchain_notary = BlockchainNotary(db=db_session)
#     logger.info("Notarization worker started (conceptual blockchain).")
    
#     while True:
#         audit_batch = []
#         try:
#             # Wait for the first item with a timeout
#             first_item = await asyncio.wait_for(AUDIT_LOG_QUEUE.get(), timeout=NOTARIZATION_BATCH_TIMEOUT)
#             audit_batch.append(first_item)
            
#             # Gather more items up to the batch size without waiting long
#             while len(audit_batch) < NOTARIZATION_BATCH_SIZE:
#                 try:
#                     item = AUDIT_LOG_QUEUE.get_nowait()
#                     audit_batch.append(item)
#                 except asyncio.QueueEmpty:
#                     break # No more items in the queue, proceed with the current batch
            
#             if audit_batch:
#                 logger.info(f"Committing a batch of {len(audit_batch)} conceptual audit records to the blockchain (simulated)...")
#                 blockchain_notary.commit_audit_batch(audit_batch)
#                 logger.info("Audit batch successfully notarized (simulated).")
#                 for _ in audit_batch:
#                     AUDIT_LOG_QUEUE.task_done()

#         except asyncio.TimeoutError:
#             # This is normal, it just means the queue was empty for the timeout period.
#             # Continue the loop to wait for the next record.
#             continue
#         except Exception as e:
#             logger.error(f"Error in notarization worker (conceptual blockchain): {e}", exc_info=True)
#             # Avoid tight loop on persistent error
#             await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    db_session = SessionLocal()
    logging_task = asyncio.create_task(async_log_sink())
    log_broadcast_task = asyncio.create_task(broadcast_logs_from_queue(log_queue))
        # notarization_task = asyncio.create_task(notarization_worker(db_session)) # Start the new worker
    # logger.info("Asynchronous logging, broadcasting, and notarization tasks started (conceptual blockchain).")

    # create_db_and_tables("operational") # Removed: Use Alembic for schema management
    logger.info("Database tables will be managed by Alembic. Ensure migrations are applied.")
    asyncio.create_task(monitor_health())
    logger.info("Health monitoring started in background.")
    
    await manager.start_consumer()
    logger.info("WebSocket event consumer started.")

    # These services are now expected to be run independently
    # await threat_intel_startup()
    # logger.info("Threat Intelligence Service startup event executed.")
    
    # await siem_startup()
    # logger.info("SIEM Integration Service startup event executed.")
    
    # await soar_startup()
    # logger.info("SOAR Engine startup event executed.")
    
    yield

    # Shutdown logic
    # These services are now expected to be run independently
    # await threat_intel_shutdown()
    # logger.info("Threat Intelligence Service shutdown event executed.")

    # await siem_shutdown()
    # logger.info("SIEM Integration Service shutdown event executed.")

    # Cancel and await the background tasks to ensure graceful shutdown
    logging_task.cancel()
    log_broadcast_task.cancel()
        # notarization_task.cancel()
    try:
        await logging_task
    except asyncio.CancelledError:
        logger.info("Asynchronous logging task stopped.")
    try:
        await log_broadcast_task
    except asyncio.CancelledError:
        logger.info("Log broadcasting task stopped.")
        # try:
    #     await notarization_task
    # except asyncio.CancelledError:
    #     logger.info("Notarization worker task stopped (conceptual blockchain).")
    
    db_session.close()
    logger.info("Shutting down application.")


from shared.redis_client import redis_client

app = FastAPI(lifespan=lifespan)

# @app.middleware("http")
# async def zero_trust_middleware(request: Request, call_next):
#     # Whitelist certain paths from zero-trust checks
#     whitelisted_paths = ["/docs", "/openapi.json", "/login", "/health"]
#     if any(request.url.path.startswith(path) for path in whitelisted_paths):
#         return await call_next(request)
# 
#     try:
#         await zero_trust_manager.verify_request(request)
#         response = await call_next(request)
#         return response
#     except HTTPException as e:
#         return JSONResponse(
#             status_code=e.status_code,
#             content={"detail": e.detail}
#         )


# Initialize Redis client


class LogEntryData(BaseModel):
    ip: str = Field(..., description="IP address from the log entry")
    port: int = Field(..., ge=0, le=65535, description="Port from the log entry")
    data: str = Field(..., min_length=1, description="Raw log data")


class CopilotContext(BaseModel):
    user_role: str
    company_policy: str


class HoneypotControl(BaseModel):
    action: str = Field(..., description="Action to perform: 'start' or 'stop'")
    port: int = Field(..., ge=1, le=65535, description="Port number for the honeypot")


class SimulateAttack(BaseModel):
    ip: str = Field(..., description="IP address for simulation")
    port: int = Field(..., ge=1, le=65635, description="Port for simulation")
    data: str = Field(..., min_length=1, description="Raw data for simulation")

class TelemetryIngestData(BaseModel):
    agent_id: str
    tenant_id: str
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    agent_os: Optional[str] = None
    agent_capabilities: Optional[Dict[str, Any]] = None

# --- CONCEPTUAL BLOCKCHAIN INTEGRATION ---
# The blockchain notarization worker above is currently simulated.
# This function `write_merkle_root_to_contract` also represents a conceptual interaction
# with a blockchain smart contract. It does not perform actual on-chain transactions.
async def write_merkle_root_to_contract(merkle_root: str, block_index: int):
    logger.info(f"Writing Merkle root {merkle_root} for block {block_index} to smart contract (simulated).")
    # In a real scenario, this would interact with a blockchain smart contract
    return None

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],  # Allow frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT_THRESHOLD = 100  # requests
RATE_LIMIT_WINDOW = 60  # seconds

BAD_USER_AGENTS = [
    "sqlmap",
    "nmap",
    "nikto",
    "dirb",
    "wpscan",
    "masscan",
    "zgrab",
    "gobuster",
    "dirbuster",
    "hydra",
    "burpsuite",
]


@app.middleware("http")
async def blacklist_middleware(request: Request, call_next):
    ip = "127.0.0.1"
    if request.client:
        ip = request.client.host
    user_agent = request.headers.get("user-agent", "").lower()

    # Check for bad user agents
    for bad_agent in BAD_USER_AGENTS:
        if bad_agent in user_agent:
            logger.warning(
                f"Blocked request from blacklisted user agent: {user_agent} from IP: {ip}"
            )
            return JSONResponse(
                status_code=403, content={"detail": "User agent is blacklisted"}
            )

    db = SessionLocal()
    try:
        blacklisted_ip = (
            db.query(BlacklistedIP).filter(BlacklistedIP.ip_address == ip).first()
        )
    finally:
        db.close()
    if blacklisted_ip:
        logger.warning(f"Blocked request from blacklisted IP: {ip}")
        return JSONResponse(
            status_code=403, content={"detail": "IP address is blacklisted"}
        )
    response = await call_next(request)
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = "127.0.0.1"
    if request.client:
        ip = request.client.host
    key = f"rate_limit:{ip}"

    # Use a pipeline to execute commands atomically
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, RATE_LIMIT_WINDOW)
    request_count, _ = pipe.execute()

    if request_count > RATE_LIMIT_THRESHOLD:
        logger.warning(f"Rate limit exceeded for IP: {ip}")
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})

    response = await call_next(request)
    return response


# @app.middleware("http")
# async def csrf_middleware(request: Request, call_next):
#     if request.method in ["POST", "PUT", "DELETE"]:
#         csrf_token = request.headers.get("X-CSRF-Token")
#         # In a real implementation, you would validate this token against a server-generated one
#         # For now, we'll just check for its presence as a placeholder.
#         if not csrf_token:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")
CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "phantomnet_agent", "config.json"
)

app.include_router(api_ecosystem_router, tags=["Enterprise API"])

app.include_router(orchestrator_router, tags=["Orchestrator"])

app.include_router(admin_router, tags=["Admin"])

app.include_router(agent_router, tags=["Agents"])

app.include_router(iam_router)


app.include_router(iam_router)
app.include_router(health_router, tags=["Health"])



# from .analyzer.neural_threat_brain import get_qa_pipeline


# from phantomnet_agent.digital_twin import generator, deployer, models
# import yaml
# from phantomnet_agent.red_teaming.api import router as red_teaming_router

# app.include_router(red_teaming_router, prefix="/api", tags=["Red Teaming"]) # DISABLED - external module


















