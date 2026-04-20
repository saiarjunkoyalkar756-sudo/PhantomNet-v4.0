from backend_api.shared.service_factory import create_phantom_service
from .siem_ingest_service import SIEMIngestService
from .log_normalizer import LogNormalizer
from .phantomql_engine import PhantomQLEngine
from .schemas import RawLog, NormalizedLog, PhantomQLQuery, QueryResult, Workspace
from backend_api.core.response import success_response, error_response
from loguru import logger
import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, APIRouter, Depends, Request

router = APIRouter(prefix="/siem", tags=["SIEM"])

# Initialize components
ingest_service = SIEMIngestService()
log_normalizer = LogNormalizer()
phantomql_engine = PhantomQLEngine()

# In-memory storage for raw and normalized logs
raw_logs_store: List[RawLog] = []
normalized_logs_store: List[NormalizedLog] = []

mock_workspaces: Dict[str, Workspace] = {
    "default-workspace": Workspace(workspace_id="default-workspace", name="Default Workspace", owner_user_id="admin")
}

async def _process_raw_logs_for_normalization():
    """Background task to continuously pull raw logs from ingest_service and normalize them."""
    while True:
        try:
            if not ingest_service.raw_log_queue.empty():
                raw_log_dict = await ingest_service.raw_log_queue.get()
                raw_log = RawLog(**raw_log_dict)
                raw_logs_store.append(raw_log)
                
                normalized_log = await log_normalizer.normalize_log(raw_log)
                if normalized_log:
                    normalized_logs_store.append(normalized_log)
                    phantomql_engine.add_indexed_log(normalized_log)
                ingest_service.raw_log_queue.task_done()
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in raw log normalization background task: {e}")
            await asyncio.sleep(5)

async def siem_integration_startup(app: FastAPI):
    logger.info("SIEM Integration: Starting ingestion service.")
    await ingest_service.start()
    app.state.normalization_task = asyncio.create_task(_process_raw_logs_for_normalization())

async def siem_integration_shutdown(app: FastAPI):
    logger.info("SIEM Integration: Stopping ingestion service.")
    await ingest_service.stop()
    if hasattr(app.state, "normalization_task"):
        app.state.normalization_task.cancel()
        await asyncio.gather(app.state.normalization_task, return_exceptions=True)

app = create_phantom_service(
    name="SIEM Integration Service",
    description="Integrates log sources, performs normalization, and provides unified querying.",
    version="1.0.0",
    custom_startup=siem_integration_startup,
    custom_shutdown=siem_integration_shutdown
)

app.include_router(router, prefix="/api")

@router.post("/ingest", status_code=202)
async def ingest_log_event(raw_log: RawLog):
    """Ingest a raw log event into the SIEM."""
    await ingest_service.ingest_raw_log(raw_log)
    return success_response(message="Log event queued for ingestion.")

@router.post("/query", response_model=QueryResult)
async def query_siem_logs(query: PhantomQLQuery):
    """Executes a PhantomQL query against normalized log data."""
    result = await phantomql_engine.query_logs(query)
    return success_response(data=result)

@router.get("/workspaces", response_model=List[Workspace])
async def get_workspaces():
    """Retrieves available multi-tenant workspaces."""
    return success_response(data=list(mock_workspaces.values()))

@router.get("/logs/normalized", response_model=List[NormalizedLog])
async def get_normalized_logs(limit: int = 100, offset: int = 0):
    """Retrieves raw normalized logs directly."""
    return success_response(data=normalized_logs_store[offset:offset+limit])

@router.get("/logs/raw", response_model=List[RawLog])
async def get_raw_logs(limit: int = 100, offset: int = 0):
    """Retrieves raw logs directly."""
    return success_response(data=raw_logs_store[offset:offset+limit])