from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from loguru import logger

from iam_service.auth_methods import get_current_user, User, UserRole, has_role
from shared.database import get_db
from phantomnet_agent.signatures.generator import generate_signatures, SignatureBundle
from phantomnet_agent.attribution.engine import attribute, AttributionResult
from phantomnet_agent.scoring.engine import compute_score, ThreatScore
from phantomnet_agent.countermeasures.generator import (
    generate_countermeasure,
    Countermeasure,
)

router = APIRouter()

class CopilotContext(BaseModel):
    user_role: str
    company_policy: str


class AttackEvent(BaseModel):
    log_id: int
    attack_type: str
    source_ip: str
    payload: str
    twin_instance_id: str | None = None


class ChatbotQuery(BaseModel):
    persona: str = "analyst"
    context: CopilotContext
    attack_event: AttackEvent
    query: str


def auto_select_persona(attack_event: AttackEvent) -> str:
    attack_type = attack_event.attack_type.lower()
    payload = attack_event.payload.lower()

    if "brute force" in attack_type or "scanning" in attack_type:
        return "analyst"
    elif "binary" in payload or "obfuscated" in payload:
        return "reverse_engineer"
    elif "intrusion" in payload or "exfil" in payload:
        return "prosecutor"
    else:
        return "analyst"  # Default persona

@router.post(
    "/chatbot",
    dependencies=[
        Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))
    ],
)
async def chatbot_query(
    query: ChatbotQuery,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    persona = (
        query.persona if query.persona else auto_select_persona(query.attack_event)
    )

    if persona == "analyst":
        response = f"Analyst response for attack type {query.attack_event.attack_type} from {query.attack_event.source_ip}"
    elif persona == "reverse_engineer":
        response = f"Reverse engineer response for attack type {query.attack_event.attack_type} from {query.attack_event.source_ip}"
    elif persona == "prosecutor":
        response = f"Prosecutor response for attack type {query.attack_event.attack_type} from {query.attack_event.source_ip}"
    else:
        response = "Invalid persona."

    signatures = generate_signatures(query.attack_event)
    attribution_result = attribute(query.attack_event)
    threat_score = compute_score(query.attack_event, attribution_result)
    countermeasure = generate_countermeasure(
        query.attack_event, attribution_result, threat_score
    )

    logger.info(
        f"Chatbot query processed for user ID: {current_user.id}. Query: {query.query}"
    )  # Review query.query for PII
    return {
        "response": response,
        "signatures": signatures.dict(),
        "attribution": attribution_result.dict(),
        "threat_score": threat_score.dict(),
        "countermeasure": countermeasure.dict(),
        "redteam_run_id": query.attack_event.redteam_run_id if hasattr(query.attack_event, 'redteam_run_id') else None,
    }
