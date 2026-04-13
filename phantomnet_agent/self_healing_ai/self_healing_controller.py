# phantomnet_agent/self_healing_ai/self_healing_controller.py

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from utils.logger import get_logger
from shared.platform_utils import SAFE_MODE, IS_ROOT, get_platform_details
from .diagnostics_engine import DiagnosticsEngine
from .error_classifier import ErrorClassifier
from .auto_remediator import AutoRemediator
from .patch_manager import PatchManager
from .system_recovery import SystemRecovery
from phantomnet_agent.core.state import get_agent_state # To access agent's overall state and components

logger = get_logger(__name__)

class SelfHealingController:
    """
    Master controller sub-agent that monitors PhantomNet components,
    automatically triggers remediation, logs decisions, and reports health.
    """
    def __init__(self, check_interval_seconds: int = 10, agent_dir: str = "."):
        self.check_interval_seconds = check_interval_seconds
        self.agent_dir = agent_dir
        self.safe_mode = SAFE_MODE
        
        self.diagnostics_engine = DiagnosticsEngine(log_dir=os.path.join(agent_dir, "logs"))
        self.error_classifier = ErrorClassifier()
        self.auto_remediator = AutoRemediator(agent_dir=agent_dir, venv_path=os.path.join(agent_dir, ".venv_phantomnet"))
        self.patch_manager = PatchManager(patch_storage_dir=os.path.join(agent_dir, "patches"))
        self.system_recovery = SystemRecovery(agent_dir=agent_dir, venv_path=os.path.join(agent_dir, ".venv_phantomnet"), cert_dir=os.path.join(agent_dir, "certs"))
        
        self.stop_event = asyncio.Event()
        self._controller_task: Optional[asyncio.Task] = None
        
        logger.info(f"SelfHealingController initialized. Check interval: {check_interval_seconds}s, SAFE_MODE: {self.safe_mode}")

    async def _monitor_python_errors(self):
        """Monitors Python exceptions caught by the diagnostics engine."""
        recent_errors = self.diagnostics_engine.get_recent_errors()
        for error_details in recent_errors:
            if not error_details.get("processed_by_self_healing"): # Avoid re-processing
                logger.info(f"Detected Python error: {error_details.get('fingerprint')}")
                classified_error = self.error_classifier.classify_error(error_details)
                
                # Update agent state with error
                agent_state = get_agent_state()
                agent_state.update_component_health(
                    "self_healing_controller", 
                    "degraded", 
                    {"last_error": classified_error}
                )

                if classified_error.get("classified_severity") in ["SEV1", "SEV2", "SEV3"]:
                    logger.warning(f"Classified error: {classified_error.get('classified_issue_type')} (Severity: {classified_error.get('classified_severity')}). Attempting remediation...")
                    
                    if not self.safe_mode:
                        success, remediation_log = await self.auto_remediator.remediate(classified_error)
                        if success:
                            logger.info(f"Remediation successful for {classified_error.get('fingerprint')}. Log: {remediation_log}")
                            self.error_classifier.send_error_signature_to_backend(classified_error) # Send solved error
                        else:
                            logger.error(f"Remediation failed for {classified_error.get('fingerprint')}. Log: {remediation_log}")
                            # Trigger system recovery if remediation repeatedly fails for critical errors
                            if classified_error.get("classified_severity") == "SEV1":
                                logger.critical("SEV1 remediation failed. Initiating system recovery...")
                                await self.trigger_system_recovery(["rebuild_venv", "repair_config", "restore_heartbeat"])
                    else:
                        logger.warning("SAFE_MODE is ON. Auto-remediation is disabled.")
                
                error_details["processed_by_self_healing"] = True # Mark as processed

    async def _monitor_component_health(self):
        """Monitors the health of other PhantomNet components."""
        agent_state = get_agent_state()
        
        for comp_name, comp_health in agent_state.component_health.items():
            if comp_health.status == "error" or comp_health.status == "degraded":
                logger.warning(f"Component '{comp_name}' is in {comp_health.status} state. Details: {comp_health.details}")
                # Trigger specific diagnostics or remediation based on component and error
                
                # Example: If a collector is failed
                if "collector" in comp_name.lower():
                    # For now, if a collector is failed, try a venv rebuild as a general fix
                    logger.info(f"Collector {comp_name} failed. Suggesting venv rebuild.")
                    await self.trigger_system_recovery(["rebuild_venv"])


    async def trigger_system_recovery(self, recovery_plan: List[str]):
        """Triggers a last-resort system recovery sequence."""
        success, log = await self.system_recovery.recover(recovery_plan)
        if success:
            logger.critical(f"System recovery successful. Log: {log}")
        else:
            logger.critical(f"System recovery failed. Log: {log}")

    async def run(self):
        """Main loop for the self-healing controller."""
        logger.info("SelfHealingController starting main loop...")
        
        # Start diagnostics engine as a background task
        asyncio.create_task(self.diagnostics_engine.run_diagnostics())

        while not self.stop_event.is_set():
            await self._monitor_python_errors()
            await self._monitor_component_health()
            
            # Conceptual: Check for patch availability from backend
            # patch_info = await self.backend_client.get_latest_patch(get_platform_details())
            # if patch_info:
            #     await self.patch_manager.process_patch(patch_info, self.agent_dir, os.path.join(self.agent_dir, "backups"))

            await asyncio.sleep(self.check_interval_seconds)

    async def start(self):
        """Starts the self-healing controller background task."""
        logger.info("SelfHealingController starting.")
        self._controller_task = asyncio.create_task(self.run())

    async def stop(self):
        """Stops the self-healing controller background task."""
        logger.info("SelfHealingController stopping.")
        self.stop_event.set()
        if self._controller_task:
            self._controller_task.cancel()
            await asyncio.gather(self._controller_task, return_exceptions=True)
        logger.info("SelfHealingController stopped.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running SelfHealingController example...")
    
    # Mock agent state for testing
    class MockAgentState:
        def __init__(self):
            self.component_health = {}
            self.os = get_platform_details()["os_type"]
            self.capabilities = get_platform_details()
        
        def update_component_health(self, name: str, status: str, details: Optional[Dict[str, Any]] = None):
            self.component_health[name] = type('obj', (object,), {'status': status, 'details': details})()
            logger.info(f"MockAgentState: Updated component '{name}' to {status}")

    # Mock get_agent_state
    _mock_agent_state = MockAgentState()
    with patch('core.state.get_agent_state', return_value=_mock_agent_state):
        controller = SelfHealingController()

        async def run_example():
            await controller.start()
            
            # Simulate an unhandled exception
            try:
                raise ImportError("mock_missing_module_for_test")
            except ImportError:
                exc_type, exc_value, tb = sys.exc_info()
                controller.diagnostics_engine._handle_unhandled_exception(exc_type, exc_value, tb)
            
            # Simulate a component going into error state
            _mock_agent_state.update_component_health("network_collector", "error", {"message": "Network dropped packets"})

            await asyncio.sleep(5) # Give controller time to process
            await controller.stop()

        try:
            from unittest.mock import patch, MagicMock # Make sure patch is imported for the example
            asyncio.run(run_example())
        except KeyboardInterrupt:
            logger.info("SelfHealingController example stopped.")