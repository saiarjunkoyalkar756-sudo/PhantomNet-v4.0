# backend_api/gateway_service/orchestrator_api.py
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend_api.shared.database import get_db, Block, Transaction, User
from backend_api.blockchain_service.blockchain import Blockchain
from backend_api.iam_service.auth_methods import UserRole, has_role, get_current_user
from backend_api.core.logging import logger as pn_logger
from backend_api.core.response import success_response, error_response

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])

async def get_blockchain(db: AsyncSession = Depends(get_db)) -> Blockchain:
    return Blockchain(db)

class ThreatData(BaseModel):
    threat_string: str

@router.post("/threats")
async def analyze_threat_endpoint(threat_data: ThreatData):
    """
    Endpoint to analyze threat data using the Cognitive Core.
    """
    pn_logger.warning("Orchestrator threat analysis is currently disabled.")
    return error_response(code="DISABLED", message="Orchestrator threat analysis is currently disabled.", status_code=501)

@router.get("/blockchain")
async def get_blockchain_data(
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the blockchain data from the database."""
    stmt = select(Block).order_by(Block.index)
    result = await db.execute(stmt)
    blocks = result.scalars().all()
    
    pn_logger.info(f"User {current_user.username} fetched blockchain data.")
    return success_response(data={"chain": [block.to_dict() for block in blocks]})

@router.post("/blockchain/verify", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def verify_blockchain_integrity(blockchain: Blockchain = Depends(get_blockchain)):
    """Verifies the integrity of the blockchain."""
    is_valid = await blockchain.is_chain_valid()
    if is_valid:
        pn_logger.info("Blockchain integrity verified: All blocks are valid.")
        return success_response(data={"message": "Blockchain integrity verified: All blocks are valid."})
    else:
        pn_logger.warning("Blockchain integrity compromised: Tampering detected.")
        return error_response(code="INTEGRITY_COMPROMISED", message="Blockchain integrity compromised: Tampering detected.", status_code=400)

def _retired_legacy_orchestrator_mutation():
    return error_response(
        code="LEGACY_GATEWAY_ORCHESTRATOR_MUTATION_RETIRED",
        message=(
            "This legacy gateway orchestrator mutation route is retired. Use governed, "
            "tenant-scoped workflows with required approval and auditable evidence."
        ),
        status_code=410,
    )


@router.api_route(
    "/blockchain/add_transaction",
    methods=["POST"],
    include_in_schema=False,
)
async def retired_blockchain_transaction_mutation():
    """Fail closed instead of mining caller-supplied transactions through the gateway."""
    return _retired_legacy_orchestrator_mutation()


@router.api_route(
    "/honeypot/control",
    methods=["POST"],
    include_in_schema=False,
)
async def retired_honeypot_control_mutation():
    """Fail closed instead of exposing gateway-controlled honeypot lifecycle actions."""
    return _retired_legacy_orchestrator_mutation()


@router.api_route(
    "/honeypot/simulate_attack",
    methods=["POST"],
    include_in_schema=False,
)
async def retired_honeypot_attack_simulation_mutation():
    """Fail closed instead of forwarding caller-defined simulated attacks to ingestion."""
    return _retired_legacy_orchestrator_mutation()
