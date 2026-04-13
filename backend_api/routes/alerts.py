from fastapi import APIRouter, Depends
from pydantic import BaseModel
import logging
from loguru import logger

from ..iam_service.auth_methods import get_current_user, User, UserRole, has_role

router = APIRouter()

class AnomalyAlert(BaseModel):
    log_id: int
    ip: str
    port: int
    data: str
    timestamp: str
    anomaly_score: float
    attack_type: str
    confidence_score: float


class ThreatVerifiedAlert(BaseModel):
    log_id: int
    ip: str
    message: str


class BlacklistedAlert(BaseModel):
    ip: str
    message: str

async def broadcast_event(message: dict):
    logger.info(f"Broadcasting event: {message.get('type')}")
    # This is a placeholder for the actual broadcast implementation
    # In the original app.py, this is handled by a global list of clients
    # For now, we will just log the event
    print(f"Broadcasting event: {message}")


@router.post("/alerts/anomaly")
async def post_anomaly_alert(alert: AnomalyAlert):
    logger.info(f"Received anomaly alert: {alert.dict()}")  # Use logger
    await broadcast_event({"type": "anomaly_alert", "alert": alert.dict()})
    return {"message": "Anomaly alert received and broadcasted"}


@router.post("/alerts/threat_verified")
async def post_threat_verified_alert(alert: ThreatVerifiedAlert):
    logger.info(f"Received verified threat alert: {alert.dict()}")  # Use logger
    await broadcast_event({"type": "threat_verified_alert", "alert": alert.dict()})
    return {"message": "Verified threat alert received and broadcasted"}


@router.post("/alerts/blacklisted")
async def post_blacklisted_alert(alert: BlacklistedAlert):
    logger.info(f"Received blacklisted alert: {alert.dict()}")  # Use logger
    await broadcast_event({"type": "blacklisted_alert", "alert": alert.dict()})
    return {"message": "Blacklisted alert received and broadcasted"}
