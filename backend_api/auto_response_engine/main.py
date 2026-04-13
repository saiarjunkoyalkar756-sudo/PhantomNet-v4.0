from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio
import datetime

# Assuming these imports from the soar_playbook_engine
# In a real microservice architecture, these would be API calls
# For now, we'll simulate direct access or use a shared database helper
from ..soar_playbook_engine import crud as playbook_crud
from ..soar_playbook_engine.database import get_db as get_playbook_db
from ..soar_playbook_engine.playbook_model import PlaybookRun

router = APIRouter()

async def execute_playbook_step(step: Dict[str, Any], playbook_run_id: int):
    """
    Simulates the execution of a single playbook step.
    In a real system, this would involve calling out to other microservices
    or interacting with external security controls.
    """
    action = step.get("action")
    parameters = step.get("parameters", {})
    
    print(f"Executing step for run {playbook_run_id}: Action '{action}' with params {parameters}")

    # Simulate delay for action execution
    await asyncio.sleep(2) 
    
    # Placeholder for actual action logic
    if action == "isolate_host":
        print(f"  -> Host '{parameters.get('host_id')}' isolated.")
        return {"status": "success", "message": f"Host {parameters.get('host_id')} isolated."}
    elif action == "block_ip":
        print(f"  -> IP '{parameters.get('ip_address')}' blocked.")
        return {"status": "success", "message": f"IP {parameters.get('ip_address')} blocked."}
    elif action == "create_ticket":
        print(f"  -> Ticket created with severity '{parameters.get('severity')}'.")
        return {"status": "success", "message": "Ticket created."}
    elif action == "await_human_approval":
        print(f"  -> Awaiting human approval for run {playbook_run_id}.")
        # This step would typically pause execution and wait for an API call to approve/reject
        # For simulation, we'll just 'pass'
        return {"status": "pending_approval", "message": "Awaiting human approval."}
    elif action == "evaluate_condition":
        print(f"  -> Evaluating condition: '{parameters.get('condition_logic')}'")
        # In a real system, this would evaluate a dynamic condition based on current context
        # For now, we'll always return true for simulation
        return {"status": "success", "result": True, "message": "Condition evaluated (simulated true)."}
    else:
        print(f"  -> Unknown action: {action}")
        return {"status": "failed", "message": f"Unknown action: {action}"}

async def execute_playbook_run_in_background(playbook_run_id: int, playbook_steps: List[Dict[str, Any]], db: Session):
    """
    Asynchronously executes all steps of a playbook run.
    Updates the playbook run status in the database.
    """
    current_status = "running"
    results = []
    
    for i, step in enumerate(playbook_steps):
        try:
            step_result = await execute_playbook_step(step, playbook_run_id)
            results.append({f"step_{i+1}": step_result})

            if step_result.get("status") == "failed":
                current_status = "failed"
                break
            elif step_result.get("status") == "pending_approval":
                current_status = "awaiting_approval"
                break # Pause execution until approved
        except Exception as e:
            print(f"Error executing step {i+1} for run {playbook_run_id}: {e}")
            results.append({f"step_{i+1}_error": str(e)})
            current_status = "failed"
            break
    
    if current_status == "running": # If all steps completed without failure or approval needed
        current_status = "completed"

    playbook_crud.update_playbook_run(
        db=db,
        run_id=playbook_run_id,
        status=current_status,
        result={"step_results": results, "final_status": current_status},
        completed_at=datetime.datetime.now()
    )
    print(f"Playbook run {playbook_run_id} finished with status: {current_status}")


@router.post("/execute/{playbook_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_playbook_execution(
    playbook_id: int,
    background_tasks: BackgroundTasks,
    triggered_by: Optional[str] = None,
    db: Session = Depends(get_playbook_db)
):
    """
    Triggers the execution of a specific playbook.
    The execution happens in the background.
    """
    playbook = playbook_crud.get_playbook(db, playbook_id=playbook_id)
    if not playbook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found.")
    
    if not playbook.approved_by_human and playbook.is_ai_generated:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI-generated playbook requires human approval before execution.")
        
    if not playbook.steps:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Playbook has no steps to execute.")

    # Create a new playbook run record
    new_run = playbook_crud.create_playbook_run(db=db, playbook_id=playbook_id, triggered_by=triggered_by)
    
    # Schedule the actual execution in a background task
    background_tasks.add_task(execute_playbook_run_in_background, new_run.id, playbook.steps, db)
    
    return {"message": f"Playbook '{playbook.name}' execution triggered for run ID: {new_run.id}", "run_id": new_run.id}

@router.post("/resume/{playbook_run_id}/approve", status_code=status.HTTP_200_OK)
async def resume_playbook_after_approval(
    playbook_run_id: int,
    approver_id: str,
    approved: bool,
    background_tasks: BackgroundTasks,
    notes: Optional[str] = None,
    db: Session = Depends(get_playbook_db)
):
    """
    Resumes a playbook run that was awaiting human approval.
    """
    db_run = playbook_crud.get_playbook_run(db, run_id=playbook_run_id)
    if not db_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook run not found.")

    if db_run.status != "awaiting_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Playbook run is not awaiting approval.")

    # Record the approval decision
    playbook_crud.create_playbook_approval(
        db=db,
        playbook_run_id=playbook_run_id,
        approver_id=approver_id,
        approved=approved,
        approval_notes=notes
    )

    if approved:
        # Update status to running and resume execution
        playbook_crud.update_playbook_run(db=db, run_id=playbook_run_id, status="running")
        
        # In a more complex system, the playbook state would need to be stored
        # and execution resumed from the exact point of pause.
        # For this simplified version, we'll re-fetch playbook and restart.
        # This simplification assumes approval acts as a 'gate' for the next step.
        playbook = playbook_crud.get_playbook(db, playbook_id=db_run.playbook_id)
        if not playbook:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated playbook not found.")

        # Simulate resuming by executing the remaining steps
        # A robust solution would store and retrieve the exact next step to execute
        # and pass it to the background task.
        # For now, we'll assume the approval step was the last one processed
        # and the next step in the linear list is what to execute.
        # This part needs refinement for truly complex workflows with pauses mid-playbook.
        background_tasks.add_task(execute_playbook_run_in_background, db_run.id, playbook.steps, db)
        return {"message": f"Playbook run {playbook_run_id} approved and resumed.", "run_id": playbook_run_id}
    else:
        # Mark as failed or rejected
        playbook_crud.update_playbook_run(db=db, run_id=playbook_run_id, status="rejected", completed_at=datetime.datetime.now())
        return {"message": f"Playbook run {playbook_run_id} rejected.", "run_id": playbook_run_id}
