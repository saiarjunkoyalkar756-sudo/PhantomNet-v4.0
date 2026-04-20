from backend_api.shared.service_factory import create_phantom_service
import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger
from backend_api.core.response import success_response, error_response
from .report_generator import generate_pdf_report

PDF_OUTPUT_DIR = "generated_reports"

async def compliance_reporting_startup(app: FastAPI):
    """
    Handles startup events for the Compliance Reporting Service.
    """
    if not os.path.exists(PDF_OUTPUT_DIR):
        os.makedirs(PDF_OUTPUT_DIR)
        logger.info(f"Compliance Reporting: Created directory {PDF_OUTPUT_DIR}")

app = create_phantom_service(
    name="Compliance Reporting Service",
    description="Generates and stores compliance audit reports.",
    version="1.0.0",
    custom_startup=compliance_reporting_startup
)

# In-memory store for reports (In production, this would be a DB)
reports_store: Dict[str, Dict[str, Any]] = {}

class ReportGenerationRequest(BaseModel):
    standard: str  # e.g., "soc2", "iso27001", "hipaa"
    scope: Optional[str] = "Global"

@app.post("/reports/generate")
async def generate_compliance_report(request: ReportGenerationRequest):
    """
    Triggers the generation of a compliance report and its PDF export.
    """
    report_id = f"{request.standard.lower()}-{uuid.uuid4().hex[:8]}"
    
    # Mock data collection for the report
    report_content = {
        "report_id": report_id,
        "standard": request.standard,
        "generated_at": datetime.utcnow().isoformat(),
        "status": "COMPLETED",
        "details": {
            "compliance_score": 92 if request.standard.lower() == "soc2" else 85,
            "findings": [
                {
                    "control_id": "CC1.1", 
                    "status": "Compliant", 
                    "description": "Board of Directors demonstrates commitment to integrity and ethical values."
                },
                {
                    "control_id": "CC6.1", 
                    "status": "Compliant", 
                    "description": "The entity restricts logical access to information assets."
                },
                {
                    "control_id": "CC7.1", 
                    "status": "Non-Compliant", 
                    "description": "Detection and monitoring of vulnerabilities is not fully automated.",
                    "severity": "MEDIUM"
                }
            ]
        }
    }
    
    # Generate PDF
    try:
        pdf_path = generate_pdf_report(report_content, output_dir=PDF_OUTPUT_DIR)
        report_content["pdf_path"] = pdf_path
        reports_store[report_id] = report_content
        
        logger.info(f"Compliance report {report_id} generated and saved to {pdf_path}")
        return success_response(
            message=f"{request.standard.upper()} report generated successfully.",
            data={"report_id": report_id, "score": report_content["details"]["compliance_score"]}
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF for report {report_id}: {str(e)}")
        return error_response(code="PDF_GENERATION_FAILED", message="Failed to generate PDF component of the report.", status_code=500)

@app.get("/reports")
async def list_reports():
    """Lists all generated reports."""
    summary = [{
        "report_id": r["report_id"],
        "standard": r["standard"],
        "generated_at": r["generated_at"],
        "score": r["details"]["compliance_score"]
    } for r in reports_store.values()]
    return success_response(data=summary)

@app.get("/reports/{report_id}/download")
async def download_report_pdf(report_id: str):
    """Downloads the PDF version of a compliance report."""
    report = reports_store.get(report_id)
    if not report or not os.path.exists(report.get("pdf_path", "")):
        return error_response(code="NOT_FOUND", message="Report or PDF file not found.", status_code=404)
    
    return FileResponse(
        path=report["pdf_path"],
        filename=os.path.basename(report["pdf_path"]),
        media_type="application/pdf"
    )
