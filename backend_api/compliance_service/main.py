from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from .database import get_db
from . import crud
import datetime

router = APIRouter()

app = create_phantom_service(
    name="Compliance Service",
    description="Service for governance, risk, and compliance management.",
    version="1.0.0",
)


class ComplianceStandardBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "ISO 27001"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Information security management systems standard."})
    version: Optional[str] = Field(None, json_schema_extra={"example": "2022"})


class ComplianceStandardCreate(ComplianceStandardBase):
    pass


class ComplianceStandardResponse(ComplianceStandardBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ComplianceAssessmentBase(BaseModel):
    standard_name: str = Field(..., json_schema_extra={"example": "ISO 27001"})
    scope: Optional[Dict[str, Any]] = None


class ComplianceAssessmentCreate(ComplianceAssessmentBase):
    pass


class ComplianceAssessmentUpdate(BaseModel):
    status: Optional[str] = None
    overall_score: Optional[str] = None


class ComplianceAssessmentResponse(ComplianceAssessmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: str
    status: str
    overall_score: Optional[str]
    created_at: datetime.datetime


@router.post("/standards/", status_code=status.HTTP_201_CREATED)
def create_standard(standard: ComplianceStandardCreate, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=standard.name)
    if db_standard:
        return error_response(code="ALREADY_EXISTS", message="Compliance standard already exists", status_code=400)
    result = crud.create_compliance_standard(db=db, **standard.model_dump())
    return success_response(data=result)


@router.get("/standards/")
def read_standards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    import json
    from loguru import logger
    from backend_api.shared.redis_client import redis_client

    cache_key = f"compliance:standards:{skip}:{limit}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info("Serving compliance standards from Redis cache.")
            return success_response(data=json.loads(cached_data))
    except Exception as exc:
        logger.error(f"Redis cache read error: {exc}")

    standards = crud.get_compliance_standards(db, skip=skip, limit=limit)
    try:
        serializable_standards = [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "version": item.version,
                "created_at": item.created_at.isoformat() if hasattr(item.created_at, "isoformat") else str(item.created_at),
                "updated_at": item.updated_at.isoformat() if hasattr(item.updated_at, "isoformat") else str(item.updated_at),
            }
            for item in standards
        ]
        redis_client.setex(cache_key, 3600, json.dumps(serializable_standards))
    except Exception as exc:
        logger.error(f"Redis cache write error: {exc}")

    return success_response(data=standards)


@router.get("/standards/{standard_name}")
def read_standard(standard_name: str, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=standard_name)
    if not db_standard:
        return error_response(code="NOT_FOUND", message="Compliance standard not found", status_code=404)
    return success_response(data=db_standard)


@router.post("/assessments/", status_code=status.HTTP_201_CREATED)
def create_assessment(assessment: ComplianceAssessmentCreate, db: Session = Depends(get_db)):
    db_standard = crud.get_compliance_standard(db, name=assessment.standard_name)
    if not db_standard:
        return error_response(code="NOT_FOUND", message="Compliance standard not found", status_code=404)
    result = crud.create_compliance_assessment(
        db=db,
        standard_id=db_standard.id,
        **assessment.model_dump(exclude={"standard_name"}),
    )
    return success_response(data=result)


@router.get("/assessments/")
def read_assessments(db: Session = Depends(get_db)):
    return success_response(data=crud.get_compliance_assessments(db))


@router.get("/assessments/{assessment_id}")
def read_assessment(assessment_id: str, db: Session = Depends(get_db)):
    db_assessment = crud.get_compliance_assessment(db, assessment_id=assessment_id)
    if not db_assessment:
        return error_response(code="NOT_FOUND", message="Compliance assessment not found", status_code=404)
    return success_response(data=db_assessment)


@router.put("/assessments/{assessment_id}")
def update_assessment(assessment_id: str, assessment: ComplianceAssessmentUpdate, db: Session = Depends(get_db)):
    db_assessment = crud.update_compliance_assessment(
        db=db,
        assessment_id=assessment_id,
        **assessment.model_dump(exclude_unset=True),
    )
    if not db_assessment:
        return error_response(code="NOT_FOUND", message="Compliance assessment not found", status_code=404)
    return success_response(data=db_assessment)


app.include_router(router)
