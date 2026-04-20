from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .context_builder.main import build_alert_context
from ...siem_ingest_service.database import get_db as get_siem_db
from ...vulnerability_management_service.database import get_db as get_vuln_db
from loguru import logger
import datetime
import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends, FastAPI, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter()

class CopilotExplanationRequest(BaseModel):
    alert_id: Optional[str] = None
    event_id: Optional[str] = None
    query: Optional[str] = None

class CopilotExplanationResponse(BaseModel):
    explanation: str
    summary: str
    recommendations: List[str]
    related_events: List[Dict[str, Any]]
    confidence: str
    raw_context: Dict[str, Any]

class DetectionRuleGenerationRequest(BaseModel):
    incident_description: str
    rule_type: str = "sigma"
    context_data: Optional[Dict[str, Any]] = None

class DetectionRuleGenerationResponse(BaseModel):
    rule_content: str
    rule_format: str
    explanation: str
    confidence: str

class ThreatReportGenerationRequest(BaseModel):
    incident_id: Optional[str] = None
    scope: Optional[str] = None
    time_frame: Optional[str] = None

class ThreatReportGenerationResponse(BaseModel):
    report_title: str
    report_summary: str
    report_content: str
    report_format: str

@router.post("/explain_alert/", response_model=CopilotExplanationResponse)
async def explain_alert(
    request: CopilotExplanationRequest,
    siem_db: Session = Depends(get_siem_db),
    vuln_db: Session = Depends(get_vuln_db)
):
    if not request.alert_id and not request.event_id and not request.query:
        return error_response(code="BAD_REQUEST", message="Either alert_id, event_id, or query must be provided.", status_code=400)

    context = await build_alert_context(request.alert_id, request.event_id, request.query, siem_db, vuln_db)

    explanation_text = "Based on the available context, this appears to be a simulated event."
    summary_text = "Simulated event summary."
    recommendations_list = ["Simulated recommendation 1.", "Simulated recommendation 2."]
    related_events_list = []
    confidence_level = "Low"

    if context["primary_event"]:
        event = context["primary_event"]
        explanation_text = f"The event (Type: {event.source_type}) from {event.host_identifier} indicates suspicious activity."
        summary_text = f"Raw log from {event.host_identifier}."
        recommendations_list = [f"Investigate {event.host_identifier}.", "Review temporal correlation."]
        
        for rel_event in context["related_events"]:
            related_events_list.append({"id": rel_event.id, "summary": rel_event.raw_log_data[:50]})

    return success_response(data=CopilotExplanationResponse(
        explanation=explanation_text,
        summary=summary_text,
        recommendations=recommendations_list,
        related_events=related_events_list,
        confidence=confidence_level,
        raw_context=context
    ).model_dump())

@router.post("/generate_detection_rule/", response_model=DetectionRuleGenerationResponse)
async def generate_detection_rule(request: DetectionRuleGenerationRequest):
    rule_content = f"title: Generated Rule\ndescription: {request.incident_description}"
    return success_response(data=DetectionRuleGenerationResponse(
        rule_content=rule_content,
        rule_format=request.rule_type,
        explanation="Automatically generated rule.",
        confidence="Medium"
    ).model_dump())

@router.post("/generate_threat_report/", response_model=ThreatReportGenerationResponse)
async def generate_threat_report(request: ThreatReportGenerationRequest):
    return success_response(data=ThreatReportGenerationResponse(
        report_title="Threat Report",
        report_summary="Summary.",
        report_content="# Report Content",
        report_format="markdown"
    ).model_dump())

app = create_phantom_service(
    name="SOC Copilot Service",
    description="Interactive AI assistant for security analysts.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1/copilot")