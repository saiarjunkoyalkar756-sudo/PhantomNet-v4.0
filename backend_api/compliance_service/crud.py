from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from .models import ComplianceStandard, ComplianceAssessment, ComplianceFinding
import datetime
import json
import uuid

# --- CRUD for ComplianceStandard ---
def create_compliance_standard(db: Session, name: str, description: Optional[str] = None,
                               version: Optional[str] = None) -> ComplianceStandard:
    db_standard = ComplianceStandard(
        name=name,
        description=description,
        version=version
    )
    db.add(db_standard)
    db.commit()
    db.refresh(db_standard)
    return db_standard

def get_compliance_standard(db: Session, standard_id: Optional[int] = None, name: Optional[str] = None) -> Optional[ComplianceStandard]:
    if standard_id:
        return db.query(ComplianceStandard).filter(ComplianceStandard.id == standard_id).first()
    if name:
        return db.query(ComplianceStandard).filter(ComplianceStandard.name == name).first()
    return None

def get_compliance_standards(db: Session, skip: int = 0, limit: int = 100) -> List[ComplianceStandard]:
    return db.query(ComplianceStandard).offset(skip).limit(limit).all()

# --- CRUD for ComplianceAssessment ---
def create_compliance_assessment(db: Session, standard_id: int, scope: Optional[Dict[str, Any]] = None) -> ComplianceAssessment:
    assessment_uuid = str(uuid.uuid4())
    db_assessment = ComplianceAssessment(
        assessment_id=assessment_uuid,
        standard_id=standard_id,
        scope_json=json.dumps(scope) if scope else None
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

def get_compliance_assessment(db: Session, assessment_id: Optional[str] = None, id: Optional[int] = None) -> Optional[ComplianceAssessment]:
    if id:
        return db.query(ComplianceAssessment).filter(ComplianceAssessment.id == id).first()
    if assessment_id:
        return db.query(ComplianceAssessment).filter(ComplianceAssessment.assessment_id == assessment_id).first()
    return None

def get_compliance_assessments(db: Session, standard_id: Optional[int] = None,
                                status: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[ComplianceAssessment]:
    query = db.query(ComplianceAssessment)
    if standard_id:
        query = query.filter(ComplianceAssessment.standard_id == standard_id)
    if status:
        query = query.filter(ComplianceAssessment.status == status)
    return query.order_by(ComplianceAssessment.created_at.desc()).offset(skip).limit(limit).all()

def update_compliance_assessment(db: Session, assessment_id: str,
                                 status: Optional[str] = None,
                                 overall_score: Optional[str] = None,
                                 end_date: Optional[datetime.datetime] = None,
                                 scope: Optional[Dict[str, Any]] = None) -> Optional[ComplianceAssessment]:
    db_assessment = get_compliance_assessment(db, assessment_id=assessment_id)
    if db_assessment:
        if status is not None:
            db_assessment.status = status
        if overall_score is not None:
            db_assessment.overall_score = overall_score
        if end_date is not None:
            db_assessment.end_date = end_date
        if scope is not None:
            db_assessment.scope_json = json.dumps(scope)
        db_assessment.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(db_assessment)
    return db_assessment

# --- CRUD for ComplianceFinding ---
def create_compliance_finding(db: Session, assessment_db_id: int, control_id: str,
                              control_description: Optional[str] = None,
                              status: Optional[str] = None,
                              evidence: Optional[Dict[str, Any]] = None,
                              gap_description: Optional[str] = None,
                              recommendation: Optional[str] = None,
                              severity: Optional[str] = None) -> ComplianceFinding:
    finding_uuid = str(uuid.uuid4())
    db_finding = ComplianceFinding(
        finding_id=finding_uuid,
        assessment_id=assessment_db_id,
        control_id=control_id,
        control_description=control_description,
        status=status if status else "open",
        evidence_json=json.dumps(evidence) if evidence else None,
        gap_description=gap_description,
        recommendation=recommendation,
        severity=severity
    )
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    return db_finding

def get_compliance_finding(db: Session, finding_id: Optional[str] = None, id: Optional[int] = None) -> Optional[ComplianceFinding]:
    if id:
        return db.query(ComplianceFinding).filter(ComplianceFinding.id == id).first()
    if finding_id:
        return db.query(ComplianceFinding).filter(ComplianceFinding.finding_id == finding_id).first()
    return None

def get_compliance_findings(db: Session, assessment_id: Optional[int] = None,
                           control_id: Optional[str] = None, status: Optional[str] = None,
                           skip: int = 0, limit: int = 100) -> List[ComplianceFinding]:
    query = db.query(ComplianceFinding)
    if assessment_id:
        query = query.filter(ComplianceFinding.assessment_id == assessment_id)
    if control_id:
        query = query.filter(ComplianceFinding.control_id == control_id)
    if status:
        query = query.filter(ComplianceFinding.status == status)
    return query.order_by(ComplianceFinding.created_at.desc()).offset(skip).limit(limit).all()

def update_compliance_finding(db: Session, finding_id: str,
                              status: Optional[str] = None,
                              evidence: Optional[Dict[str, Any]] = None,
                              gap_description: Optional[str] = None,
                              recommendation: Optional[str] = None,
                              severity: Optional[str] = None) -> Optional[ComplianceFinding]:
    db_finding = get_compliance_finding(db, finding_id=finding_id)
    if db_finding:
        if status is not None:
            db_finding.status = status
        if evidence is not None:
            db_finding.evidence_json = json.dumps(evidence)
        if gap_description is not None:
            db_finding.gap_description = gap_description
        if recommendation is not None:
            db_finding.recommendation = recommendation
        if severity is not None:
            db_finding.severity = severity
        db_finding.updated_at = datetime.datetime.now()
        db.commit()
        db.refresh(db_finding)
    return db_finding
