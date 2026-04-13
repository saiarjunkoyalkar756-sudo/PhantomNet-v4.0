from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import asyncio

from ..database import get_db
from ..redis_client import redis_client
from ..services import plugin_manager, is_service_running

# Import get_db functions from other services
from backend_api.soar_playbook_engine.database import get_db as get_soar_db
from backend_api.threat_intelligence_service.app import app as threat_intel_app

router = APIRouter()

class ComponentStatus(BaseModel):
    name: str
    status: str
    details: Dict[str, Any] = {}

class HealthReport(BaseModel):
    overall_status: str
    components: List[ComponentStatus]

async def check_database_health(db: Session, name: str) -> ComponentStatus:
    try:
        db.execute("SELECT 1")
        return ComponentStatus(name=name, status="ok")
    except Exception as e:
        return ComponentStatus(name=name, status="error", details={"error": str(e)})

async def check_redis_health() -> ComponentStatus:
    try:
        is_redis_ok = redis_client.ping()
        if is_redis_ok:
            return ComponentStatus(name="redis", status="ok")
        else:
            return ComponentStatus(name="redis", status="degraded", details={"info": "Using mock Redis client."})
    except Exception as e:
        return ComponentStatus(name="redis", status="error", details={"error": str(e)})

async def check_service_health(service_name: str, url: str) -> ComponentStatus:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                return ComponentStatus(name=service_name, status="ok", details=response.json())
            else:
                return ComponentStatus(name=service_name, status="degraded", details=response.json())
    except httpx.RequestError as e:
        return ComponentStatus(name=service_name, status="error", details={"error": str(e)})

@router.get("/health", response_model=HealthReport)
async def get_health_status(db: Session = Depends(get_db), soar_db: Session = Depends(get_soar_db)):
    """
    Provides a detailed health check of all backend components.
    """
    component_statuses = await asyncio.gather(
        check_database_health(db, "main_database"),
        check_database_health(soar_db, "soar_database"),
        check_redis_health(),
        check_service_health("threat_intelligence_service", "http://localhost:8015/health")
        # Add checks for other services here
    )

    overall_ok = all(c.status == "ok" for c in component_statuses)

    return HealthReport(
        overall_status="ok" if overall_ok else "degraded",
        components=list(component_statuses)
    )

