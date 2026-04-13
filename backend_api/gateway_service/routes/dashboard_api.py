# backend_api/gateway_service/routes/dashboard_api.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

# In a real app, you'd have proper dependency injection for services
# from ..services import get_attack_graph_service, get_asset_service, get_alert_service
from ....shared.database import get_db
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# --- MOCK DATA & SERVICES ---
# This simulates fetching data from other microservices.
async def get_mock_attack_path(incident_id: str) -> List[str]:
    if incident_id == "INC-001":
        return ["ip:1.2.3.4", "host:web-server-01", "process:powershell.exe", "host:domain-controller-01"]
    return []

async def get_mock_asset_details(asset_id: str) -> Dict[str, Any]:
    assets = {
        "host:web-server-01": {"owner": "web-team", "criticality": 7, "os": "Linux"},
        "host:domain-controller-01": {"owner": "it-infra", "criticality": 10, "os": "Windows Server"},
    }
    return assets.get(asset_id, {})

async def get_mock_alert_details(incident_id: str) -> Dict[str, Any]:
    if incident_id == "INC-001":
        return {
            "alert_id": "ALERT-XYZ-789",
            "title": "Potential Ransomware Kill-Chain Detected",
            "timestamp": "2025-12-13T12:00:00Z",
            "severity": "CRITICAL",
            "source_ip": "1.2.3.4",
            "target_asset_id": "host:web-server-01",
            "ai_explanation": "Alert triggered because a process spawned from an Office document made a suspicious DNS request, a pattern consistent with initial access and C2 establishment (T1566.001 -> T1071.001)."
        }
    return {}
# --- END MOCK DATA ---


@router.get("/incident/{incident_id}/details", response_model=Dict[str, Any])
async def get_incident_details_for_soc(incident_id: str):
    """
    Endpoint for the SOC Analyst Workflow.
    Aggregates all necessary data for an incident into a single response
    to power the incident details view in the dashboard.
    """
    logger.info(f"Fetching aggregated details for incident: {incident_id}")

    # 1. Get the core alert details (from the alerts database/service)
    alert_details = await get_mock_alert_details(incident_id)
    if not alert_details:
        raise HTTPException(status_code=404, detail="Incident not found")

    # 2. Get the predicted attack path from the Attack Graph Engine
    attack_path = await get_mock_attack_path(incident_id)

    # 3. Enrich the attack path nodes with details from the Asset Inventory Service
    enriched_path = []
    for node_id in attack_path:
        asset_details = await get_mock_asset_details(node_id)
        enriched_path.append({"node_id": node_id, "details": asset_details})

    # 4. Get SOAR simulation results (conceptual)
    soar_preview = {
        "recommended_playbook": "critical_host_compromise_remediation",
        "business_impact_score": 9,
        "reason_for_escalation": "Business impact (9) is above the autonomy threshold (4)."
    }

    # 5. Combine everything into a single response object
    return {
        "incident_summary": alert_details,
        "attack_graph": {
            "path": enriched_path,
        },
        "soar_decision_preview": soar_preview,
        "related_events": [], # Placeholder for raw events
    }

@router.get("/executive-summary", response_model=Dict[str, Any])
async def get_executive_summary():
    """
    Endpoint for the Executive Summary Dashboard.
    Provides high-level, aggregated metrics about the platform's performance.
    """
    # In a real system, this data would be calculated and cached by a reporting service.
    return {
        "mean_time_to_respond_hours": 6.5,
        "automated_remediations_count_24h": 128,
        "manual_escalations_count_24h": 15,
        "overall_risk_score": 78, # A score out of 100
        "risk_trend_percent_7d": -5.2, # Negative means risk is decreasing
        "top_attack_vectors": [
            {"vector": "Phishing", "count": 45},
            {"vector": "Exposed Public Service", "count": 22},
            {"vector": "Credential Stuffing", "count": 18},
        ]
    }

@router.get("/risk-trends", response_model=Dict[str, List[Dict[str, Any]]])
async def get_risk_trends():
    """
    Endpoint for the Risk Trend Visualization.
    Provides time-series data for plotting risk scores.
    """
    # This data would come from a service that calculates and stores historical risk scores.
    return {
        "risk_history": [
            {"date": "2025-12-06", "score": 82},
            {"date": "2025-12-07", "score": 85},
            {"date": "2025-12-08", "score": 83},
            {"date": "2025-12-09", "score": 79},
            {"date": "2025-12-10", "score": 80},
            {"date": "2025-12-11", "score": 75},
            {"date": "2025-12-12", "score": 78},
        ]
    }
