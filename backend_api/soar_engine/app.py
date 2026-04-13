from fastapi import FastAPI, HTTPException, status, Query, APIRouter, Depends # Add Depends
from pydantic import BaseModel
import logging
import yaml
import os
import asyncio # Import asyncio
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager # Import for lifespan
import uvicorn # Import uvicorn for standalone execution
from sqlalchemy.orm import Session # Import Session for DB dependency
from sqlalchemy.exc import IntegrityError # Import for handling unique constraints

from .kafka_consumer import consume_kafka_messages, stop_soar_consumer_task # Import Kafka consumer functions
from .soar_playbook_engine import SOARPlaybookEngine
from .playbook_flow_builder import AIPlaybookGenerator
from .auto_response_engine import AutoResponseEngine
from .human_in_the_loop import HumanInTheLoop, ApprovalRequest
from .models import Playbook, PlaybookStep, PlaybookRun, PlaybookStatus, RemediationAction # Import models
from backend_api.shared.database import get_db, PlaybookDB, PlaybookRunDB, PlaybookExecutionLogDB # Import DB models

from shared.logger_config import logger

router = APIRouter(prefix="/soar", tags=["SOAR"])

# Initialize SOAR components
soar_engine = SOARPlaybookEngine()
ai_playbook_generator = AIPlaybookGenerator()
auto_response_engine = AutoResponseEngine()
human_in_the_loop = HumanInTheLoop()

# Removed: from .state import playbooks_store, playbook_runs
# Playbooks and playbook runs are now managed in the database

def load_playbooks(db: Session):
    """
    Loads playbooks from YAML files and ensures they are in the database.
    Updates existing playbooks or creates new ones.
    """
    playbooks_dir = os.path.join(os.path.dirname(__file__), "playbooks")
    if not os.path.exists(playbooks_dir):
        logger.warning(f"Playbooks directory not found: {playbooks_dir}. Skipping playbook loading.")
        return

    for filename in os.listdir(playbooks_dir):
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            filepath = os.path.join(playbooks_dir, filename)
            with open(filepath, "r") as f:
                try:
                    playbook_data = yaml.safe_load(f)
                    
                    playbooks_to_process = []
                    if isinstance(playbook_data, list):
                        playbooks_to_process.extend(playbook_data)
                    elif isinstance(playbook_data, dict):
                        playbooks_to_process.append(playbook_data)
                    else:
                        logger.error(f"Invalid playbook format in {filename}: Expected dict or list of dicts.")
                        continue

                    for pb_data in playbooks_to_process:
                        try:
                            playbook_pydantic = Playbook(**pb_data) # Validate with Pydantic model
                            
                            # Check if playbook already exists by name
                            existing_playbook_db = db.query(PlaybookDB).filter(PlaybookDB.name == playbook_pydantic.name).first()

                            if existing_playbook_db:
                                # Update existing playbook
                                existing_playbook_db.description = playbook_pydantic.description
                                existing_playbook_db.trigger = playbook_pydantic.trigger.model_dump_json() if playbook_pydantic.trigger else None
                                existing_playbook_db.steps = [step.model_dump() for step in playbook_pydantic.steps]
                                existing_playbook_db.context = playbook_pydantic.context
                                db.add(existing_playbook_db)
                                logger.info(f"Updated playbook in DB: {playbook_pydantic.name} from {filename}")
                            else:
                                # Create new playbook
                                new_playbook_db = PlaybookDB(
                                    name=playbook_pydantic.name,
                                    description=playbook_pydantic.description,
                                    trigger=playbook_pydantic.trigger.model_dump_json() if playbook_pydantic.trigger else None,
                                    steps=[step.model_dump() for step in playbook_pydantic.steps],
                                    context=playbook_pydantic.context
                                )
                                db.add(new_playbook_db)
                                logger.info(f"Loaded new playbook to DB: {playbook_pydantic.name} from {filename}")
                            db.commit()
                        except IntegrityError:
                            db.rollback()
                            logger.error(f"Integrity error (e.g., duplicate name) for playbook from {filename}: {playbook_pydantic.name}")
                        except Exception as e:
                            logger.error(f"Error processing playbook '{pb_data.get('name', 'Unknown')}' from {filename}: {e}", exc_info=True)

                except yaml.YAMLError as e:
                    logger.error(f"Error loading playbook from {filename}: {e}")
                except Exception as e:
                    logger.error(
                        f"Invalid playbook format in {filename}: {e}", exc_info=True
                    )

# New startup function for SOAR
soar_consumer_task: Optional[asyncio.Task] = None

async def soar_startup():
    logger.info("SOAR Engine starting up...")
    db = next(get_db()) # Get a DB session
    load_playbooks(db) # Pass DB session to load_playbooks
    db.close() # Close session after use
    global soar_consumer_task
    soar_consumer_task = asyncio.create_task(consume_kafka_messages())
    logger.info("SOAR Kafka consumer task for SOAR alerts started.")

async def soar_shutdown():
    logger.info("SOAR Engine shutting down...")
    await stop_soar_consumer_task()
    logger.info("SOAR Kafka consumer task stopped.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await soar_startup()
    yield
    await soar_shutdown()

app = FastAPI(title="SOAR Engine", lifespan=lifespan)
app.include_router(router, prefix="/api")


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "SOAR Engine is healthy"}

@router.get("/playbooks", response_model=List[Playbook])
async def get_all_playbooks(db: Session = Depends(get_db)):
    """Retrieve all loaded playbooks."""
    playbooks_db = db.query(PlaybookDB).all()
    return [Playbook(
        name=pb.name,
        description=pb.description,
        trigger=json.loads(pb.trigger), # Deserialize JSON string back to dict
        steps=[PlaybookStep(**step) for step in pb.steps] if pb.steps else [], # Deserialize steps
        context=pb.context # Already a dict
    ) for pb in playbooks_db]

@router.get("/playbooks/{playbook_name}", response_model=Playbook)
async def get_playbook_by_name(playbook_name: str, db: Session = Depends(get_db)):
    """Retrieve a specific playbook by name."""
    playbook_db = db.query(PlaybookDB).filter(PlaybookDB.name == playbook_name).first()
    if not playbook_db:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return Playbook(
        name=playbook_db.name,
        description=playbook_db.description,
        trigger=json.loads(playbook_db.trigger),
        steps=[PlaybookStep(**step) for step in playbook_db.steps] if playbook_db.steps else [],
        context=playbook_db.context
    )

@router.post("/playbooks/{playbook_name}/execute", response_model=PlaybookRun)
async def execute_playbook(playbook_name: str, incident_context: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Triggers the execution of a specific playbook for a given incident context.
    """
    playbook_db = db.query(PlaybookDB).filter(PlaybookDB.name == playbook_name).first()
    if not playbook_db:
        raise HTTPException(status_code=404, detail=f"Playbook '{playbook_name}' not found.")
    
    # Transform PlaybookDB to Pydantic Playbook model for execution logic
    playbook_pydantic = Playbook(
        name=playbook_db.name,
        description=playbook_db.description,
        trigger=json.loads(playbook_db.trigger),
        steps=[PlaybookStep(**step) for step in playbook_db.steps] if playbook_db.steps else [],
        context=playbook_db.context
    )

    # Create a new playbook run instance in DB
    playbook_run_db = PlaybookRunDB(
        playbook_id=playbook_db.id,
        playbook_name=playbook_db.name,
        status=PlaybookStatus.RUNNING.value, # Initial status
        triggered_by=incident_context,
        current_context={"incident": incident_context}, # Initialize context
    )
    db.add(playbook_run_db)
    db.commit()
    db.refresh(playbook_run_db)

    # Transform PlaybookRunDB to Pydantic PlaybookRun model for execution logic
    playbook_run_pydantic = PlaybookRun(
        run_id=playbook_run_db.id,
        playbook_name=playbook_run_db.playbook_name,
        status=PlaybookStatus(playbook_run_db.status),
        triggered_by=playbook_run_db.triggered_by,
        start_time=playbook_run_db.start_time,
        end_time=playbook_run_db.end_time,
        current_context=playbook_run_db.current_context,
        playbook=playbook_pydantic,
        execution_logs=[] # Will be populated by soar_engine
    )
    
    # Execute the playbook in a background task
    # soar_engine will update playbook_run_db and commit changes
    asyncio.create_task(soar_engine.execute_playbook_run(playbook_run_pydantic, playbook_run_db, db))
    logger.info(f"Playbook '{playbook_name}' execution started (Run ID: {playbook_run_pydantic.run_id}).")
    return playbook_run_pydantic

@router.get("/playbook_runs/{run_id}", response_model=PlaybookRun)
async def get_playbook_run_status(run_id: str, db: Session = Depends(get_db)):
    """Retrieves the current status and logs of a playbook run."""
    playbook_run_db = db.query(PlaybookRunDB).filter(PlaybookRunDB.id == run_id).first()
    if not playbook_run_db:
        raise HTTPException(status_code=404, detail="Playbook run not found.")
    
    # Fetch associated playbook for full PlaybookRun Pydantic model
    playbook_db = db.query(PlaybookDB).filter(PlaybookDB.id == playbook_run_db.playbook_id).first()
    if not playbook_db:
        # This should ideally not happen if foreign keys are enforced
        raise HTTPException(status_code=500, detail="Associated playbook not found for this run.")

    # Fetch execution logs
    execution_logs_db = db.query(PlaybookExecutionLogDB).filter(PlaybookExecutionLogDB.playbook_run_id == run_id).order_by(PlaybookExecutionLogDB.timestamp).all()
    
    return PlaybookRun(
        run_id=playbook_run_db.id,
        playbook_name=playbook_run_db.playbook_name,
        status=PlaybookStatus(playbook_run_db.status),
        triggered_by=playbook_run_db.triggered_by,
        start_time=playbook_run_db.start_time,
        end_time=playbook_run_db.end_time,
        current_context=playbook_run_db.current_context,
        playbook=Playbook(
            name=playbook_db.name,
            description=playbook_db.description,
            trigger=json.loads(playbook_db.trigger),
            steps=[PlaybookStep(**step) for step in playbook_db.steps] if playbook_db.steps else [],
            context=playbook_db.context
        ),
        execution_logs=[PlaybookExecutionLog(
            timestamp=log.timestamp,
            step_action=log.step_action,
            status=PlaybookStatus(log.status),
            details=log.details,
            output=log.output
        ) for log in execution_logs_db]
    )

@router.post("/playbooks/generate", response_model=Playbook)
async def generate_playbook_ai(incident: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Generates a new playbook using AI based on incident details.
    """
    generated_playbook = await ai_playbook_generator.generate_playbook_from_incident(incident)
    
    # Store the generated playbook in the database
    new_playbook_db = PlaybookDB(
        name=generated_playbook.name,
        description=generated_playbook.description,
        trigger=generated_playbook.trigger.model_dump_json() if generated_playbook.trigger else None,
        steps=[step.model_dump() for step in generated_playbook.steps],
        context=generated_playbook.context
    )
    db.add(new_playbook_db)
    db.commit()
    db.refresh(new_playbook_db)

    logger.info(f"AI generated playbook and saved to DB: {generated_playbook.name}")
    return generated_playbook

@router.get("/approvals", response_model=List[ApprovalRequest])
async def get_pending_approvals():
    """Retrieves all pending human approval requests."""
    return list(human_in_the_loop.pending_approvals.values())

@router.post("/approvals/{request_id}/approve", response_model=ApprovalRequest)
async def approve_playbook_step(request_id: str, approved_by: str = Query(..., description="User who approved the request."), reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Approves a pending playbook step, allowing its execution to proceed."""
    approved_req = await human_in_the_loop.approve_request(request_id, approved_by, reason)
    if not approved_req:
        raise HTTPException(status_code=404, detail=f"Approval request {request_id} not found or not pending.")
    
    # Update PlaybookRunDB status
    playbook_run_db = db.query(PlaybookRunDB).filter(PlaybookRunDB.id == approved_req.playbook_run_id).first()
    if playbook_run_db:
        playbook_run_db.status = PlaybookStatus.RUNNING.value # Or appropriate status after approval
        playbook_run_db.execution_logs.append(PlaybookExecutionLogDB(
            timestamp=datetime.utcnow(),
            step_action=f"Approval for {approved_req.step_name}",
            status=PlaybookStatus.COMPLETED.value,
            details={"approved_by": approved_by, "reason": reason},
            output={"message": "Step approved."}
        ))
        db.add(playbook_run_db)
        db.commit()
        db.refresh(playbook_run_db)
        logger.info(f"Approval for {request_id} granted. Playbook run {approved_req.playbook_run_id} status updated.")
    else:
        logger.warning(f"Playbook run {approved_req.playbook_run_id} not found for approval request {request_id}.")

    # Trigger resume of playbook execution (conceptual, would involve messaging)
    logger.info(f"Approval for {request_id} granted. Signalling SOAR engine to resume.")
    # In a real system, you'd send a message to the SOARPlaybookEngine via a queue
    # to resume the specific playbook run from the approved step.
    return approved_req

@router.post("/approvals/{request_id}/reject", response_model=ApprovalRequest)
async def reject_playbook_step(request_id: str, rejected_by: str = Query(..., description="User who rejected the request."), reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Rejects a pending playbook step, preventing its execution."""
    rejected_req = await human_in_the_loop.reject_request(request_id, rejected_by, reason)
    if not rejected_req:
        raise HTTPException(status_code=404, detail=f"Approval request {request_id} not found or not pending.")
    
    # Update PlaybookRunDB status
    playbook_run_db = db.query(PlaybookRunDB).filter(PlaybookRunDB.id == rejected_req.playbook_run_id).first()
    if playbook_run_db:
        playbook_run_db.status = PlaybookStatus.REJECTED.value # Or appropriate status after rejection
        playbook_run_db.execution_logs.append(PlaybookExecutionLogDB(
            timestamp=datetime.utcnow(),
            step_action=f"Rejection for {rejected_req.step_name}",
            status=PlaybookStatus.FAILED.value, # Rejection usually means a failed step
            details={"rejected_by": rejected_by, "reason": reason},
            output={"message": "Step rejected."}
        ))
        db.add(playbook_run_db)
        db.commit()
        db.refresh(playbook_run_db)
        logger.info(f"Approval for {request_id} rejected. Playbook run {rejected_req.playbook_run_id} status updated.")
    else:
        logger.warning(f"Playbook run {rejected_req.playbook_run_id} not found for rejection request {request_id}.")

    # Signal playbook to mark step as failed and potentially stop
    logger.info(f"Approval for {request_id} rejected. Signalling SOAR engine to mark step as failed.")
    return rejected_req

# Conceptual Integration with Threat Intelligence Service (Moved to soar_playbook_engine for direct usage)
# --- End Conceptual Integration ---
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8016, reload=True) # Assuming 8016 is the port for SOAR engine
