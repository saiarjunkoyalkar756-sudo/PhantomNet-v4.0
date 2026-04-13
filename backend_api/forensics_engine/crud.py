from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from .models import ForensicJob, ForensicReport
import datetime
import json
import uuid

def create_forensic_job(db: Session, target_asset_id: str, job_type: str,
                        requested_by: Optional[str] = None,
                        parameters: Optional[Dict[str, Any]] = None) -> ForensicJob:
    job_uuid = str(uuid.uuid4())
    db_job = ForensicJob(
        job_id=job_uuid,
        target_asset_id=target_asset_id,
        job_type=job_type,
        requested_by=requested_by,
        parameters_json=json.dumps(parameters) if parameters else None
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_forensic_job(db: Session, job_id: Optional[str] = None, id: Optional[int] = None) -> Optional[ForensicJob]:
    if id:
        return db.query(ForensicJob).filter(ForensicJob.id == id).first()
    if job_id:
        return db.query(ForensicJob).filter(ForensicJob.job_id == job_id).first()
    return None

def get_forensic_jobs(db: Session, skip: int = 0, limit: int = 100,
                      status: Optional[str] = None,
                      target_asset_id: Optional[str] = None) -> List[ForensicJob]:
    query = db.query(ForensicJob)
    if status:
        query = query.filter(ForensicJob.status == status)
    if target_asset_id:
        query = query.filter(ForensicJob.target_asset_id == target_asset_id)
    return query.order_by(ForensicJob.created_at.desc()).offset(skip).limit(limit).all()

def update_forensic_job_status(db: Session, job_id: str, status: str) -> Optional[ForensicJob]:
    db_job = get_forensic_job(db, job_id=job_id)
    if db_job:
        db_job.status = status
        db_job.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(db_job)
    return db_job

def create_forensic_report(db: Session, job_db_id: int, report_type: str,
                           report_summary: Optional[str] = None,
                           report_path: Optional[str] = None,
                           findings: Optional[Dict[str, Any]] = None) -> ForensicReport:
    report_uuid = str(uuid.uuid4())
    db_report = ForensicReport(
        report_id=report_uuid,
        job_id=job_db_id,
        report_type=report_type,
        report_summary=report_summary,
        report_path=report_path,
        findings_json=json.dumps(findings) if findings else None
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_forensic_report(db: Session, report_id: Optional[str] = None, id: Optional[int] = None) -> Optional[ForensicReport]:
    if id:
        return db.query(ForensicReport).filter(ForensicReport.id == id).first()
    if report_id:
        return db.query(ForensicReport).filter(ForensicReport.report_id == report_id).first()
    return None

def get_forensic_reports_for_job(db: Session, job_db_id: int) -> List[ForensicReport]:
    return db.query(ForensicReport).filter(ForensicReport.job_id == job_db_id).order_by(ForensicReport.created_at.desc()).all()

def update_forensic_report(db: Session, report_id: str,
                           status: Optional[str] = None,
                           report_summary: Optional[str] = None,
                           report_path: Optional[str] = None,
                           findings: Optional[Dict[str, Any]] = None) -> Optional[ForensicReport]:
    db_report = get_forensic_report(db, report_id=report_id)
    if db_report:
        if status is not None:
            db_report.status = status
        if report_summary is not None:
            db_report.report_summary = report_summary
        if report_path is not None:
            db_report.report_path = report_path
        if findings is not None:
            db_report.findings_json = json.dumps(findings)
        db_report.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(db_report)
    return db_report
