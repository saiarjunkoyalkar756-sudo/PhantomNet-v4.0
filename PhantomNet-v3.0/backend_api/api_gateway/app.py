from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from datetime import timedelta, datetime # Import timedelta and datetime
import sys
from backend_api.plugin_manager import PluginManager
import pyotp # Ensure pyotp is imported for 2FA setup
from backend_api.blue_team_ai import BlueTeamAI # Import BlueTeamAI
from backend_api.pnql_engine import PnqlEngine # Import PnqlEngine
from backend_api.attack_path_generator import generate_simulated_attack_path, AttackPathGraph # Import Attack Path Generator
from backend_api.osint_engine import OsintEngine, OsintQuery, OsintResult # Import OSINT Engine components
from backend_api.event_stream_processor import EventStreamProcessor, RawEvent # Import EventStreamProcessor components
from backend_api.dfir_toolkit import DFIRToolkit, ForensicResult, MemoryDumpAnalysisRequest, DiskForensicsRequest, LogTimeliningRequest, MalwareSandboxRequest, YARAScanRequest # Import DFIR Toolkit components
from backend_api.compliance_engine import ComplianceEngine, ComplianceReport # Import Compliance Engine components
from backend_api.bas_simulator import BASSimulator, AttackScenario, SimulationResult # Import BAS Simulator components
from typing import Optional, List # Import Optional for global type hints, List for OsintResult list

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
import json
import asyncio
import httpx
import logging
from loguru import logger # Import loguru logger

# Configure logging
logger.remove() # Remove default logger
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO") # Add basic console logger
logger.add("file.log", rotation="10 MB", compression="zip", serialize=True) # Add file logger with JSON serialization
logger.add("behavioral_data.log", rotation="10 MB", compression="zip", serialize=True, filter=lambda record: "behavioral_data" in record["extra"]) # Add behavioral data logger
logger.info(f"JWT_SECRET_KEY from .env: {os.getenv('JWT_SECRET_KEY')}")

from backend_api.database import User, SessionLocal, create_db_and_tables, SessionToken, PasswordResetToken, AttackLog, BlacklistedIP # Import User, SessionLocal, create_db_and_tables, SessionToken, PasswordResetToken, AttackLog
from backend_api.schemas import UserCreate, UserInDB, Token, TokenData, PasswordResetRequest, PasswordResetConfirm, RecoveryCodeResponse, TwoFACode, TwoFAChallenge, MFARequiredResponse, SecurityAlert, Webhook, AttackSimulation, LoginRequest
# from backend_api.analyzer.neural_threat_brain import brain
from backend_api.auth import ( # Import auth functions
    generate_totp_secret,
    verify_totp_code,
    authenticate_user,
    get_current_user,
    get_password_hash,
    create_access_token,
    get_user,
    UserRole,
    has_role,
    SECRET_KEY, # Import SECRET_KEY
    ALGORITHM, # Import ALGORITHM
    generate_recovery_code,
    hash_recovery_code,
    verify_recovery_code,
    RECOVERY_CODE_COUNT, # Import RECOVERY_CODE_COUNT
    calculate_anomaly_score # Import calculate_anomaly_score
)
from pydantic import BaseModel, Field, validator # Import BaseModel, Field, validator
import redis # Import redis
from backend_api.api_gateway.api_ecosystem import router as api_ecosystem_router # Import api_ecosystem_router
from backend_api.admin import router as admin_router
from backend_api.agent_api import router as agent_router # Import admin_router
from backend_api.orchestrator_api import router as orchestrator_router
from backend_api.blockchain_service.blockchain import Blockchain
from starlette.datastructures import URL # Import URL
from uuid import uuid4 # Import uuid4
from backend_api.email_service import send_reset_email # Import send_reset_email
from backend_api.health_monitor import monitor_health # Import health monitor
from jose import jwt, JWTError # Import jwt for token decoding in logout


# Configure logging
logger.remove() # Remove default logger
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO") # Add basic console logger
logger.add("file.log", rotation="10 MB", compression="zip", serialize=True) # Add file logger with JSON serialization
logger.add("behavioral_data.log", rotation="10 MB", compression="zip", serialize=True, filter=lambda record: "behavioral_data" in record["extra"]) # Add behavioral data logger

app = FastAPI()

# Initialize PluginManager globally
plugin_manager = PluginManager()
blue_team_ai: Optional[BlueTeamAI] = None # Declare blue_team_ai globally
pnql_engine: Optional[PnqlEngine] = None # Declare pnql_engine globally
osint_engine: Optional[OsintEngine] = None # Declare osint_engine globally
event_stream_processor: Optional[EventStreamProcessor] = None # Declare event_stream_processor globally
dfir_toolkit: Optional[DFIRToolkit] = None # Declare dfir_toolkit globally
compliance_engine: Optional[ComplianceEngine] = None # Declare compliance_engine globally
bas_simulator: Optional[BASSimulator] = None # Declare bas_simulator globally


@app.exception_handler(Exception)


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get the PluginManager
def get_plugin_manager():
    return plugin_manager

# Dependency to get the PnqlEngine
def get_pnql_engine():
    if pnql_engine is None:
        raise HTTPException(status_code=500, detail="PNQL Engine not initialized.")
    return pnql_engine

# Dependency to get the OsintEngine
def get_osint_engine():
    if osint_engine is None:
        raise HTTPException(status_code=500, detail="OSINT Engine not initialized.")
    return osint_engine

# Dependency to get the EventStreamProcessor
def get_event_stream_processor():
    if event_stream_processor is None:
        raise HTTPException(status_code=500, detail="Event Stream Processor not initialized.")
    return event_stream_processor

# Dependency to get the DFIRToolkit
def get_dfir_toolkit():
    if dfir_toolkit is None:
        raise HTTPException(status_code=500, detail="DFIR Toolkit not initialized.")
    return dfir_toolkit

# Dependency to get the ComplianceEngine
def get_compliance_engine():
    if compliance_engine is None:
        raise HTTPException(status_code=500, detail="Compliance Engine not initialized.")
    return compliance_engine

# Dependency to get the BASSimulator
def get_bas_simulator():
    if bas_simulator is None:
        raise HTTPException(status_code=500, detail="BAS Simulator not initialized.")
    return bas_simulator


# New routes for plugin management
@app.get("/plugins", tags=["Plugins"])
async def list_plugins(plugin_mgr: PluginManager = Depends(get_plugin_manager)):
    # Return a list of available plugins with their manifest info and status
    return {name: {"manifest": p["manifest"], "status": p["status"]} for name, p in plugin_mgr.available_plugins.items()}


class PluginExecuteRequest(BaseModel):
    function_name: str
    args: list = []
    kwargs: dict = {}

@app.post("/plugins/{plugin_name}/execute", tags=["Plugins"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def execute_plugin(
    plugin_name: str,
    request_data: PluginExecuteRequest,
    plugin_mgr: PluginManager = Depends(get_plugin_manager),
    current_user: User = Depends(get_current_user) # To ensure user is authenticated
):
    # First, ensure the plugin is loaded (or attempt to load it)
    if not plugin_mgr.available_plugins.get(plugin_name):
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found.")
    
    # Attempt to load the plugin if not already loaded.
    # The load_plugin method now just updates status, actual load is in sandbox.
    if plugin_mgr.available_plugins[plugin_name]["status"] != "loaded":
        load_success = plugin_mgr.load_plugin(plugin_name)
        if not load_success:
            raise HTTPException(status_code=500, detail=f"Failed to prepare plugin '{plugin_name}' for execution.")

    logger.info(f"User {current_user.username} (ID: {current_user.id}) executing plugin '{plugin_name}' function '{request_data.function_name}'")
    
    result = plugin_mgr.execute_plugin_function(
        plugin_name,
        request_data.function_name,
        *request_data.args,
        **request_data.kwargs
    )
    
    if result and "error" in result:
        logger.error(f"Plugin execution failed for '{plugin_name}' function '{request_data.function_name}': {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

class PNQLQueryRequest(BaseModel):
    query: str

@app.post("/pnql/query", tags=["PNQL"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def execute_pnql_query(
    request_data: PNQLQueryRequest,
    pnql_engine_dep: PnqlEngine = Depends(get_pnql_engine),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) executing PNQL query: '{request_data.query}'")
    result = pnql_engine_dep.execute_query(request_data.query)
    if result and isinstance(result, list) and len(result) > 0 and "error" in result[0]:
        logger.error(f"PNQL query failed: {result[0]['error']}")
        raise HTTPException(status_code=400, detail=result[0]["error"])
    return result

@app.get("/attack-path/generate", response_model=AttackPathGraph, tags=["AI Attack Path"])
async def get_attack_path(current_user: User = Depends(get_current_user), depth: int = 3):
    """
    Generates a simulated AI-driven attack path.
    """
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting simulated attack path with depth {depth}.")
    path_graph = generate_simulated_attack_path(depth=depth)
    return path_graph

@app.post("/osint/query", response_model=List[OsintResult], tags=["OSINT"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def execute_osint_query_api(
    query: OsintQuery,
    osint_engine_dep: OsintEngine = Depends(get_osint_engine),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) executing OSINT query for target '{query.target}' with sources {query.sources}.")
    results = await osint_engine_dep.execute_osint_query(query)
    return results

@app.get("/osint/{target}/results", response_model=List[OsintResult], tags=["OSINT"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def get_osint_results_api(
    target: str,
    osint_engine_dep: OsintEngine = Depends(get_osint_engine),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting recent OSINT results for target '{target}'.")
    results = osint_engine_dep.get_recent_osint_results(target)
    if results is None:
        raise HTTPException(status_code=404, detail=f"No recent OSINT results found for target '{target}'.")
    return results

@app.post("/events/ingest", status_code=status.HTTP_202_ACCEPTED, tags=["Events"])
async def ingest_event_api(
    event: RawEvent,
    event_processor: EventStreamProcessor = Depends(get_event_stream_processor),
    current_user: User = Depends(get_current_user) # To ensure user is authenticated
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) ingesting event: {event.id} from {event.source}")
    await event_processor.ingest_event(event)
    return {"message": "Event ingested successfully."}

@app.post("/dfir/memory-dump-analysis", response_model=ForensicResult, tags=["DFIR"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def memory_dump_analysis_api(
    request_data: MemoryDumpAnalysisRequest,
    dfir_toolkit_dep: DFIRToolkit = Depends(get_dfir_toolkit),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting memory dump analysis for {request_data.dump_path}.")
    result = await dfir_toolkit_dep.analyze_memory_dump(request_data)
    return result

@app.post("/dfir/disk-forensics", response_model=ForensicResult, tags=["DFIR"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def disk_forensics_api(
    request_data: DiskForensicsRequest,
    dfir_toolkit_dep: DFIRToolkit = Depends(get_dfir_toolkit),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting disk forensics for {request_data.image_path}.")
    result = await dfir_toolkit_dep.perform_disk_forensics(request_data)
    return result

@app.post("/dfir/log-timelining", response_model=ForensicResult, tags=["DFIR"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def log_timelining_api(
    request_data: LogTimeliningRequest,
    dfir_toolkit_dep: DFIRToolkit = Depends(get_dfir_toolkit),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting log timelining for {len(request_data.log_paths)} files.")
    result = await dfir_toolkit_dep.create_log_timeline(request_data)
    return result

@app.post("/dfir/malware-sandbox", response_model=ForensicResult, tags=["DFIR"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def malware_sandbox_api(
    request_data: MalwareSandboxRequest,
    dfir_toolkit_dep: DFIRToolkit = Depends(get_dfir_toolkit),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting malware sandboxing for {request_data.file_path}.")
    result = await dfir_toolkit_dep.sandbox_malware(request_data)
    return result

@app.post("/dfir/yara-scan", response_model=ForensicResult, tags=["DFIR"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def yara_scan_api(
    request_data: YARAScanRequest,
    dfir_toolkit_dep: DFIRToolkit = Depends(get_dfir_toolkit),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting YARA scan for {len(request_data.scan_paths)} paths.")
    result = await dfir_toolkit_dep.run_yara_scan(request_data)
    return result

@app.get("/dfir/operations/{operation_id}/status", response_model=ForensicResult, tags=["DFIR"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def get_dfir_operation_status_api(
    operation_id: str,
    dfir_toolkit_dep: DFIRToolkit = Depends(get_dfir_toolkit),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting status for DFIR operation {operation_id}.")
    result = dfir_toolkit_dep.get_operation_status(operation_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"DFIR operation {operation_id} not found.")
    return result

@app.post("/compliance/scan/{standard}", response_model=ComplianceReport, tags=["Compliance"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def compliance_scan_api(
    standard: str,
    compliance_engine_dep: ComplianceEngine = Depends(get_compliance_engine),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting compliance scan for standard {standard}.")
    report = await compliance_engine_dep.run_compliance_scan(standard)
    return report

@app.get("/compliance/reports/{report_id}", response_model=ComplianceReport, tags=["Compliance"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def get_compliance_report_api(
    report_id: str,
    compliance_engine_dep: ComplianceEngine = Depends(get_compliance_engine),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting compliance report {report_id}.")
    report = compliance_engine_dep.get_compliance_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Compliance report {report_id} not found.")
    return report

@app.get("/compliance/reports", response_model=List[ComplianceReport], tags=["Compliance"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def get_all_compliance_reports_api(
    compliance_engine_dep: ComplianceEngine = Depends(get_compliance_engine),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting all compliance reports.")
    reports = compliance_engine_dep.get_all_reports()
    return reports

@app.post("/bas/simulate", response_model=SimulationResult, tags=["BAS"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def bas_simulate_api(
    scenario: AttackScenario,
    bas_simulator_dep: BASSimulator = Depends(get_bas_simulator),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting BAS simulation for scenario {scenario.name}.")
    result = await bas_simulator_dep.run_simulation(scenario)
    return result

@app.get("/bas/simulations/{simulation_id}/results", response_model=SimulationResult, tags=["BAS"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def get_bas_simulation_results_api(
    simulation_id: str,
    bas_simulator_dep: BASSimulator = Depends(get_bas_simulator),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting BAS simulation results for {simulation_id}.")
    result = bas_simulator_dep.get_simulation_result(simulation_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found.")
    return result

@app.get("/bas/simulations", response_model=List[SimulationResult], tags=["BAS"], dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def get_all_bas_simulations_api(
    bas_simulator_dep: BASSimulator = Depends(get_bas_simulator),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"User {current_user.username} (ID: {current_user.id}) requesting all BAS simulations.")
    results = bas_simulator_dep.get_all_simulations()
    return results

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    global blue_team_ai
    global pnql_engine # Declare pnql_engine as global to modify it
    global osint_engine # Declare osint_engine as global to modify it
    global event_stream_processor # Declare event_stream_processor as global to modify it
    global dfir_toolkit # Declare dfir_toolkit as global to modify it
    global compliance_engine # Declare compliance_engine as global to modify it
    global bas_simulator # Declare bas_simulator as global to modify it

    create_db_and_tables()
    logger.info("Database tables created/checked.") # Log startup event
    # Start the health monitoring in the background
    asyncio.create_task(monitor_health())
    logger.info("Health monitoring started in background.")
    
    # Discover plugins at startup
    plugin_manager.discover_plugins()
    logger.info(f"Discovered {len(plugin_manager.available_plugins)} plugins.")

    # Initialize and start BlueTeamAI
    blue_team_ai = BlueTeamAI(plugin_manager)
    asyncio.create_task(blue_team_ai.run_defense_cycle())
    logger.info("Autonomous Blue Team AI defense cycle started in background.")

    # Initialize OSINT Engine
    osint_engine = OsintEngine()
    logger.info("OSINT Engine initialized.")

    # Initialize Event Stream Processor
    # The broadcast_event function is defined globally in app.py
    event_stream_processor = EventStreamProcessor(websocket_broadcaster=broadcast_event, plugin_manager=plugin_manager)
    asyncio.create_task(event_stream_processor.start())
    logger.info("Event Stream Processor initialized and started.")

    # Initialize DFIR Toolkit
    dfir_toolkit = DFIRToolkit()
    logger.info("DFIR Toolkit initialized.")

    # Initialize Compliance Engine
    compliance_engine = ComplianceEngine()
    logger.info("Compliance Engine initialized.")

    # Initialize BAS Simulator
    bas_simulator = BASSimulator()
    logger.info("BAS Simulator initialized.")

    # Initialize PNQL Engine
    # Define data sources for PNQL
    def get_logs_pnql():
        # Query the actual logs database
        db = SessionLocal()
        try:
            logs = db.query(AttackLog).order_by(AttackLog.timestamp.desc()).all()
            logger.info(f"PNQL: Retrieved {len(logs)} logs from AttackLog table.")
            return [{
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "ip": log.ip,
                "port": log.port,
                "data": log.data,
                "attack_type": log.attack_type,
                "confidence_score": log.confidence_score,
                "is_anomaly": log.is_anomaly,
                "anomaly_score": log.anomaly_score,
                "is_verified_threat": log.is_verified_threat,
                "is_blacklisted": log.is_blacklisted
            } for log in logs]
        finally:
            db.close()

    def get_threats_pnql():
        # TODO: Implement actual threat data retrieval from a database or other source
        # For now, return an empty list
        return []
    
    def get_assets_pnql():
        # TODO: Implement actual asset data retrieval from a database or other source
        # For now, return an empty list
        return []

    def execute_plugins_pnql(query_parsed_for_plugins: Dict[str, Any]):
        # This function bridges PNQL's SCAN command to the PluginManager
        # It expects a dictionary like {"target": "...", "plugins": [...]} 
        target = query_parsed_for_plugins.get("target")
        plugins_to_use = query_parsed_for_plugins.get("plugins", [])
        
        results = []
        for plugin_name in plugins_to_use:
            # First, load the plugin if not already loaded
            if plugin_manager.available_plugins.get(plugin_name) and \
               plugin_manager.available_plugins[plugin_name]["status"] != "loaded":
                plugin_manager.load_plugin(plugin_name)
                
            if plugin_manager.available_plugins.get(plugin_name) and \
               plugin_manager.available_plugins[plugin_name]["status"] == "loaded" and \
               plugin_manager.available_plugins[plugin_name]["manifest"]["type"] == "scanner": # Ensure it's a scanner type
                print(f"Executing scanner plugin '{plugin_name}' on target '{target}' via PNQL.")
                # We assume scanner plugins have a 'run_scan' or similar function
                # This needs to be formalized in plugin manifest/type
                func_name = "run_kerbrute_scan" if "kerbrute" in plugin_name.lower() else "run_scanner" # Defaulting for now
                
                plugin_result = plugin_manager.execute_plugin_function(plugin_name, func_name, target)
                results.append({"plugin": plugin_name, "target": target, "result": plugin_result})
            else:
                results.append({"plugin": plugin_name, "target": target, "error": "Plugin not found, not loaded, or not a scanner type."})
        return results


    pnql_data_sources = {
        "logs": get_logs_pnql,
        "threats": get_threats_pnql,
        "assets": get_assets_pnql,
        "scan_plugins": execute_plugins_pnql # The callable for SCAN command in PNQL
    }
    pnql_engine = PnqlEngine(pnql_data_sources)
    logger.info("PNQL Engine initialized.")


# Initialize Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class TransactionData(BaseModel):
    ip: str = Field(..., description="IP address of the attacking entity")
    port: int = Field(..., ge=1, le=65535, description="Port number involved in the attack")
    data: str = Field(..., min_length=1, max_length=2048, description="Raw attack data or payload")

    @validator('ip')
    def validate_ip_address(cls, v):
        # Basic IP address validation (can be expanded for IPv6 or more strict checks)
        parts = v.split('.')
        if len(parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
            raise ValueError('Invalid IP address format')
        return v

class LogEntryData(BaseModel):
    ip: str = Field(..., description="IP address from the log entry")
    port: int = Field(..., ge=0, le=65535, description="Port from the log entry")
    data: str = Field(..., min_length=1, description="Raw log data")

class AnomalyAlert(BaseModel):
    log_id: int
    ip: str
    port: int
    data: str
    timestamp: str
    anomaly_score: float
    attack_type: str
    confidence_score: float

class ThreatVerifiedAlert(BaseModel):
    log_id: int
    ip: str
    message: str

class BlacklistedAlert(BaseModel):
    ip: str
    message: str

class CopilotContext(BaseModel):
    user_role: str
    company_policy: str

class AttackEvent(BaseModel):
    log_id: int
    attack_type: str
    source_ip: str
    payload: str
    twin_instance_id: str | None = None

class ChatbotQuery(BaseModel):
    persona: str = "analyst"
    context: CopilotContext
    attack_event: AttackEvent
    query: str

class HoneypotControl(BaseModel):
    action: str = Field(..., description="Action to perform: 'start' or 'stop'")
    port: int = Field(..., ge=1, le=65535, description="Port number for the honeypot")

class SimulateAttack(BaseModel):
    ip: str = Field(..., description="IP address for simulation")
    port: int = Field(..., ge=1, le=65535, description="Port for simulation")
    data: str = Field(..., min_length=1, description="Data for simulation")

clients = set() # Store active WebSocket connections


# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost"], # Allow only the frontend development server
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
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "").lower()

    # Check for bad user agents
    for bad_agent in BAD_USER_AGENTS:
        if bad_agent in user_agent:
            logger.warning(f"Blocked request from blacklisted user agent: {user_agent} from IP: {ip}")
            return JSONResponse(status_code=403, content={"detail": "User agent is blacklisted"})

    db = SessionLocal()
    try:
        blacklisted_ip = db.query(BlacklistedIP).filter(BlacklistedIP.ip_address == ip).first()
    finally:
        db.close()
    if blacklisted_ip:
        logger.warning(f"Blocked request from blacklisted IP: {ip}")
        return JSONResponse(status_code=403, content={"detail": "IP address is blacklisted"})
    response = await call_next(request)
    return response

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
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
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "phantomnet_agent", "config.json")

app.include_router(api_ecosystem_router, prefix="/api/v1/enterprise", tags=["Enterprise API"])

def get_blockchain(db: Session = Depends(get_db)):
    return Blockchain(db)

@app.post("/blockchain/add_transaction", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def add_blockchain_transaction(
    transaction: TransactionData,
    current_user: dict = Depends(get_current_user),
    blockchain: Blockchain = Depends(get_blockchain), # Inject the Blockchain dependency
    db: Session = Depends(get_db) # Inject the database session
):
    try:
        # Add a new transaction to the blockchain
        blockchain.new_transaction(
            sender="honeypot", # The agent is the sender
            recipient=transaction.ip,
            amount=1, # Placeholder, consider adding more meaningful data from transaction.data
        )

        # Mine a new block to record the transaction
        last_block_obj = blockchain.last_block
        last_proof = last_block_obj.proof if last_block_obj else 0 # Get proof from the last block object
        previous_hash = blockchain.hash(last_block_obj.to_dict()) if last_block_obj else '1' # Hash the last block object

        new_block_obj = blockchain.new_block(proof, previous_hash)
        db.add(new_block_obj) # Add the new block to the session
        db.commit() # Commit the new block to the database
        db.refresh(new_block_obj) # Refresh to get the ID and other generated fields

        # Broadcast the new block event
        await broadcast_event({"type": "new_block", "block": new_block_obj.to_dict()}) # Use to_dict() for broadcasting

        # Add event to Redis Stream
        redis_client.xadd('blockchain_events', {'type': 'new_block', 'block_index': new_block_obj.index, 'timestamp': new_block_obj.timestamp.isoformat()}) # Use isoformat for datetime

        # Call the placeholder for smart contract interaction
        if new_block_obj.merkle_root: # Only write if there are transactions and thus a Merkle root
            await write_merkle_root_to_contract(new_block_obj.merkle_root, new_block_obj.index)

        logger.info(f"Transaction added and block mined: {new_block_obj.index}") # Use logger
        return {"message": "Transaction added and block mined", "block_index": new_block_obj.index}
    except Exception as e:
        db.rollback() # Rollback changes in case of error
        logger.error(f"Error in add_blockchain_transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the transaction."
        )

@app.post("/alerts/anomaly")
async def post_anomaly_alert(alert: AnomalyAlert):
    logger.info(f"Received anomaly alert: {alert.dict()}") # Use logger
    await broadcast_event({"type": "anomaly_alert", "alert": alert.dict()})
    return {"message": "Anomaly alert received and broadcasted"}

@app.post("/alerts/threat_verified")
async def post_threat_verified_alert(alert: ThreatVerifiedAlert):
    logger.info(f"Received verified threat alert: {alert.dict()}") # Use logger
    await broadcast_event({"type": "threat_verified_alert", "alert": alert.dict()})
    return {"message": "Verified threat alert received and broadcasted"}

@app.post("/alerts/blacklisted")
async def post_blacklisted_alert(alert: BlacklistedAlert):
    logger.info(f"Received blacklisted alert: {alert.dict()}") # Use logger
    await broadcast_event({"type": "blacklisted_alert", "alert": alert.dict()})
    return {"message": "Blacklisted alert received and broadcasted"}

# from backend_api.analyzer.model import get_qa_pipeline

def auto_select_persona(attack_event: AttackEvent) -> str:
    attack_type = attack_event.attack_type.lower()
    payload = attack_event.payload.lower()

    if "brute force" in attack_type or "scanning" in attack_type:
        return "analyst"
    elif "binary" in payload or "obfuscated" in payload:
        return "reverse_engineer"
    elif "intrusion" in payload or "exfil" in payload:
        return "prosecutor"
    else:
        return "analyst"  # Default persona

from phantomnet_agent.signatures.generator import generate_signatures, SignatureBundle

from phantomnet_agent.attribution.engine import attribute, AttributionResult
from phantomnet_agent.scoring.engine import compute_score, ThreatScore

from phantomnet_agent.scoring.engine import compute_score, ThreatScore

from phantomnet_agent.countermeasures.generator import generate_countermeasure, Countermeasure

@app.post("/chatbot", dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
async def chatbot_query(query: ChatbotQuery, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    persona = query.persona if query.persona else auto_select_persona(query.attack_event)

    if persona == "analyst":
        response = f"Analyst response for attack type {query.attack_event.attack_type} from {query.attack_event.source_ip}"
    elif persona == "reverse_engineer":
        response = f"Reverse engineer response for attack type {query.attack_event.attack_type} from {query.attack_event.source_ip}"
    elif persona == "prosecutor":
        response = f"Prosecutor response for attack type {query.attack_event.attack_type} from {query.attack_event.source_ip}"
    else:
        response = "Invalid persona."

    signatures = generate_signatures(query.attack_event)
    attribution_result = attribute(query.attack_event)
    threat_score = compute_score(query.attack_event, attribution_result)
    countermeasure = generate_countermeasure(query.attack_event, attribution_result, threat_score)
    
    logger.info(f"Chatbot query processed for user ID: {current_user.id}. Query: {query.query}") # Review query.query for PII
    return {"response": response, "signatures": signatures.dict(), "attribution": attribution_result.dict(), "threat_score": threat_score.dict(), "countermeasure": countermeasure.dict(), "redteam_run_id": query.attack_event.redteam_run_id}

from phantomnet_agent.digital_twin import generator, deployer, models
import yaml
from phantomnet_agent.red_teaming.api import router as red_teaming_router

app.include_router(red_teaming_router, prefix="/api", tags=["Red Teaming"])

@app.post("/digital_twin/render", response_model=models.TwinInstance)
async def render_digital_twin(template_id: str, params: dict, current_user: dict = Depends(get_current_user)):
    try:
        template_path = os.path.join(os.path.dirname(__file__), "..", "..", "phantomnet_agent", "digital_twin", "presets", f"{template_id}.yaml")
        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)
        template = models.TwinTemplate(**template_data)
        instance = generator.render_template(template, params)
        logger.info(f"Digital twin rendered for user ID: {current_user.id}. Instance ID: {instance.instance_id}") # Redact username
        return instance
    except FileNotFoundError:
        logger.warning(f"Digital twin template not found: {template_id}") # No PII
        raise HTTPException(status_code=404, detail="Template not found")
    except Exception as e:
        logger.error(f"Error rendering digital twin: {e}", exc_info=True) # No PII
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/digital_twin/deploy")
async def deploy_digital_twin(instance: models.TwinInstance, current_user: dict = Depends(get_current_user)):
    try:
        workdir = deployer.deploy_instance(instance)
        logger.info(f"Digital twin deployed for user ID: {current_user.id}. Instance ID: {instance.instance_id} in {workdir}") # Redact username
        return {"message": f"Instance {instance.instance_id} deployed successfully in {workdir}"}
    except Exception as e:
        logger.error(f"Error deploying digital twin: {e}", exc_info=True) # No PII
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/honeypot/control", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def honeypot_control(control: HoneypotControl, current_user: dict = Depends(get_current_user)):
    if control.action == "start":
        logger.info(f"User ID: {current_user.id} simulating starting honeypot on port {control.port}") # Redact username
        return {"message": f"Honeypot simulated to start on port {control.port}"}
    elif control.action == "stop":
        logger.info(f"User ID: {current_user.id} simulating stopping honeypot on port {control.port}") # Redact username
        return {"message": f"Honeypot simulated to stop on port {control.port}"}
    else:
        logger.info(f"User ID: {current_user.id} attempted invalid honeypot action: {control.action}") # Redact username
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'start' or 'stop'.")

@app.post("/honeypot/simulate_attack", dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def simulate_attack(attack: SimulateAttack, current_user: dict = Depends(get_current_user)):
    logger.info(f"User ID: {current_user.id} simulating attack from IP: {attack.ip} on port {attack.port} with data: [REDACTED]") # Redact username and attack.data
    # In a real scenario, this would send data to the collector service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://collector:8001/logs/ingest", # Directly call the collector service
                json={
                    "ip": attack.ip,
                    "port": attack.port,
                    "data": attack.data
                }
            )
            response.raise_for_status()
            logger.info(f"Simulated attack data sent to collector by user ID: {current_user.id}") # Redact username
            return {"message": "Simulated attack data sent to collector", "collector_response": response.json()}
    except httpx.RequestError as e:
        logger.error(f"User ID: {current_user.id} failed to send simulated attack to collector: {e}", exc_info=True) # Redact username
        raise HTTPException(status_code=500, detail=f"Failed to send simulated attack to collector: {e}")

@app.get("/")
def home():
    logger.info("Root endpoint accessed.") # Use logger
    return {"message": "PhantomNet API Running"}

@app.get("/logs", dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
def get_logs(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = db.query(AttackLog).order_by(AttackLog.timestamp.desc()).all()
    # Convert AttackLog objects to dictionaries or a suitable format for the frontend
    logger.info(f"User ID: {current_user.id} fetched logs.") # Redact username
    return {"logs": [{"timestamp": log.timestamp.isoformat(), "ip": log.ip, "port": log.port, "data": log.data, "attack_type": log.attack_type, "confidence_score": log.confidence_score, "is_anomaly": log.is_anomaly, "anomaly_score": log.anomaly_score, "is_verified_threat": log.is_verified_threat, "is_blacklisted": log.is_blacklisted} for log in logs]}

@app.get("/config", dependencies=[Depends(has_role([UserRole.ADMIN]))])
def get_config(current_user: dict = Depends(get_current_user)):
    # Note: Exposing the agent's configuration, even if not critically sensitive,
    # can provide reconnaissance information to an authenticated attacker.
    # Consider implementing more granular access control or filtering sensitive fields
    # if this endpoint is exposed to non-administrative users in production.
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"User ID: {current_user.id} attempted to fetch non-existent config file.") # Redact username
        return {"error": "Config file not found"}, 404
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    logger.info(f"User ID: {current_user.id} fetched config.") # Redact username
    return config

@app.get("/blockchain", dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))])
def get_blockchain_data(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    blocks = db.query(Block).order_by(Block.index).all()
    logger.info(f"User ID: {current_user.id} fetched blockchain data.") # Redact username
    return [block.to_dict() for block in blocks]

@app.post("/blockchain/verify", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def verify_blockchain_integrity(db: Session = Depends(get_db)):
    blockchain_instance = Blockchain(db)
    is_valid = blockchain_instance.is_chain_valid()
    if is_valid:
        logger.info("Blockchain integrity verified: All blocks are valid.") # Use logger
        return {"message": "Blockchain integrity verified: All blocks are valid."}
    else:
        logger.warning("Blockchain integrity compromised: Tampering detected.") # Use logger
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blockchain integrity compromised: Tampering detected.")

@app.get("/ip-info/{ip_address}", dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def get_ip_info(ip_address: str, current_user: dict = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://ip-api.com/json/{ip_address}")
        if response.status_code == 200:
            logger.info(f"User ID: {current_user.id} fetched IP info for IP: {ip_address}.") # Redact username
            return response.json()
        else:
            logger.error(f"User ID: {current_user.id} failed to fetch IP info for IP: {ip_address}: Status {response.status_code}") # Redact username
            return {"error": "Failed to fetch IP info"}, response.status_code

@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    logger.info("Client connected to /ws/events.") # No PII
    try:
        while True:
            # Keep the connection alive. Incoming messages are not expected for this broadcast endpoint.
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(ws)
        logger.info("Client disconnected from events.") # No PII
    except Exception as e:
        clients.remove(ws)
        logger.error(f"WebSocket event error: {e}", exc_info=True) # No PII
        import traceback
        traceback.print_exc()

@app.websocket("/ws/logs")
async def websocket_log_endpoint(
    websocket: WebSocket,
    token: str = None,
    db: Session = Depends(get_db) # Inject the database session
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Assuming we can get user ID from username here, or pass it through the token
    user = get_user(db, username=username) # Fetch user to get ID
    user_id_for_logging = user.id if user else "UNKNOWN"

    await websocket.accept()
    clients.add(websocket) # Add to the general clients set for broadcasting
    logger.info(f"Client connected to /ws/logs. User ID: {user_id_for_logging}") # Redact username
    try:
        # Send existing logs from the database
        logs = db.query(AttackLog).order_by(AttackLog.timestamp.desc()).limit(100).all() # Limit to 100 for initial load
        formatted_logs = [{"timestamp": log.timestamp.isoformat(), "ip": log.ip, "port": log.port, "data": log.data, "attack_type": log.attack_type, "confidence_score": log.confidence_score, "is_anomaly": log.is_anomaly, "anomaly_score": log.anomaly_score, "is_verified_threat": log.is_verified_threat, "is_blacklisted": log.is_blacklisted} for log in logs]
        await websocket.send_json({"type": "initial_logs", "logs": formatted_logs})

        # Keep the connection alive. New logs will be broadcasted via broadcast_event
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(ws)
        logger.info("Client disconnected from events.") # No PII
    except Exception as e:
        clients.remove(ws)
        import traceback
        logger.error(f"WebSocket event error: {e}", exc_info=True) # No PII
        traceback.print_exc()
    finally:
        await websocket.close()
