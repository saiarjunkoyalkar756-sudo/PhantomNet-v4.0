from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .database import get_db
from . import crud
import datetime

router = APIRouter()

app = create_phantom_service(
    name="Compliance Service",
    description="Service for governance, risk, and compliance management.",
    version="1.0.0"
)
app.include_router(router)

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
        from_attributes = True

# --- Assessments ---
class ComplianceAssessmentBase(BaseModel):
    standard_name: str = Field(..., example="ISO 27001")
    scope: Optional[Dict[str, Any]] = None

class ComplianceAssessmentCreate(ComplianceAssessmentBase):
    pass

class ComplianceAssessmentUpdate(BaseModel):
    status: Optional[str] = None
    overall_score: Optional[str] = None

class ComplianceAssessmentResponse(ComplianceAssessmentBase):
    id: int
    assessment_id: str
    status: str
    overall_score: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Standards Endpoints ---
@router.post("/standards/", status_code=status.HTTP_201_CREATED)
def create_standard(standard: ComplianceStandardCreate, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=standard.name)
    if db_standard:
        return error_response(code="ALREADY_EXISTS", message="Compliance standard already exists", status_code=400)
    result = crud.create_compliance_standard(db=db, **standard.dict())
    return success_response(data=result)

@router.get("/standards/")
def read_standards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    standards = crud.get_compliance_standards(db, skip=skip, limit=limit)
    return success_response(data=standards)

@router.get("/standards/{standard_name}")
def read_standard(standard_name: str, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=standard_name)
    if not db_standard:
        return error_response(code="NOT_FOUND", message="Compliance standard not found", status_code=404)
    return success_response(data=db_standard)

# --- Assessments Endpoints ---
@router.post("/assessments/", status_code=status.HTTP_201_CREATED)
def create_assessment(assessment: ComplianceAssessmentCreate, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=assessment.standard_name)
    if not db_standard:
        return error_response(code="NOT_FOUND", message="Compliance standard not found", status_code=404)
    
    result = crud.create_compliance_assessment(db=db, standard_id=db_standard.id, **assessment.dict(exclude={"standard_name"}))
    return success_response(data=result)

@router.get("/assessments/")
def read_assessments(db: Session = Depends(get_db)):
    assessments = crud.get_compliance_assessments(db)
    return success_response(data=assessments)

@router.get("/assessments/{assessment_id}")
def read_assessment(assessment_id: str, db: Session = Depends(get_db)):
    db_assessment = crud.get_compliance_assessment(db, assessment_id=assessment_id)
    if not db_assessment:
        return error_response(code="NOT_FOUND", message="Compliance assessment not found", status_code=404)
    return success_response(data=db_assessment)

@router.put("/assessments/{assessment_id}")
def update_assessment(assessment_id: str, assessment: ComplianceAssessmentUpdate, db: Session = Depends(get_db)):
    db_assessment = crud.update_compliance_assessment(db=db, assessment_id=assessment_id, **assessment.dict(exclude_unset=True))
    if not db_assessment:
        return error_response(code="NOT_FOUND", message="Compliance assessment not found", status_code=404)
    return success_response(data=db_assessment)