# backend_api/compliance_reporting_service/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any, List
from datetime import datetime
import random

logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory store for simulated reports
reports_store: Dict[str, Dict[str, Any]] = {}


class ReportGenerationRequest(BaseModel):
    standard: str  # e.g., "iso27001", "soc2", "pci_dss", "gdpr"
    start_date: str = None
    end_date: str = None
    
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Compliance Reporting Service is healthy"}

@app.post("/reports/generate", status_code=201)
async def generate_compliance_report(request: ReportGenerationRequest):
    """
    Generates a simulated compliance report for a given standard.
    """
    report_id = f"{request.standard}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    report_content = {
        "report_id": report_id,
        "standard": request.standard,
        "generated_at": datetime.now().isoformat(),
        "status": "COMPLETED",
        "summary": f"Simulated {request.standard} compliance report generated.",
        "details": {
            "scope": "Entire PhantomNet deployment (simulated)",
            "compliance_score": random.randint(70, 100),
            "findings": [
                {"control_id": "A.5.1.1", "status": "Compliant", "description": "Information security policy in place."},
                {"control_id": "A.9.2.1", "status": "Non-Compliant", "description": "Some user access reviews are overdue (simulated).", "severity": "MEDIUM"}
            ] if request.standard == "iso27001" else (
                [{"control_id": "CC1.1", "status": "Compliant", "description": "Control environment established."}] if request.standard == "soc2" else (
                    [{"control_id": "Req 1.1", "status": "Compliant", "description": "Install and maintain a firewall configuration."}] if request.standard == "pci_dss" else (
                        [{"control_id": "Art. 5", "status": "Compliant", "description": "Principles relating to processing of personal data."}] if request.standard == "gdpr" else []
                    )
                )
            ),
            "recommendations": ["Review overdue access reviews." ] if request.standard == "iso27001" else []
        }
    }
    
    reports_store[report_id] = report_content
    logger.info(f"Generated simulated {request.standard} report: {report_id}")
    return {"message": "Report generated successfully", "report_id": report_id}

@app.get("/reports", response_model=List[Dict[str, Any]])
async def get_all_reports():
    """
    Retrieves a list of all generated reports.
    """
    return list(reports_store.values())

@app.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_report_by_id(report_id: str):
    """
    Retrieves a specific report by its ID.
    """
    report = reports_store.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
