from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import os
from sqlalchemy.orm import Session
from backend_api.shared.database import get_db
import httpx  # Import httpx
from typing import List, Dict, Any
from backend_api.blockchain_service.blockchain import Blockchain # Import Blockchain
from backend_api.iam_service.auth_methods import UserRole, has_role, get_current_user # Import UserRole, has_role, get_current_user
from backend_api.shared.schemas import TransactionData # Import TransactionData schema
from loguru import logger # Import logger
from datetime import datetime # Import datetime for timestamp
import json # Import json for serialization
import hashlib # Import hashlib for hashing
from backend_api.shared.database import get_db, Block # Import get_db, get_blockchain, and Block

# Import CommandDispatcher
from shared.command_dispatcher import CommandDispatcher

# This is a bit of a hack for now to make sure the orchestrator has a file to snapshot
# In a real system, this would be a path to a critical system file
DUMMY_SYSTEM_FILE = "dummy_system_state.txt"
if not os.path.exists(DUMMY_SYSTEM_FILE):
    with open(DUMMY_SYSTEM_FILE, "w") as f:
        f.write("Initial system state.")

# from phantomnet_agent.orchestrator import Orchestrator

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"]) # Add prefix to router

# Initialize the CommandDispatcher
command_dispatcher = CommandDispatcher()

def get_blockchain_instance(db: Session = Depends(get_db)) -> Blockchain:
    return Blockchain(db)

# def get_orchestrator(db: Session = Depends(get_db)) -> Orchestrator:
#     return Orchestrator(db_session=db, target_system_file=DUMMY_SYSTEM_FILE)


class ThreatData(BaseModel):
    threat_string: str


@router.post("/threats")
async def analyze_threat_endpoint(
    threat_data: ThreatData,
    # orchestrator: Orchestrator = Depends(get_orchestrator) # Commented out due to disabled functionality
):
    """
    Endpoint to analyze threat data using the Cognitive Core.
    Expects a JSON body with a "threat_string" key.
    """
    threat_string = threat_data.threat_string
    if not threat_string:
        raise HTTPException(
            status_code=400, detail="'threat_string' not provided in request body"
        )
    
    # analysis_result = orchestrator.cognitive_core.analyze_threat(threat_string)
    return {"detail": "Orchestrator threat analysis is currently disabled."}


@router.get(
    "/blockchain",
    dependencies=[
        Depends(has_role([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER]))
    ],
)
def get_blockchain_data(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    blocks = db.query(Block).order_by(Block.index).all()
    logger.info(
        f"User ID: {current_user['id']} fetched blockchain data." # Use ['id'] for dict
    )
    return {"chain": [block.to_dict() for block in blocks]}


@router.post("/blockchain/verify", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def verify_blockchain_integrity(db: Session = Depends(get_db)):
    blockchain_instance = Blockchain(db)
    is_valid = blockchain_instance.is_chain_valid()
    if is_valid:
        logger.info(
            "Blockchain integrity verified: All blocks are valid."
        )
        return {"message": "Blockchain integrity verified: All blocks are valid."}
    else:
        logger.warning(
            "Blockchain integrity compromised: Tampering detected."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Blockchain integrity compromised: Tampering detected.",
        )


# from phantomnet_agent.digital_twin import generator, deployer, models
# import yaml

@router.post("/digital_twin/render")
async def render_digital_twin(
    template_id: str, params: dict, current_user: dict = Depends(get_current_user)
):
    logger.warning("Digital twin rendering attempted, but functionality is disabled.")
    raise HTTPException(status_code=501, detail="Digital twin rendering is currently disabled.")


@router.post("/digital_twin/deploy")
async def deploy_digital_twin(
    current_user: dict = Depends(get_current_user) # Keeping current_user for potential generic logging/auth
):
    logger.warning("Digital twin deployment attempted, but functionality is disabled.")
    raise HTTPException(status_code=501, detail="Digital twin deployment is currently disabled.")


@router.post(
    "/blockchain/add_transaction", dependencies=[Depends(has_role([UserRole.ADMIN]))]
)
async def add_blockchain_transaction(
    transaction: TransactionData,
    current_user: dict = Depends(get_current_user),
    blockchain: Blockchain = Depends(get_blockchain_instance),  # Inject the Blockchain dependency
    db: Session = Depends(get_db),  # Inject the database session
):
    try:
        # Add a new transaction to the blockchain
        blockchain.new_transaction(
            sender="honeypot",  # The agent is the sender
            recipient=transaction.ip,
            amount=1,  # Placeholder, consider adding more meaningful data from transaction.data
        )

        # Mine a new block to record the transaction
        # Need to ensure blockchain.last_block is mocked or handled correctly
        last_block_obj = blockchain.last_block
        last_proof = (
            last_block_obj.proof if last_block_obj else 0
        )  # Get proof from the last block object
        previous_hash = (
            blockchain.hash(last_block_obj.to_dict()) if last_block_obj else "1"
        )  # Hash the last block object

        new_block_obj = blockchain.new_block(last_proof, previous_hash) # Use last_proof instead of undefined 'proof'
        db.add(new_block_obj)  # Add the new block to the session
        db.commit()  # Commit the new block to the database
        db.refresh(new_block_obj)  # Refresh to get the ID and other generated fields

        # Broadcast the new block event
        # Assuming broadcast_event is available in the main app
        # await broadcast_event(
        #     {"type": "new_block", "block": new_block_obj.to_dict()}
        # )  # Use to_dict() for broadcasting

        # Add event to Redis Stream
        # Assuming redis_client is available in the main app
        # redis_client.xadd(
        #     "blockchain_events",
        #     {
        #         "type": "new_block",
        #         "block_index": new_block_obj.index,
        #         "timestamp": new_block_obj.timestamp.isoformat(),
        #     },
        # )  # Use isoformat for datetime

        # Call the placeholder for smart contract interaction
        # if (
        #     new_block_obj.merkle_root
        # ):  # Only write if there are transactions and thus a Merkle root
        #     await write_merkle_root_to_contract(
        #         new_block_obj.merkle_root, new_block_obj.index
        #     )

        logger.info(
            f"Transaction added and block mined: {new_block_obj.index}"
        )  # Use logger
        return {
            "message": "Transaction added and block mined",
            "block_index": new_block_obj.index,
        }
    except Exception as e:
        db.rollback()  # Rollback changes in case of error
        logger.error(f"Error in add_blockchain_transaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the transaction.",
        )


from shared.schemas import TransactionData, HoneypotControl, SimulateAttack # Import TransactionData, HoneypotControl, SimulateAttack
import httpx # Import httpx

@router.post("/honeypot/control", dependencies=[Depends(has_role([UserRole.ADMIN]))])
async def honeypot_control(
    control: HoneypotControl, current_user: dict = Depends(get_current_user)
):
    if control.action == "start":
        logger.info(
            f"User ID: {current_user['id']} simulating starting honeypot on port {control.port}"
        )
        return {"message": f"Honeypot simulated to start on port {control.port}"}
    elif control.action == "stop":
        logger.info(
            f"User ID: {current_user['id']} simulating stopping honeypot on port {control.port}"
        )
        return {"message": f"Honeypot simulated to stop on port {control.port}"}
    else:
        logger.info(
            f"User ID: {current_user['id']} attempted invalid honeypot action: {control.action}"
        )
        raise HTTPException(
            status_code=400, detail="Invalid action. Must be 'start' or 'stop'."
        )


@router.post(
    "/honeypot/simulate_attack",
    dependencies=[Depends(has_role([UserRole.ADMIN, UserRole.ANALYST]))],
)
async def simulate_attack(
    attack: SimulateAttack, current_user: dict = Depends(get_current_user)
):
    logger.info(
        f"User ID: {current_user['id']} simulating attack from IP: {attack.ip} on port {attack.port} with data: [REDACTED]"
    )
    # In a real scenario, this would send data to the collector service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://collector:8001/logs/ingest",
                json={"ip": attack.ip, "port": attack.port, "data": attack.data},
            )
            response.raise_for_status()
            logger.info(
                f"Simulated attack data sent to collector by user ID: {current_user['id']}"
            )
            return {
                "message": "Simulated attack data sent to collector",
                "collector_response": response.json(),
            }
    except httpx.RequestError as e:
        logger.error(
            f"User ID: {current_user['id']} failed to send simulated attack to collector: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to send simulated attack to collector: {e}"
        )
