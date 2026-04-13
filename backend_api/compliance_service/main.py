from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
import uuid

from . import crud, models
from .database import SessionLocal, engine, get_db



router = APIRouter()

# Pydantic models for API request/response validation
from pydantic import BaseModel, Field

# --- Standards ---
class ComplianceStandardBase(BaseModel):
    name: str = Field(..., example="ISO 27001")
    description: Optional[str] = Field(None, example="Information security management systems standard.")
    version: Optional[str] = Field(None, example="2022")

class ComplianceStandardCreate(ComplianceStandardBase):
    pass

class ComplianceStandardResponse(ComplianceStandardBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

# --- Assessments ---
class ComplianceAssessmentBase(BaseModel):
    standard_name: str = Field(..., example="ISO 27001", description="Name of the compliance standard this assessment is against.")
    scope: Optional[Dict[str, Any]] = Field(None, example={"assets": ["server-01", "webapp-db"], "departments": ["IT"]})

class ComplianceAssessmentCreate(ComplianceAssessmentBase):
    pass

class ComplianceAssessmentUpdate(BaseModel):
    status: Optional[str] = Field(None, example="completed")
    overall_score: Optional[str] = Field(None, example="Compliant")
    end_date: Optional[datetime.datetime] = None
    scope: Optional[Dict[str, Any]] = None

class ComplianceAssessmentResponse(ComplianceAssessmentBase):
    id: int
    assessment_id: str
    standard_id: int
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime]
    status: str
    overall_score: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

# --- Findings ---
class ComplianceFindingBase(BaseModel):
    control_id: str = Field(..., example="A.5.1.1")
    control_description: Optional[str] = Field(None, example="Policy for information security.")
    status: str = Field("open", example="non_compliant")
    evidence: Optional[Dict[str, Any]] = Field(None, example={"document_link": "http://doc.example.com/sec_policy.pdf"})
    gap_description: Optional[str] = Field(None, example="Lack of formal security policy document.")
    recommendation: Optional[str] = Field(None, example="Develop and publish an information security policy.")
    severity: Optional[str] = Field(None, example="High")

class ComplianceFindingCreate(ComplianceFindingBase):
    pass

class ComplianceFindingUpdate(ComplianceFindingBase):
    control_id: Optional[str] = None # Control ID should not change typically
    status: Optional[str] = None

class ComplianceFindingResponse(ComplianceFindingBase):
    id: int
    finding_id: str
    assessment_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

# --- Standards Endpoints ---
@router.post("/standards/", response_model=ComplianceStandardResponse, status_code=status.HTTP_201_CREATED)
def create_standard(standard: ComplianceStandardCreate, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=standard.name)
    if db_standard:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Compliance standard with this name already exists")
    return crud.create_compliance_standard(db=db, **standard.dict())

@router.get("/standards/", response_model=List[ComplianceStandardResponse])
def read_standards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    standards = crud.get_compliance_standards(db, skip=skip, limit=limit)
    return standards

@router.get("/standards/{standard_name}", response_model=ComplianceStandardResponse)
def read_standard(standard_name: str, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=standard_name)
    if db_standard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance standard not found")
    return db_standard

# --- Assessments Endpoints ---
@router.post("/assessments/", response_model=ComplianceAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(assessment: ComplianceAssessmentCreate, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=assessment.standard_name)
    if db_standard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Compliance standard '{assessment.standard_name}' not found")
    
    assessment_data = assessment.dict(exclude={"standard_name"})
    return crud.create_compliance_assessment(db=db, standard_id=db_standard.id, **assessment_data)

@router.get("/assessments/", response_model=List[ComplianceAssessmentResponse])
def read_assessments(
    standard_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    assessments = crud.get_compliance_assessments(db, standard_id=standard_id, status=status, skip=skip, limit=limit)
    return [
        ComplianceAssessmentResponse(
            id=a.id,
            assessment_id=a.assessment_id,
            standard_name=a.standard.name, # Populate standard_name from relationship
            standard_id=a.standard_id,
            start_date=a.start_date,
            end_date=a.end_date,
            status=a.status,
            overall_score=a.overall_score,
            scope=a.scope,
            created_at=a.created_at,
            updated_at=a.updated_at
        ) for a in assessments
    ]

@router.get("/assessments/{assessment_id}", response_model=ComplianceAssessmentResponse)
def read_assessment(assessment_id: str, db: Session = Depends(get_db)):
    db_assessment = crud.get_compliance_assessment(db, assessment_id=assessment_id)
    if db_assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance assessment not found")
    
    return ComplianceAssessmentResponse(
        id=db_assessment.id,
        assessment_id=db_assessment.assessment_id,
        standard_name=db_assessment.standard.name,
        standard_id=db_assessment.standard_id,
        start_date=db_assessment.start_date,
        end_date=db_assessment.end_date,
        status=db_assessment.status,
        overall_score=db_assessment.overall_score,
        scope=db_assessment.scope,
        created_at=db_assessment.created_at,
        updated_at=db_assessment.updated_at
    )

@router.put("/assessments/{assessment_id}", response_model=ComplianceAssessmentResponse)
def update_assessment(assessment_id: str, assessment: ComplianceAssessmentUpdate, db: Session = Depends(get_db)):
    db_assessment = crud.update_compliance_assessment(db=db, assessment_id=assessment_id, **assessment.dict(exclude_unset=True))
    if db_assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance assessment not found")
    
    return ComplianceAssessmentResponse(
        id=db_assessment.id,
        assessment_id=db_assessment.assessment_id,
        standard_name=db_assessment.standard.name,
        standard_id=db_assessment.standard_id,
        start_date=db_assessment.start_date,
        end_date=db_assessment.end_date,
        status=db_assessment.status,
        overall_score=db_assessment.overall_score,
        scope=db_assessment.scope,
        created_at=db_assessment.created_at,
        updated_at=db_assessment.updated_at
    )

# --- Findings Endpoints ---
@router.post("/assessments/{assessment_id}/findings", response_model=ComplianceFindingResponse, status_code=status.HTTP_201_CREATED)
def create_finding_for_assessment(assessment_id: str, finding: ComplianceFindingCreate, db: Session = Depends(get_db)):
    db_assessment = crud.get_compliance_assessment(db, assessment_id=assessment_id)
    if db_assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance assessment not found")
    
    finding_data = finding.dict()
    return crud.create_compliance_finding(db=db, assessment_db_id=db_assessment.id, **finding_data)

@router.get("/assessments/{assessment_id}/findings", response_model=List[ComplianceFindingResponse])
def read_findings_for_assessment(
    assessment_id: str,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    db_assessment = crud.get_compliance_assessment(db, assessment_id=assessment_id)
    if db_assessment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance assessment not found")
    
    findings = crud.get_compliance_findings(db, assessment_id=db_assessment.id, status=status, skip=skip, limit=limit)
    return [
        ComplianceFindingResponse(
            id=f.id,
            finding_id=f.finding_id,
            assessment_id=f.assessment_id,
            control_id=f.control_id,
            control_description=f.control_description,
            status=f.status,
            evidence=f.evidence,
            gap_description=f.gap_description,
            recommendation=f.recommendation,
            severity=f.severity,
            created_at=f.created_at,
            updated_at=f.updated_at
        ) for f in findings
    ]

@router.get("/findings/{finding_id}", response_model=ComplianceFindingResponse)
def read_finding(finding_id: str, db: Session = Depends(get_db)):
    db_finding = crud.get_compliance_finding(db, finding_id=finding_id)
    if db_finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance finding not found")
    
    return ComplianceFindingResponse(
        id=db_finding.id,
        finding_id=db_finding.finding_id,
        assessment_id=db_finding.assessment_id,
        control_id=db_finding.control_id,
        control_description=db_finding.control_description,
        status=db_finding.status,
        evidence=db_finding.evidence,
        gap_description=db_finding.gap_description,
        recommendation=db_finding.recommendation,
        severity=db_finding.severity,
        created_at=db_finding.created_at,
        updated_at=db_finding.updated_at
    )

@router.put("/findings/{finding_id}", response_model=ComplianceFindingResponse)
def update_finding(finding_id: str, finding: ComplianceFindingUpdate, db: Session = Depends(get_db)):
    db_finding = crud.update_compliance_finding(db=db, finding_id=finding_id, **finding.dict(exclude_unset=True))
    if db_finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance finding not found")
    
    return ComplianceFindingResponse(
        id=db_finding.id,
        finding_id=db_finding.finding_id,
        assessment_id=db_finding.assessment_id,
        control_id=db_finding.control_id,
        control_description=db_finding.control_description,
        status=db_finding.status,
        evidence=db_finding.evidence,
        gap_description=db_finding.gap_description,
        recommendation=db_finding.recommendation,
        severity=db_finding.severity,
        created_at=db_finding.created_at,
        updated_at=db_finding.updated_at
    )