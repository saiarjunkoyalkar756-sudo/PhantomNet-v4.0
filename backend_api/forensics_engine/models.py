from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import datetime
import json

Base = declarative_base()

class ForensicJob(Base):
    __tablename__ = "forensic_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False) # UUID for the job
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)
    status = Column(String, default="pending", nullable=False) # e.g., pending, running, completed, failed
    target_asset_id = Column(String, nullable=False) # Identifier for the asset being investigated
    requested_by = Column(String, nullable=True) # User or system that initiated the job
    job_type = Column(String, nullable=False) # e.g., "full_disk_image", "memory_dump", "log_collection", "timeline_reconstruction"
    parameters_json = Column(Text, nullable=True) # JSON for job-specific parameters

    reports = relationship("ForensicReport", back_populates="job")

    def __repr__(self):
        return f"<ForensicJob(id={self.id}, job_id='{self.job_id}', status='{self.status}', target='{self.target_asset_id}')>"

    @property
    def parameters(self):
        return json.loads(self.parameters_json) if self.parameters_json else {}

    @parameters.setter
    def parameters(self, value):
        self.parameters_json = json.dumps(value)


class ForensicReport(Base):
    __tablename__ = "forensic_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, index=True, nullable=False) # UUID for the report
    job_id = Column(Integer, ForeignKey("forensic_jobs.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)
    status = Column(String, default="generating", nullable=False) # e.g., generating, completed, failed
    report_type = Column(String, nullable=False) # e.g., "timeline", "memory_analysis", "summary"
    report_summary = Column(Text, nullable=True)
    report_path = Column(String, nullable=True) # Path to the generated report file (e.g., PDF)
    findings_json = Column(Text, nullable=True) # JSON for structured findings

    job = relationship("ForensicJob", back_populates="reports")

    def __repr__(self):
        return f"<ForensicReport(id={self.id}, report_id='{self.report_id}', type='{self.report_type}')>"

    @property
    def findings(self):
        return json.loads(self.findings_json) if self.findings_json else {}

    @findings.setter
    def findings(self, value):
        self.findings_json = json.dumps(value)
