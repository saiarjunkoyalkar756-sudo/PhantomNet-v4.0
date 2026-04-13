# backend_api/soar_engine/human_in_the_loop.py

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from shared.logger_config import logger
from .models import PlaybookRun, PlaybookStatus, PlaybookExecutionLog, PlaybookStep # Import relevant models

logger = logger

class ApprovalRequest(BaseModel):
    """Represents a request for human approval."""
    request_id: str
    playbook_run_id: str
    step_index: int
    step_description: str
    context_snapshot: Dict[str, Any]
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    status: PlaybookStatus = PlaybookStatus.REQUIRES_APPROVAL
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    reason: Optional[str] = None

class HumanInTheLoop:
    """
    Manages human approval workflows for SOAR playbook steps.
    """
    def __init__(self):
        self.pending_approvals: Dict[str, ApprovalRequest] = {} # Store pending approval requests
        logger.info("HumanInTheLoop module initialized.")

    async def create_approval_request(self, playbook_run: PlaybookRun, step_index: int) -> ApprovalRequest:
        """
        Creates a new approval request for a playbook step.
        """
        step = playbook_run.playbook.steps[step_index]
        request_id = f"approval-{playbook_run.run_id}-{step_index}"
        
        approval_request = ApprovalRequest(
            request_id=request_id,
            playbook_run_id=playbook_run.run_id,
            step_index=step_index,
            step_description=step.description or step.action,
            context_snapshot=playbook_run.current_context, # Snapshot current state for decision
        )
        self.pending_approvals[request_id] = approval_request
        
        # Update playbook run status
        playbook_run.execution_logs.append(PlaybookExecutionLog(
            step_action=step.action,
            timestamp=datetime.utcnow(),
            status=PlaybookStatus.REQUIRES_APPROVAL,
            details=f"Step '{step.action}' requires human approval. Request ID: {request_id}",
            output={"request_id": request_id}
        ))
        playbook_run.status = PlaybookStatus.REQUIRES_APPROVAL # Overall playbook status

        logger.info(f"Created approval request {request_id} for playbook run {playbook_run.run_id}, step {step_index}.")
        return approval_request

    async def approve_request(self, request_id: str, approved_by: str, reason: Optional[str] = None) -> Optional[ApprovalRequest]:
        """
        Approves a pending request and updates its status.
        """
        approval_request = self.pending_approvals.get(request_id)
        if not approval_request:
            logger.warning(f"Approval request {request_id} not found.")
            return None
        
        if approval_request.status != PlaybookStatus.REQUIRES_APPROVAL:
            logger.warning(f"Approval request {request_id} is not in PENDING state. Current status: {approval_request.status}.")
            return None

        approval_request.status = PlaybookStatus.APPROVED
        approval_request.approved_by = approved_by
        approval_request.approved_at = datetime.utcnow()
        approval_request.reason = reason
        
        del self.pending_approvals[request_id] # Remove from pending
        logger.info(f"Approval request {request_id} approved by {approved_by}.")
        
        # In a real system, this would signal the SOARPlaybookEngine to resume execution
        # For now, it just updates the status.
        return approval_request

    async def reject_request(self, request_id: str, rejected_by: str, reason: Optional[str] = None) -> Optional[ApprovalRequest]:
        """
        Rejects a pending request and updates its status.
        """
        approval_request = self.pending_approvals.get(request_id)
        if not approval_request:
            logger.warning(f"Approval request {request_id} not found.")
            return None

        if approval_request.status != PlaybookStatus.REQUIRES_APPROVAL:
            logger.warning(f"Approval request {request_id} is not in PENDING state. Current status: {approval_request.status}.")
            return None

        approval_request.status = PlaybookStatus.REJECTED
        # In a real system, you'd mark the playbook run as failed or require a new path
        approval_request.approved_by = rejected_by # Reusing field for who rejected
        approval_request.approved_at = datetime.utcnow()
        approval_request.reason = reason
        
        del self.pending_approvals[request_id] # Remove from pending
        logger.info(f"Approval request {request_id} rejected by {rejected_by}.")
        return approval_request

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running HumanInTheLoop example...")
    
    # Needs a mock PlaybookRun and Playbook for example
    from .models import Playbook, PlaybookStep, PlaybookRun, RemediationAction
    import uuid
    
    mock_playbook = Playbook(
        name="test_human_approval",
        description="A playbook with a step requiring human approval.",
        trigger={"event_type": "high_risk_action"},
        steps=[
            PlaybookStep(action=RemediationAction.ENRICH_INDICATOR, tool_name="ThreatIntel", parameters={"value": "1.1.1.1", "type": "ip"}),
            PlaybookStep(action=RemediationAction.ISOLATE_HOST, tool_name="EDR", parameters={"host_id": "critical-server-01"}, requires_approval=True, description="Isolate critical server."),
            PlaybookStep(action=RemediationAction.NOTIFY_USER, tool_name="Messaging", parameters={"user_id": "soc_lead", "message": "Host isolated."})
        ]
    )
    
    mock_playbook_run = PlaybookRun(
        run_id=str(uuid.uuid4()),
        playbook_name=mock_playbook.name,
        triggered_by={"event": "high_risk_event"},
        playbook=mock_playbook,
        current_context={"incident": {"source_ip": "1.1.1.1", "host_id": "critical-server-01"}}
    )

    async def run_example():
        hitl = HumanInTheLoop()
        
        # Simulate playbook reaching an approval step
        # For this example, we manually create the request after step 0
        step_index_requiring_approval = 1 
        
        # First step (automated)
        # This part would normally be handled by SOARPlaybookEngine
        log_entry_step0 = PlaybookExecutionLog(
            step_action=RemediationAction.ENRICH_INDICATOR,
            timestamp=datetime.utcnow(),
            status=PlaybookStatus.COMPLETED,
            details="Enriched indicator.",
            output={"enriched_ip": {"reputation_score": 90}}
        )
        mock_playbook_run.execution_logs.append(log_entry_step0)
        mock_playbook_run.current_context["enriched_ip"] = {"reputation_score": 90}


        # Now, simulate the SOAR engine realizing step 1 requires approval
        approval_req = await hitl.create_approval_request(mock_playbook_run, step_index_requiring_approval)
        logger.info(f"Approval request created: {approval_req.model_dump_json(indent=2)}")
        
        logger.info(f"Current Playbook Run Status after approval request:\n{mock_playbook_run.model_dump_json(indent=2)}")

        # Simulate human approval
        await asyncio.sleep(2) # Simulate delay for human
        approved_request = await hitl.approve_request(approval_req.request_id, "SOC Analyst 1", "Confirmed critical impact.")
        logger.info(f"Approved Request: {approved_request.model_dump_json(indent=2)}")

        # If approved, SOARPlaybookEngine would then execute the step.
        # This part is outside HITL module's direct responsibility but part of the overall flow.
        logger.info("SOARPlaybookEngine would now execute the approved step.")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("HumanInTheLoop example stopped.")
