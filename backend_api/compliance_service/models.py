from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import datetime
import json

Base = declarative_base()

class ComplianceStandard(Base):
    __tablename__ = "compliance_standards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True) # e.g., "ISO 27001", "SOC 2 Type II", "HIPAA"
    description = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)

    assessments = relationship("ComplianceAssessment", back_populates="standard")

    def __repr__(self):
        return f"<ComplianceStandard(id={self.id}, name='{self.name}', version='{self.version}')>"


class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String, unique=True, nullable=False, index=True) # UUID for the assessment
    standard_id = Column(Integer, ForeignKey("compliance_standards.id"), nullable=False)
    start_date = Column(DateTime, server_default=func.now(), nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, default="in_progress", nullable=False) # e.g., "in_progress", "completed", "failed"
    overall_score = Column(String, nullable=True) # e.g., "Compliant", "Non-Compliant", "Partial"
    scope_json = Column(Text, nullable=True) # JSON for defining assessment scope (e.g., assets, departments)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)

    standard = relationship("ComplianceStandard", back_populates="assessments")
    findings = relationship("ComplianceFinding", back_populates="assessment")

    def __repr__(self):
        return f"<ComplianceAssessment(id={self.id}, standard='{self.standard.name}', status='{self.status}')>"

    @property
    def scope(self):
        return json.loads(self.scope_json) if self.scope_json else {}

    @scope.setter
    def scope(self, value):
        self.scope_json = json.dumps(value)


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(String, unique=True, nullable=False, index=True) # UUID for the finding
    assessment_id = Column(Integer, ForeignKey("compliance_assessments.id"), nullable=False)
    control_id = Column(String, nullable=False) # e.g., "A.12.1.1" for ISO 27001
    control_description = Column(Text, nullable=True)
    status = Column(String, default="open", nullable=False) # e.g., "open", "compliant", "non_compliant", "mitigated"
    evidence_json = Column(Text, nullable=True) # JSON for links to collected evidence
    gap_description = Column(Text, nullable=True) # Description of the gap if non-compliant
    recommendation = Column(Text, nullable=True)
    severity = Column(String, nullable=True) # e.g., "High", "Medium", "Low"
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)

    assessment = relationship("ComplianceAssessment", back_populates="findings")

    def __repr__(self):
        return f"<ComplianceFinding(id={self.id}, control='{self.control_id}', status='{self.status}')>"

    @property
    def evidence(self):
        return json.loads(self.evidence_json) if self.evidence_json else {}

    @evidence.setter
    def evidence(self, value):
        self.evidence_json = json.dumps(value)
