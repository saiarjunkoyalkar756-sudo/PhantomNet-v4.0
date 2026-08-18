from backend_api.shared.service_factory import create_phantom_service
import yaml
import os
import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .consumer import consume_kafka_messages, stop_soar_consumer_task
from .soar_playbook_engine import SOARPlaybookEngine
from .playbook_flow_builder import AIPlaybookGenerator
from .auto_response_engine import AutoResponseEngine
from .human_in_the_loop import HumanInTheLoop, ApprovalRequest
from .models import Playbook, PlaybookStep, PlaybookRun, PlaybookStatus, RemediationAction
from .governed_api import router as governed_containment_router
from .governed_containment import init_governed_containment_store
from backend_api.shared.database import SessionLocal, PlaybookDB, PlaybookRunDB, PlaybookExecutionLogDB

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from loguru import logger
from backend_api.core.response import success_response, error_response
from fastapi import APIRouter, FastAPI, Depends, Query, HTTPException

router = APIRouter(prefix="/soar", tags=["SOAR"])

# Initialize SOAR components
soar_engine = SOARPlaybookEngine()
ai_playbook_generator = AIPlaybookGenerator()
auto_response_engine = AutoResponseEngine()
human_in_the_loop = HumanInTheLoop()

def load_playbooks(db: Session):
    """Loads playbooks from YAML files and ensures they are in the database."""
    playbooks_dir = os.path.join(os.path.dirname(__file__), "playbooks")
    if not os.path.exists(playbooks_dir):
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
                    
                    for pb_data in playbooks_to_process:
                        try:
                            playbook_pydantic = Playbook(**pb_data)
                            existing_playbook_db = db.query(PlaybookDB).filter(PlaybookDB.name == playbook_pydantic.name).first()

                            if existing_playbook_db:
                                existing_playbook_db.description = playbook_pydantic.description
                                existing_playbook_db.trigger = json.dumps(playbook_pydantic.trigger) if playbook_pydantic.trigger else None
                                existing_playbook_db.steps = [step.model_dump() for step in playbook_pydantic.steps]
                                existing_playbook_db.context = playbook_pydantic.context
                                db.add(existing_playbook_db)
                            else:
                                new_playbook_db = PlaybookDB(
                                    name=playbook_pydantic.name,
                                    description=playbook_pydantic.description,
                                    trigger=json.dumps(playbook_pydantic.trigger) if playbook_pydantic.trigger else None,
                                    steps=[step.model_dump() for step in playbook_pydantic.steps],
                                    context=playbook_pydantic.context
                                )
                                db.add(new_playbook_db)
                            db.commit()
                        except Exception as e:
                            logger.error(f"SOAR: Failed to load playbook {pb_data.get('name')}: {e}")
                            db.rollback()
                except Exception as e:
                    logger.error(f"SOAR: Failed to read playbook file {filename}: {e}")

async def soar_startup(app: FastAPI):
    # Startup tasks
    logger.info("SOAR Engine: Loading playbooks...")
    db = next(get_db())
    load_playbooks(db)
    db.close()
    await init_governed_containment_store()
    
    app.state.consumer_task = asyncio.create_task(consume_kafka_messages())
    logger.info("SOAR Engine: Kafka consumer task started.")

async def soar_shutdown(app: FastAPI):
    logger.info("SOAR Engine: Shutting down consumer...")
    await stop_soar_consumer_task()
    if hasattr(app.state, "consumer_task"):
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
    logger.info("SOAR Engine: Consumer stopped.")

app = create_phantom_service(
    name="SOAR Engine",
    description="Orchestration and Automation for incident response.",
    version="1.0.0",
    custom_startup=soar_startup,
    custom_shutdown=soar_shutdown
)

@router.get("/playbooks")
async def get_all_playbooks(db: Session = Depends(get_db)):
    load_playbooks(db)
    playbooks_db = db.query(PlaybookDB).all()
    data = [Playbook(
        name=pb.name,
        description=pb.description,
        trigger=json.loads(pb.trigger) if pb.trigger else {},
        steps=[PlaybookStep(**step) for step in pb.steps] if pb.steps else [],
        context=pb.context
    ) for pb in playbooks_db]
    return success_response(data=data)

@router.get("/playbooks/{playbook_name}")
async def get_playbook_by_name(playbook_name: str, db: Session = Depends(get_db)):
    load_playbooks(db)
    playbook_db = db.query(PlaybookDB).filter(PlaybookDB.name == playbook_name).first()
    if not playbook_db:
        return error_response(code="NOT_FOUND", message="Playbook not found", status_code=404)
    data = Playbook(
        name=playbook_db.name,
        description=playbook_db.description,
        trigger=json.loads(playbook_db.trigger) if playbook_db.trigger else {},
        steps=[PlaybookStep(**step) for step in playbook_db.steps] if playbook_db.steps else [],
        context=playbook_db.context
    )
    return success_response(data=data)

@router.post("/playbooks/{playbook_name}/execute")
async def execute_playbook(playbook_name: str, incident_context: Dict[str, Any], db: Session = Depends(get_db)):
    load_playbooks(db)
    playbook_db = db.query(PlaybookDB).filter(PlaybookDB.name == playbook_name).first()
    if not playbook_db:
        return error_response(code="NOT_FOUND", message="Playbook not found", status_code=404)
    
    playbook_run_db = PlaybookRunDB(
        playbook_id=playbook_db.id,
        playbook_name=playbook_db.name,
        status=PlaybookStatus.IN_PROGRESS.value,
        triggered_by=incident_context,
        current_context={"incident": incident_context},
    )
    db.add(playbook_run_db)
    db.commit()
    db.refresh(playbook_run_db)

    # Automatically execute the playbook steps so it produces actual logs and populates soar_execution.log
    from .models import Playbook, PlaybookRun, PlaybookStep
    from .consumer import execute_playbook as run_soar_playbook
    from backend_api.shared.database import PlaybookExecutionLogDB

    try:
        playbook_pydantic = Playbook(
            name=playbook_db.name,
            description=playbook_db.description,
            trigger=json.loads(playbook_db.trigger) if playbook_db.trigger else {},
            steps=[PlaybookStep(**step) for step in playbook_db.steps] if playbook_db.steps else [],
            context=playbook_db.context or {}
        )
        
        playbook_run_pydantic = PlaybookRun(
            run_id=playbook_run_db.id,
            playbook_name=playbook_db.name,
            triggered_by=incident_context,
            playbook=playbook_pydantic,
            current_context={"incident": incident_context}
        )
        
        run_soar_playbook(playbook_run_pydantic)

        playbook_run_db.status = playbook_run_pydantic.status.value
        playbook_run_db.end_time = playbook_run_pydantic.end_time
        
        playbook_run_db.execution_logs = []
        for log in playbook_run_pydantic.execution_logs:
            exec_log_db = PlaybookExecutionLogDB(
                timestamp=log.timestamp,
                step_action=log.step_action.value,
                status=log.status.value,
                details={"message": log.details},
                output=log.output
            )
            playbook_run_db.execution_logs.append(exec_log_db)
            
        db.add(playbook_run_db)
        db.commit()
        db.refresh(playbook_run_db)
    except Exception as e:
        logger.error(f"Failed to execute playbook in endpoint background: {e}", exc_info=True)
        # Mark as failed in DB
        playbook_run_db.status = PlaybookStatus.FAILED.value
        playbook_run_db.end_time = datetime.now(timezone.utc)
        db.add(playbook_run_db)
        db.commit()

    return success_response(data={"run_id": playbook_run_db.id, "status": playbook_run_db.status})

@router.get("/playbook_runs/{run_id}")
async def get_playbook_run_status(run_id: str, db: Session = Depends(get_db)):
    playbook_run_db = db.query(PlaybookRunDB).filter(PlaybookRunDB.id == run_id).first()
    if not playbook_run_db:
        return error_response(code="NOT_FOUND", message="Playbook run not found", status_code=404)
    
    return success_response(data={
        "run_id": playbook_run_db.id,
        "status": playbook_run_db.status,
        "playbook_name": playbook_run_db.playbook_name
    })

@router.post("/playbooks/generate")
async def generate_playbook_ai(incident: Dict[str, Any], db: Session = Depends(get_db)):
    generated_playbook = await ai_playbook_generator.generate_playbook_from_incident(incident)
    return success_response(data=generated_playbook)

@router.get("/approvals")
async def get_pending_approvals():
    return success_response(data=list(human_in_the_loop.pending_approvals.values()))

@router.post("/approvals/{request_id}/approve", response_model=ApprovalRequest)
async def approve_playbook_step(request_id: str, approved_by: str = Query(..., description="User who approved the request."), reason: Optional[str] = None, db: Session = Depends(get_db)):
    approved_req = await human_in_the_loop.approve_request(request_id, approved_by, reason)
    if not approved_req:
        raise HTTPException(status_code=404, detail=f"Approval request {request_id} not found or not pending.")
    
    playbook_run_db = db.query(PlaybookRunDB).filter(PlaybookRunDB.id == approved_req.playbook_run_id).first()
    if playbook_run_db:
        playbook_run_db.status = PlaybookStatus.IN_PROGRESS.value
        playbook_run_db.execution_logs.append(PlaybookExecutionLogDB(
            timestamp=datetime.now(timezone.utc),
            step_action=f"Approval for {approved_req.step_name}",
            status=PlaybookStatus.COMPLETED.value,
            details={"approved_by": approved_by, "reason": reason},
            output={"message": "Step approved."}
        ))
        db.add(playbook_run_db)
        db.commit()
    return approved_req

@router.post("/approvals/{request_id}/reject", response_model=ApprovalRequest)
async def reject_playbook_step(request_id: str, rejected_by: str = Query(..., description="User who rejected the request."), reason: Optional[str] = None, db: Session = Depends(get_db)):
    rejected_req = await human_in_the_loop.reject_request(request_id, rejected_by, reason)
    if not rejected_req:
        raise HTTPException(status_code=404, detail=f"Approval request {request_id} not found or not pending.")
    
    playbook_run_db = db.query(PlaybookRunDB).filter(PlaybookRunDB.id == rejected_req.playbook_run_id).first()
    if playbook_run_db:
        playbook_run_db.status = PlaybookStatus.REJECTED.value
        playbook_run_db.execution_logs.append(PlaybookExecutionLogDB(
            timestamp=datetime.now(timezone.utc),
            step_action=f"Rejection for {rejected_req.step_name}",
            status=PlaybookStatus.FAILED.value,
            details={"rejected_by": rejected_by, "reason": reason},
            output={"message": "Step rejected."}
        ))
        db.add(playbook_run_db)
        db.commit()
    return rejected_req

app.include_router(router, prefix="/api")
app.include_router(governed_containment_router, prefix="/api/soar")
