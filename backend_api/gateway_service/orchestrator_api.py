# backend_api/gateway_service/orchestrator_api.py
import os
import json
import hashlib
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend_api.shared.database import get_db, Block, Transaction, User
from backend_api.blockchain_service.blockchain import Blockchain
from backend_api.iam_service.auth_methods import UserRole, has_role, get_current_user
from backend_api.shared.schemas import TransactionData, HoneypotControl, SimulateAttack
from backend_api.shared.command_dispatcher import CommandDispatcher
from backend_api.core.logging import logger as pn_logger
from backend_api.core.response import success_response, error_response

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])

# Initialize the CommandDispatcher
command_dispatcher = CommandDispatcher()

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

@router.post("/blockchain/add_transaction", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def add_blockchain_transaction(
    transaction: TransactionData,
    blockchain: Blockchain = Depends(get_blockchain),
    db: AsyncSession = Depends(get_db)
):
    """Adds a transaction and mines a new block asynchronously."""
    try:
        # Add a new transaction to the blockchain (now async)
        await blockchain.new_transaction(
            sender="honeypot",
            recipient=transaction.ip,
            amount=1.0,
            data={"raw_data": transaction.data}
        )

        # Mine a new block (now async and handles persistence internally)
        # We simulate a proof-of-work increment based on the last block
        last_block = await blockchain.last_block
        proof = (last_block.proof + 1) if last_block else 100
        
        new_block_obj = await blockchain.mine_block(proof)
        
        # mine_block calls db.add() and db.flush(), but we need to commit
        await db.commit()
        await db.refresh(new_block_obj)

        pn_logger.info(f"Transaction added and block mined asynchronously: {new_block_obj.index}")
        return success_response(data={
            "message": "Transaction added and block mined (Async)",
            "block_index": new_block_obj.index
        })
    except Exception as e:
        await db.rollback()
        pn_logger.error(f"Error in add_blockchain_transaction: {str(e)}", exc_info=True)
        return error_response(code="INTERNAL_ERROR", message=f"Failed to process transaction: {str(e)}", status_code=500)

@router.post("/honeypot/control", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def honeypot_control(
    control: HoneypotControl, 
    current_user: User = Depends(get_current_user)
):
    """Controls the honeypot status."""
    if control.action not in ["start", "stop"]:
        return error_response(code="INVALID_ACTION", message="Action must be 'start' or 'stop'.", status_code=400)

    pn_logger.info(f"User {current_user.username} {control.action}ing honeypot on port {control.port}")
    return success_response(data={"message": f"Honeypot {control.action}ed on port {control.port}"})

@router.post("/honeypot/simulate_attack", dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))])
async def simulate_attack(
    attack: SimulateAttack, 
    current_user: User = Depends(get_current_user)
):
    """Simulates an attack against the honeypot for testing."""
    pn_logger.info(f"User {current_user.username} simulating attack from {attack.ip}:{attack.port}")
    
    # In a real scenario, this would send data to the collector service
    try:
        async with httpx.AsyncClient() as client:
            # We point to the local ingestor for this simulation
            ingest_url = os.getenv("TELEMETRY_INGESTOR_URL", "http://telemetry-ingestor:8000/ingest")
            response = await client.post(
                ingest_url,
                json={
                    "source": "honeypot_simulation",
                    "type": "malicious_scan",
                    "data": {
                        "ip": attack.ip,
                        "port": attack.port,
                        "raw_data": attack.data
                    }
                },
                timeout=5.0
            )
            response.raise_for_status()
            pn_logger.info(f"Simulated attack data sent to ingestor by {current_user.username}")
            return success_response(data={
                "message": "Simulated attack data sent to ingestor",
                "ingestor_response": response.json()
            })
    except Exception as e:
        pn_logger.error(f"Failed to send simulated attack: {str(e)}")
        return error_response(code="INGESTION_FAILED", message=f"Failed to send simulated attack: {str(e)}", status_code=500)
