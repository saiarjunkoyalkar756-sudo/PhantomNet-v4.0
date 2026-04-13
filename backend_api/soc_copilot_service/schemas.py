from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AlertExplanationRequest(BaseModel):
    alert_title: str
    alert_description: str
    alert_context: Dict[str, Any] = Field(default_factory=dict)

class AlertExplanationResponse(BaseModel):
    explanation: str = Field(..., description="LLM-generated explanation of the alert.")
    potential_impact: List[str] = Field(default_factory=list, description="Potential impact statements.")
    recommended_actions: List[str] = Field(default_factory=list, description="Suggested immediate actions.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class InvestigationRequest(BaseModel):
    indicator_value: str
    indicator_type: str
    initial_alert_id: Optional[str] = None
    investigation_context: Dict[str, Any] = Field(default_factory=dict)

class InvestigationStep(BaseModel):
    step_description: str
    tool_used: Optional[str] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    status: str = "completed" # e.g., "completed", "failed", "pending_human_review"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class InvestigationResponse(BaseModel):
    summary: str = Field(..., description="LLM-generated summary of the investigation.")
    conclusion: str
    steps_taken: List[InvestigationStep]
    identified_threats: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_remediation: List[str] = Field(default_factory=list)

class RuleGenerationRequest(BaseModel):
    event_pattern: Dict[str, Any] = Field(..., description="A dictionary describing the event pattern to detect.")
    rule_type: str = Field(..., description="Type of rule to generate (e.g., 'yara', 'sigma').")
    context_info: Optional[str] = Field(None, description="Additional context for rule generation.")

class GeneratedRule(BaseModel):
    rule_type: str
    rule_content: str
    rule_name: str
    description: str
    mitre_techniques: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class ThreatReportRequest(BaseModel):
    incident_id: str
    report_type: str = "summary" # e.g., "summary", "technical", "executive"
    additional_context: Optional[str] = None

class ThreatReportResponse(BaseModel):
    report_title: str
    report_summary: str
    report_content: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    sections: Dict[str, str] = Field(default_factory=dict)
    related_indicators: List[str] = Field(default_factory=list)