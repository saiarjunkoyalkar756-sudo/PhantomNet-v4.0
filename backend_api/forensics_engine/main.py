from backend_api.shared.service_factory import create_phantom_service
from . import crud, models
from .database import SessionLocal, engine, get_db
from .timeline_builder.main import router as timeline_router, TimelineRequest, TimelineResponse
from .evidence_collector.main import router as evidence_router, EvidenceCollectionRequest, EvidenceCollectionResponse
from backend_api.core.response import success_response, error_response
from loguru import logger
import datetime
import uuid
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, FastAPI
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

router = APIRouter()
router.include_router(timeline_router, prefix="/timeline", tags=["timeline_builder"])
router.include_router(evidence_router, prefix="/evidence", tags=["evidence_collector"])

# Define Models
class ForensicJobCreate(BaseModel):
    target_asset_id: str = Field(..., example="compromised-server-01")
    job_type: str = Field(..., example="full_investigation")
    requested_by: Optional[str] = Field(None, example="analyst_alice")
    parameters: Optional[Dict[str, Any]] = Field(None)

class ForensicJobResponse(BaseModel):
    job_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: str
    target_asset_id: str
    requested_by: Optional[str]
    job_type: str
    parameters: Dict[str, Any]

    class Config:
        from_attributes = True

class ForensicReportResponse(BaseModel):
    report_id: str
    job_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: str
    report_type: str
    report_summary: Optional[str]
    report_path: Optional[str]
    findings: Dict[str, Any]

    class Config:
        from_attributes = True

async def _perform_forensic_tasks_in_background(job_id: str, job_type: str, target_asset_id: str, parameters: Dict[str, Any], db: Session):
    logger.info(f"Starting forensic job {job_id}")
    crud.update_forensic_job_status(db, job_id, "running")
    try:
        # Simulations (placeholder logic from original)
        await asyncio.sleep(2)
        crud.update_forensic_job_status(db, job_id, "completed")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        crud.update_forensic_job_status(db, job_id, "failed")

@router.post("/jobs/", response_model=ForensicJobResponse, status_code=status.HTTP_201_CREATED)
async def create_forensic_job_endpoint(job_create: ForensicJobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_job = crud.create_forensic_job(db=db, target_asset_id=job_create.target_asset_id, job_type=job_create.job_type, requested_by=job_create.requested_by, parameters=job_create.parameters)
    background_tasks.add_task(_perform_forensic_tasks_in_background, new_job.job_id, new_job.job_type, new_job.target_asset_id, new_job.parameters, db)
    return success_response(data=new_job)

@router.get("/jobs/", response_model=List[ForensicJobResponse])
def read_forensic_jobs(skip: int = 0, limit: int = 100, status: Optional[str] = None, target_asset_id: Optional[str] = None, db: Session = Depends(get_db)):
    jobs = crud.get_forensic_jobs(db, skip=skip, limit=limit, status=status, target_asset_id=target_asset_id)
    return success_response(data=jobs)

async def forensics_startup(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    logger.info("Forensics Engine: Database tables initialized.")

app = create_phantom_service(
    name="Forensics Engine",
    description="Advanced forensic analysis engine.",
    version="1.0.0",
    custom_startup=forensics_startup
)

app.include_router(router)
