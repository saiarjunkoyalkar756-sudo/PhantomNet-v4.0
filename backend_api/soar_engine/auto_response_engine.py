# backend_api/soar_engine/auto_response_engine.py

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.logger_config import logger
from .models import PlaybookRun, PlaybookStatus, RemediationAction # Import relevant models

logger = logger

class AutoResponseEngine:
    """
    Automates decision-making and remediation actions within SOAR playbooks,
    handling steps that do not require human-in-the-loop approval.
    """
    def __init__(self):
        logger.info("AutoResponseEngine initialized.")
        # In a real system, this might track ongoing automated actions

    async def execute_automated_step(self, playbook_run: PlaybookRun, step_index: int) -> PlaybookRun:
        """
        Executes a single playbook step that does not require human approval.
        Updates the playbook_run with execution logs.
        """
        if step_index >= len(playbook_run.playbook.steps):
            logger.warning(f"Attempted to execute step {step_index} for playbook run {playbook_run.run_id}, but step does not exist.")
            return playbook_run

        step = playbook_run.playbook.steps[step_index]
        
        if step.requires_approval:
            logger.warning(f"Step '{step.action}' in playbook run {playbook_run.run_id} requires human approval. AutoResponseEngine will not execute.")
            return playbook_run
        
        logger.info(f"Auto-executing step '{step.action}' for playbook run {playbook_run.run_id}.")

        log_entry_data = {
            "step_action": step.action,
            "timestamp": datetime.utcnow(),
            "status": PlaybookStatus.IN_PROGRESS,
            "details": f"Auto-executing step: {step.description or step.action}",
            "output": {}
        }
        
        try:
            # Evaluate condition before executing
            # NOTE: _evaluate_condition needs access to playbook_run.current_context
            # For simplicity, passing full context directly.
            # In a full refactor, context management would be more central.
            from .soar_playbook_engine import SOARPlaybookEngine # Avoid circular by importing here
            engine = SOARPlaybookEngine() # Re-initialize or pass existing
            
            if step.condition and not await engine._evaluate_condition(step.condition, playbook_run.current_context):
                log_entry_data["status"] = PlaybookStatus.SKIPPED
                log_entry_data["details"] = f"Step skipped due to condition: {step.condition} not met."
                logger.info(log_entry_data["details"])
            else:
                # Resolve parameters (similar to SOARPlaybookEngine)
                resolved_parameters = {}
                for k, v in step.parameters.items():
                    if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                        path = v[2:-2] # Corrected slicing for double curly braces
                        try:
                            resolved_value = playbook_run.current_context
                            for part in path.split('.'):
                                resolved_value = resolved_value[part]
                            resolved_parameters[k] = resolved_value
                        except (KeyError, TypeError):
                            logger.warning(f"Could not resolve context variable '{path}' for parameter '{k}'. Using original value.")
                            resolved_parameters[k] = v
                    else:
                        resolved_parameters[k] = v

                # Execute external tool (mocked)
                result = await engine._execute_external_tool(step.tool_name, step.action, resolved_parameters)
                
                log_entry_data["output"] = result
                if result.get("status") == "success":
                    log_entry_data["status"] = PlaybookStatus.COMPLETED
                    log_entry_data["details"] = f"Step '{step.action}' completed successfully."
                else:
                    log_entry_data["status"] = PlaybookStatus.FAILED
                    log_entry_data["details"] = f"Step '{step.action}' failed: {result.get('message', 'Unknown error')}."
            
            # Update playbook_run's current_context with step output if output_to is set
            if step.output_to and log_entry_data["status"] == PlaybookStatus.COMPLETED:
                playbook_run.current_context[step.output_to] = log_entry_data["output"]

        except Exception as e:
            logger.error(f"Error auto-executing step '{step.action}': {e}", exc_info=True)
            log_entry_data["status"] = PlaybookStatus.FAILED
            log_entry_data["details"] = f"Exception during auto-execution: {str(e)}."

        playbook_run.execution_logs.append(log_entry_data)
        
        # Determine if playbook is completed or failed
        if log_entry_data["status"] == PlaybookStatus.FAILED:
            playbook_run.status = PlaybookStatus.FAILED
            playbook_run.end_time = datetime.utcnow()
        elif step_index == len(playbook_run.playbook.steps) - 1: # Last step executed
             playbook_run.status = PlaybookStatus.COMPLETED
             playbook_run.end_time = datetime.utcnow()
        
        return playbook_run

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running AutoResponseEngine example...")
    
    # Needs a mock PlaybookRun and Playbook for example
    from .models import Playbook, PlaybookStep, PlaybookRun, RemediationAction
    
    mock_playbook = Playbook(
        name="test_auto_response",
        description="A playbook for testing automated responses.",
        trigger={"event_type": "automated_test"},
        steps=[
            PlaybookStep(action=RemediationAction.BLOCK_IP, tool_name="Firewall", parameters={"ip_address": "192.168.1.1"}),
            PlaybookStep(action=RemediationAction.CREATE_TICKET, tool_name="TicketingSystem", parameters={"title": "Automated Block", "description": "IP 192.168.1.1 blocked."}),
            PlaybookStep(action=RemediationAction.ISOLATE_HOST, tool_name="EDR", parameters={"host_id": "host-123"}, requires_approval=True) # This step should be skipped by auto-response
        ]
    )
    
    mock_playbook_run = PlaybookRun(
        run_id="run-auto-test-001",
        playbook_name=mock_playbook.name,
        triggered_by={"event": "test_event"},
        playbook=mock_playbook # Link the playbook
    )

    async def run_example():
        engine = AutoResponseEngine()
        
        # Simulate executing first step
        updated_run = await engine.execute_automated_step(mock_playbook_run, 0)
        logger.info(f"After step 0:\n{updated_run.model_dump_json(indent=2)}")

        # Simulate executing second step
        updated_run = await engine.execute_automated_step(updated_run, 1)
        logger.info(f"After step 1:\n{updated_run.model_dump_json(indent=2)}")

        # Simulate attempting to execute third step (requires approval)
        updated_run = await engine.execute_automated_step(updated_run, 2)
        logger.info(f"After step 2 (should be skipped due to approval requirement):\n{updated_run.model_dump_json(indent=2)}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("AutoResponseEngine example stopped.")
