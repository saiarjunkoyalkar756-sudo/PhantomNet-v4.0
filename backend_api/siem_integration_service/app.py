# backend_api/siem_integration_service/app.py

import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, APIRouter
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager # Import for lifespan
import uvicorn # Import uvicorn for standalone execution

from shared.logger_config import logger
from .schemas import RawLog, NormalizedLog, PhantomQLQuery, QueryResult, Workspace # Import models
from .siem_ingest_service import SIEMIngestService
from .log_normalizer import LogNormalizer
from .phantomql_engine import PhantomQLEngine

logger = logger

router = APIRouter(prefix="/siem", tags=["SIEM"])

# Initialize components
ingest_service = SIEMIngestService()
log_normalizer = LogNormalizer()
phantomql_engine = PhantomQLEngine()

# In-memory storage for raw and normalized logs (conceptual - in reality, persistent storage would be used)
raw_logs_store: List[RawLog] = []
normalized_logs_store: List[NormalizedLog] = []

# Conceptual multi-tenant workspaces
mock_workspaces: Dict[str, Workspace] = {
    "default-workspace": Workspace(workspace_id="default-workspace", name="Default Workspace", owner_user_id="admin")
}

async def siem_startup():
    logger.info("SIEM Integration Service starting up...")
    await ingest_service.start()
    asyncio.create_task(_process_raw_logs_for_normalization())

async def siem_shutdown():
    logger.info("SIEM Integration Service shutting down...")
    await ingest_service.stop()

async def _process_raw_logs_for_normalization():
    """Background task to continuously pull raw logs from ingest_service and normalize them."""
    while True:
        try:
            # For this in-memory example, we'll pull from the ingest_service's internal queue.
            # In a real system, this would be consuming from Kafka/Redpanda topic.
            if not ingest_service.raw_log_queue.empty():
                raw_log_dict = await ingest_service.raw_log_queue.get()
                raw_log = RawLog(**raw_log_dict) # Re-instantiate RawLog model
                raw_logs_store.append(raw_log)
                
                normalized_log = await log_normalizer.normalize_log(raw_log)
                if normalized_log:
                    normalized_logs_store.append(normalized_log)
                    phantomql_engine.add_indexed_log(normalized_log) # Add to query engine's index
                ingest_service.raw_log_queue.task_done()
            else:
                await asyncio.sleep(1) # Wait if no logs
        except Exception as e:
            logger.error(f"Error in raw log normalization background task: {e}", exc_info=True)
            await asyncio.sleep(5) # Avoid tight loop on continuous errors

@asynccontextmanager
async def lifespan(app: FastAPI):
    await siem_startup()
    yield
    await siem_shutdown()

app = FastAPI(title="SIEM Integration Service", lifespan=lifespan)
app.include_router(router, prefix="/api")


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "SIEM Integration Service is healthy"}

@router.post("/ingest", status_code=202)
async def ingest_log_event(raw_log: RawLog):
    """Ingest a raw log event into the SIEM."""
    await ingest_service.ingest_raw_log(raw_log)
    return {"status": "accepted", "message": "Log event queued for ingestion."}

@router.post("/query", response_model=QueryResult)
async def query_siem_logs(query: PhantomQLQuery):
    """Executes a PhantomQL query against normalized log data."""
    return await phantomql_engine.query_logs(query)

@router.get("/workspaces", response_model=List[Workspace])
async def get_workspaces():
    """Retrieves available multi-tenant workspaces (conceptual)."""
    return list(mock_workspaces.values())

@router.get("/logs/normalized", response_model=List[NormalizedLog])
async def get_normalized_logs(limit: int = 100, offset: int = 0):
    """Retrieves raw normalized logs directly (for debugging/testing)."""
    return normalized_logs_store[offset:offset+limit]

@router.get("/logs/raw", response_model=List[RawLog])
async def get_raw_logs(limit: int = 100, offset: int = 0):
    """Retrieves raw logs directly (for debugging/testing)."""
    return raw_logs_store[offset:offset+limit]

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8011, reload=True) # Assuming 8011 is the port for SIEM service