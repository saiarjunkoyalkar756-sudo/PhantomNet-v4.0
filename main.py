# main.py (PhantomNet Unified Stack Entry Point)
import os
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

# Ensure the root directory and backend_api directory are in python path
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "backend_api"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize unified root FastAPI application
app = FastAPI(
    title="PhantomNet Unified Stack",
    description="Unified API Gateway and microservices engine for PhantomNet v4.0. Designed for convenient local development and testing.",
    version="4.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registry of mounted sub-applications
mounted_services = {}

# Dynamic Service Loading Helpers
def mount_sub_service(path_prefix: str, module_path: str, app_var_name: str = "app") -> bool:
    """Dynamically imports a microservice FastAPI app and mounts it under path_prefix."""
    try:
        # Import the module
        logger.info(f"Loading microservice: {module_path}")
        parts = module_path.split('.')
        mod = __import__(module_path, fromlist=[app_var_name])
        sub_app = getattr(mod, app_var_name)
        
        # Mount the sub-app
        app.mount(path_prefix, sub_app)
        mounted_services[path_prefix] = module_path
        logger.info(f"Successfully mounted {module_path} on {path_prefix}")
        return True
    except ImportError as e:
        logger.warning(f"Could not import {module_path} due to missing dependency: {e}. Gracefully skipping.")
        return False
    except AttributeError:
        logger.warning(f"Module {module_path} does not export attribute '{app_var_name}'. Skipping.")
        return False
    except Exception as e:
        logger.error(f"Error loading {module_path}: {e}")
        return False

# --- Lifespan & Startup Hooks ---
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing PhantomNet Unified Stack...")
    
    # 1. Initialize Database Tables
    try:
        from backend_api.shared.database import create_db_and_tables
        logger.info("Running database schema migrations/initialization...")
        create_db_and_tables()
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

    # 2. Dynamic Microservices Registry Mounts
    # Mount main API gateway as root proxy or sub-path
    mount_sub_service("/api/v1/gateway", "backend_api.gateway_service.main")
    
    # Mount key telemetry and analytics services
    mount_sub_service("/api/v1/behavioral", "backend_api.ai_behavioral_engine.main")
    mount_sub_service("/api/v1/soar", "backend_api.soar_engine.app")
    mount_sub_service("/api/v1/compliance", "backend_api.compliance_service.main")
    mount_sub_service("/api/v1/vulnerability", "backend_api.vulnerability_management_service.main")
    mount_sub_service("/api/v1/bas", "backend_api.bas_engine.main")
    mount_sub_service("/api/v1/blue-team", "backend_api.autonomous_blue_team.main")
    mount_sub_service("/api/v1/honeypot", "backend_api.honeypot_service.main")
    mount_sub_service("/api/v1/threat-intel", "backend_api.threat_intelligence_service.main")
    mount_sub_service("/api/v1/asset", "backend_api.asset_inventory_service.main")
    mount_sub_service("/api/v1/forensics", "backend_api.forensics_engine.main")
    mount_sub_service("/api/v1/attack-graph", "backend_api.attack_graph_engine.main")
    mount_sub_service("/api/v1/chatbot", "backend_api.chatbot_service.main")
    mount_sub_service("/api/v1/dashboard", "backend_api.dashboard_service.main")

    logger.info(f"PhantomNet Unified Stack is ready! Mounted {len(mounted_services)} services.")

# --- Unified Root API Endpoints ---
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Welcome to PhantomNet v4.0 Unified Stack Developer Grid.",
        "mounted_services": mounted_services
    }

@app.get("/health")
async def health_check():
    """Aggregates diagnostics from critical dependencies (DB, Redis, Kafka) and active sub-apps."""
    health_results = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "kafka": "unknown",
        "active_services": list(mounted_services.keys())
    }
    
    # 1. Database Health Check
    try:
        from backend_api.shared.database import sync_engine
        from sqlalchemy import text
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_results["database"] = "healthy"
    except Exception as e:
        health_results["database"] = f"unhealthy ({e})"
        health_results["status"] = "degraded"
        
    # 2. Redis Health Check
    try:
        import redis
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", 6379))
        r = redis.Redis(host=redis_host, port=redis_port, socket_timeout=1.0)
        r.ping()
        health_results["redis"] = "healthy"
    except Exception as e:
        health_results["redis"] = f"unhealthy ({e})"
        # Do not degrade the entire stack if redis is missing in dev mode (unless required)
        
    # 3. Kafka Health Check
    try:
        from kafka import KafkaAdminClient
        kafka_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        admin = KafkaAdminClient(bootstrap_servers=kafka_servers, request_timeout_ms=1000)
        admin.list_topics()
        health_results["kafka"] = "healthy"
    except Exception as e:
        health_results["kafka"] = f"unhealthy ({e})"
        
    return health_results

if __name__ == "__main__":
    port = int(os.environ.get("UNIFIED_PORT", 8000))
    logger.info(f"Starting PhantomNet Unified Stack on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
