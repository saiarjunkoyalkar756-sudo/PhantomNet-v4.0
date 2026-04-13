from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
import uuid
import asyncio

from . import crud, models
from .database import SessionLocal, engine, get_db

# Import routers from sub-modules
from .timeline_builder.main import router as timeline_router, TimelineRequest, TimelineResponse
from .evidence_collector.main import router as evidence_router, EvidenceCollectionRequest, EvidenceCollectionResponse



router = APIRouter()

# Include sub-module routers
router.include_router(timeline_router, prefix="/timeline", tags=["timeline_builder"])
router.include_router(evidence_router, prefix="/evidence", tags=["evidence_collector"])

# Pydantic models for API request/response validation
from pydantic import BaseModel, Field

class ForensicJobCreate(BaseModel):
    target_asset_id: str = Field(..., example="compromised-server-01")
    job_type: str = Field(..., example="full_investigation", description="Type of forensic job (e.g., 'full_disk_image', 'memory_dump', 'log_collection', 'timeline_reconstruction', 'full_investigation').")
    requested_by: Optional[str] = Field(None, example="analyst_alice")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Job-specific parameters (e.g., 'artifact_types': ['memory_dump', 'logs'], 'time_range': {'start': '...', 'end': '...'}).")

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
        orm_mode = True

class ForensicReportResponse(BaseModel):
    report_id: str
    job_id: str # Refers to ForensicJob.job_id (external UUID)
    created_at: datetime.datetime
    updated_at: datetime.datetime
    status: str
    report_type: str
    report_summary: Optional[str]
    report_path: Optional[str]
    findings: Dict[str, Any]

    class Config:
        orm_mode = True

async def _perform_forensic_tasks_in_background(job_id: str, job_type: str, target_asset_id: str, parameters: Dict[str, Any], db: Session):
    """
    Simulates performing various forensic tasks in the background.
    """
    print(f"Starting forensic job {job_id} of type {job_type} for asset {target_asset_id}")
    
    # Update job status
    crud.update_forensic_job_status(db, job_id, "running")

    try:
        # Simulate evidence collection
        if job_type in ["full_disk_image", "memory_dump", "log_collection", "full_investigation"]:
            artifact_types = parameters.get("artifact_types", ["memory_dump", "system_logs", "user_files"])
            collection_request = EvidenceCollectionRequest(
                asset_id=target_asset_id,
                job_id=job_id,
                artifact_types=artifact_types,
                collection_parameters=parameters.get("collection_parameters", {})
            )
            # Call evidence_collector's API internally (simulated for now)
            # In a real microservice, this would be an HTTP call
            collected_evidence = await evidence_router.post_collect_evidence(collection_request)
            
            crud.create_forensic_report(
                db=db,
                job_db_id=crud.get_forensic_job(db, job_id=job_id).id,
                report_type="evidence_collection",
                report_summary=f"Collected {len(collected_evidence.collected_artifacts)} artifacts.",
                findings={"collected_artifacts": [a.dict() for a in collected_evidence.collected_artifacts]}
            )
            print(f"Job {job_id}: Evidence collection completed.")
        
        # Simulate timeline reconstruction
        if job_type in ["timeline_reconstruction", "full_investigation"]:
            timeline_request = TimelineRequest(
                asset_id=target_asset_id,
                start_time=parameters.get("start_time"),
                end_time=parameters.get("end_time"),
                data_sources=parameters.get("timeline_data_sources", ["logs", "memory"])
            )
            # Call timeline_builder's API internally (simulated for now)
            # In a real microservice, this would be an HTTP call
            forensic_timeline = await timeline_router.post_build_forensic_timeline(timeline_request)

            crud.create_forensic_report(
                db=db,
                job_db_id=crud.get_forensic_job(db, job_id=job_id).id,
                report_type="timeline_reconstruction",
                report_summary=f"Reconstructed timeline with {len(forensic_timeline.timeline_events)} events.",
                findings={"timeline_events": [e.dict() for e in forensic_timeline.timeline_events]}
            )
            print(f"Job {job_id}: Timeline reconstruction completed.")

        # Simulate AI-powered PDF report generation (placeholder)
        if job_type == "full_investigation":
            await asyncio.sleep(5) # Simulate report generation time
            pdf_report_path = f"/forensics_repo/{job_id}/full_report.pdf"
            crud.create_forensic_report(
                db=db,
                job_db_id=crud.get_forensic_job(db, job_id=job_id).id,
                report_type="final_report",
                report_summary="AI-generated comprehensive incident report.",
                report_path=pdf_report_path,
                findings={"ai_summary": "Initial AI assessment indicates sophisticated persistent threat."}
            )
            print(f"Job {job_id}: AI-powered report generated.")

        crud.update_forensic_job_status(db, job_id, "completed")
        print(f"Forensic job {job_id} completed successfully.")

    except Exception as e:
        print(f"Forensic job {job_id} failed: {e}")
        crud.update_forensic_job_status(db, job_id, "failed")
        raise


@router.post("/jobs/", response_model=ForensicJobResponse, status_code=status.HTTP_201_CREATED)
async def create_forensic_job_endpoint(
    job_create: ForensicJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Creates and initiates a new forensic job.
    """
    new_job = crud.create_forensic_job(
        db=db,
        target_asset_id=job_create.target_asset_id,
        job_type=job_create.job_type,
        requested_by=job_create.requested_by,
        parameters=job_create.parameters
    )
    
    # Trigger background processing
    background_tasks.add_task(
        _perform_forensic_tasks_in_background,
        new_job.job_id, new_job.job_type, new_job.target_asset_id, new_job.parameters, db
    )

    return new_job

@router.get("/jobs/", response_model=List[ForensicJobResponse])
def read_forensic_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    target_asset_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of forensic jobs.
    """
    jobs = crud.get_forensic_jobs(db, skip=skip, limit=limit, status=status, target_asset_id=target_asset_id)
    return jobs

@router.get("/jobs/{job_id}", response_model=ForensicJobResponse)
def read_forensic_job(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves details of a specific forensic job.
    """
    db_job = crud.get_forensic_job(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic job not found")
    return db_job

@router.get("/jobs/{job_id}/reports", response_model=List[ForensicReportResponse])
def read_reports_for_job(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all reports associated with a specific forensic job.
    """
    db_job = crud.get_forensic_job(db, job_id=job_id)
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic job not found")
    
    reports = crud.get_forensic_reports_for_job(db, job_db_id=db_job.id)
    # Map SQLAlchemy object attributes to Pydantic model for JSON serialization
    response_reports = []
    for report in reports:
        response_reports.append(ForensicReportResponse(
            report_id=report.report_id,
            job_id=db_job.job_id, # Use external job_id here
            created_at=report.created_at,
            updated_at=report.updated_at,
            status=report.status,
            report_type=report.report_type,
            report_summary=report.report_summary,
            report_path=report.report_path,
            findings=report.findings
        ))
    return response_reports


@router.get("/reports/{report_id}", response_model=ForensicReportResponse)
def read_forensic_report(report_id: str, db: Session = Depends(get_db)):
    """
    Retrieves details of a specific forensic report.
    """
    db_report = crud.get_forensic_report(db, report_id=report_id)
    if db_report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forensic report not found")
    
    db_job = crud.get_forensic_job(db, id=db_report.job_id) # Get parent job to link external job_id
    if db_job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated forensic job not found for report.")

    return ForensicReportResponse(
        report_id=db_report.report_id,
        job_id=db_job.job_id,
        created_at=db_report.created_at,
        updated_at=db_report.updated_at,
        status=db_report.status,
        report_type=db_report.report_type,
        report_summary=db_report.report_summary,
        report_path=db_report.report_path,
        findings=db_report.findings
    )
