from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime
import asyncio
import uuid

# Assuming dependencies on other services
# In a real scenario, these would be API calls
# For now, we'll simulate data retrieval
from ...siem_ingest_service import crud as siem_crud
from ...siem_ingest_service.database import get_db as get_siem_db
from ...vulnerability_management_service import crud as vuln_crud
from ...vulnerability_management_service.database import get_db as get_vuln_db
from ..soc_copilot_service.context_builder.main import build_alert_context # Import from sub-module


router = APIRouter()

class CopilotExplanationRequest(BaseModel):
    alert_id: Optional[str] = Field(None, description="ID of the alert to explain.")
    event_id: Optional[str] = Field(None, description="ID of a specific event to explain.")
    query: Optional[str] = Field(None, description="A natural language query for the copilot.")

class CopilotExplanationResponse(BaseModel):
    explanation: str = Field(..., example="This alert indicates a potential brute-force attack on a critical server...")
    summary: str = Field(..., example="Brute-force attack detected on host-12345.")
    recommendations: List[str] = Field(default_factory=list, example=["Review login attempts.", "Block source IP.", "Implement MFA."])
    related_events: List[Dict[str, Any]] = Field(default_factory=list, description="List of related events identified during investigation.")
    confidence: str = Field(..., example="High", description="AI's confidence in the explanation.")
    raw_context: Dict[str, Any] = Field(default_factory=dict, description="Raw context data gathered for the explanation.")


class DetectionRuleGenerationRequest(BaseModel):
    incident_description: str = Field(..., example="Failed logins from multiple IPs targeting user 'admin' on host 'webserver-prod'.")
    rule_type: str = Field("sigma", example="sigma", description="Type of rule to generate (e.g., 'sigma', 'yara').")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context to help rule generation.")

class DetectionRuleGenerationResponse(BaseModel):
    rule_content: str = Field(..., example="title: Brute-Force Detection...")
    rule_format: str = Field(..., example="sigma")
    explanation: str = Field(..., example="This Sigma rule detects multiple failed login attempts against a single host/user.")
    confidence: str = Field(..., example="Medium")

class ThreatReportGenerationRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="ID of the incident to generate a report for.")
    scope: Optional[str] = Field(None, description="Scope of the report (e.g., 'full', 'executive_summary').")
    time_frame: Optional[str] = Field(None, example="past 24 hours")

class ThreatReportGenerationResponse(BaseModel):
    report_title: str = Field(..., example="Incident Report: Brute-Force Attack on Web Server")
    report_summary: str = Field(..., example="A detailed report on the brute-force attack incident.")
    report_content: str = Field(..., description="The full content of the generated report (Markdown or PDF base64).")
    report_format: str = Field(..., example="markdown")


@router.post("/explain_alert/", response_model=CopilotExplanationResponse)
async def explain_alert(
    request: CopilotExplanationRequest,
    siem_db: Session = Depends(get_siem_db),
    vuln_db: Session = Depends(get_vuln_db) # Pass other DB sessions as needed
):
    """
    Provides an AI-powered explanation and auto-investigation for a given alert or event.
    """
    if not request.alert_id and not request.event_id and not request.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either alert_id, event_id, or query must be provided.")

    # Simulate gathering context using the context_builder
    context = await build_alert_context(request.alert_id, request.event_id, request.query, siem_db, vuln_db)

    # Simulated AI logic based on context
    explanation_text = "Based on the available context, this appears to be a simulated event."
    summary_text = "Simulated event summary."
    recommendations_list = ["Simulated recommendation 1.", "Simulated recommendation 2."]
    related_events_list = []
    confidence_level = "Low"

    if context["primary_event"]:
        event = context["primary_event"]
        explanation_text = f"The event (ID: {event.id}, Type: {event.source_type}) indicates a '{event.raw_log_data[:50]}...' from {event.host_identifier}. This often signifies a {event.source_type} related activity. Ingested at: {event.ingested_at}. This is a raw log; further normalization would provide more detail."
        summary_text = f"Raw log from {event.host_identifier}, Type: {event.source_type}, Ingested: {event.ingested_at}."
        recommendations_list = [
            f"Investigate {event.host_identifier} for malicious activity.",
            f"Review other events around {event.timestamp}.",
            "Consider blocking the source IP if confirmed malicious."
        ]
        # Example of how severity could be inferred or used if normalized events were used
        # if event.severity == "Critical":
        #     explanation_text += " This is a critical event, requiring immediate attention."
        #     recommendations_list.insert(0, "Initiate incident response protocol immediately.")
        #     confidence_level = "High"
        
        # Populate related events if any were found
        for rel_event in context["related_events"]:
            related_events_list.append({
                "id": rel_event.id,
                "timestamp": rel_event.timestamp,
                "source_type": rel_event.source_type,
                "summary": rel_event.raw_log_data[:100] + "..." if len(rel_event.raw_log_data) > 100 else rel_event.raw_log_data
            })


    return CopilotExplanationResponse(
        explanation=explanation_text,
        summary=summary_text,
        recommendations=recommendations_list,
        related_events=related_events_list,
        confidence=confidence_level,
        raw_context=context
    )

@router.post("/generate_detection_rule/", response_model=DetectionRuleGenerationResponse)
async def generate_detection_rule(request: DetectionRuleGenerationRequest):
    """
    Generates a detection rule (e.g., Sigma, YARA) based on an incident description and context.
    """
    # Simulated AI logic for rule generation
    if request.rule_type.lower() == "sigma":
        rule_content = f"""
title: Generated Rule for {request.incident_description[:50]}
id: {str(uuid.uuid4())}
description: Generated by SOC Copilot for incident: {request.incident_description}
author: PhantomNet SOC Copilot
date: {datetime.date.today().isoformat()}
logsource:
    category: windows
    product: security
detection:
    selection:
        EventID: 4625 # Failed login
        Message|contains: '{request.incident_description}'
    condition: selection
level: high
"""
        explanation = "This Sigma rule targets failed login attempts that match the provided incident description. It's a basic rule and may require refinement."
    elif request.rule_type.lower() == "yara":
        rule_content = f"""
rule generated_by_copilot_{str(uuid.uuid4()).replace('-', '_')} {{
    meta:
        description = "Generated by SOC Copilot for incident: {request.incident_description}"
        author = "PhantomNet SOC Copilot"
        date = "{datetime.date.today().isoformat()}"
    strings:
        $s1 = "{request.incident_description.lower()}" wide ascii
    condition:
        $s1
}}
"""
        explanation = "This YARA rule looks for the incident description string within files. It's a very broad rule and might generate false positives."
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported rule type: {request.rule_type}")
    
    return DetectionRuleGenerationResponse(
        rule_content=rule_content,
        rule_format=request.rule_type,
        explanation=explanation,
        confidence="Low" # As it's a simple, generated rule
    )

@router.post("/generate_threat_report/", response_model=ThreatReportGenerationResponse)
async def generate_threat_report(request: ThreatReportGenerationRequest):
    """
    Generates a threat report for a given incident or based on specified scope/timeframe.
    """
    # Simulated AI logic for report generation
    report_title = f"Simulated Threat Report: Incident {request.incident_id or 'General'}"
    report_summary = f"This is a simulated executive summary for an incident report. Details for incident {request.incident_id or 'general scope'} are provided below."
    report_content = f"""
# {report_title}

## Executive Summary
{report_summary}

## Incident Details
- **Incident ID:** {request.incident_id or 'N/A'}
- **Scope:** {request.scope or 'General Monitoring'}
- **Timeframe:** {request.time_frame or 'As per request'}
- **AI Analysis:** Simulated analysis suggests low-to-medium impact.

## Recommendations
- Implement stronger access controls.
- Conduct regular security audits.
- Review and update incident response plans.

---
*Generated by PhantomNet SOC AI Copilot on {datetime.date.today().isoformat()}*
"""
    return ThreatReportGenerationResponse(
        report_title=report_title,
        report_summary=report_summary,
        report_content=report_content,
        report_format="markdown"
    )