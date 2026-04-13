# backend_api/soc_copilot_service/app.py

import os
import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, APIRouter
from pydantic import BaseModel
from datetime import datetime

from shared.logger_config import logger
from .schemas import AlertExplanationRequest, AlertExplanationResponse, InvestigationRequest, InvestigationResponse, RuleGenerationRequest, GeneratedRule, ThreatReportRequest, ThreatReportResponse
from .soc_copilot_service import SOCCopilotService

logger = logger

router = APIRouter(prefix="/soc-copilot", tags=["SOC AI Copilot"])

# Initialize the Copilot service
soc_copilot_service = SOCCopilotService()


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "SOC AI Copilot Service is healthy"}

@router.post("/explain_alert", response_model=AlertExplanationResponse)
async def explain_alert_endpoint(request: AlertExplanationRequest):
    """Explains a given alert using AI, providing impact and recommended actions."""
    try:
        response = await soc_copilot_service.explain_alert(request)
        return response
    except Exception as e:
        logger.error(f"Error explaining alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to explain alert: {e}")

@router.post("/auto_investigate", response_model=InvestigationResponse)
async def auto_investigate_endpoint(request: InvestigationRequest):
    """Runs an AI-driven auto-investigation for a given indicator."""
    try:
        response = await soc_copilot_service.auto_investigate(request)
        return response
    except Exception as e:
        logger.error(f"Error during auto-investigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to auto-investigate: {e}")

@router.post("/generate_rule", response_model=GeneratedRule)
async def generate_rule_endpoint(request: RuleGenerationRequest):
    """Generates a detection rule (e.g., YARA, Sigma) based on an event pattern."""
    try:
        response = await soc_copilot_service.write_detection_rule(request)
        return response
    except Exception as e:
        logger.error(f"Error generating rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate rule: {e}")

@router.post("/generate_report", response_model=ThreatReportResponse)
async def generate_report_endpoint(request: ThreatReportRequest):
    """Generates a threat report for a given incident."""
    try:
        response = await soc_copilot_service.generate_threat_report(request)
        return response
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

if __name__ == "__main__":
    # Example usage (requires uvicorn to run)
    # uvicorn app:app --reload --port 8000
    # Then access endpoints like:
    # POST http://localhost:8000/explain_alert
    pass
