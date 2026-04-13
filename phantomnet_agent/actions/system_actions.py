import asyncio
import logging
from typing import Dict, Any, Optional

from actions.base import Action
from schemas.config_schema import PhantomNetAgentConfig

class SystemActions(Action):
    """
    Implements actions related to system management, such as executing OS commands or isolating the host.
    """
    def __init__(self, logger: logging.Logger, transport: Optional[Transport] = None, config: Optional[PhantomNetAgentConfig] = None, adapter: Optional[Any] = None):
        super().__init__(logger, transport, config, adapter)
        self.logger.info("SystemActions initialized.")

    async def execute_os_command(self, cmd: str, shell: bool = False, command_id: Optional[str] = None) -> Dict[str, Any]:
        """Executes an OS command and returns its output and status."""
        self.logger.info(f"Executing OS command: '{cmd}'", extra={"command": cmd, "shell": shell, "command_id": command_id})
        result = await self.adapter.execute_command(cmd, shell)
        if result["returncode"] == 0:
            self.logger.info(f"OS command '{cmd}' completed successfully.", extra={"command": cmd, "result": result})
            return {"status": "success", "message": f"Command '{cmd}' executed successfully.", "details": result}
        else:
            self.logger.warning(f"OS command '{cmd}' failed with return code {result['returncode']}.", extra={"command": cmd, "result": result})
            return {"status": "failed", "message": f"Command '{cmd}' failed with return code {result['returncode']}.", "details": result}

    async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Isolates the system (e.g., blocks all network traffic except to management interfaces)."""
        self.logger.info(f"Initiating system isolation for reason: {reason}", extra={"action": {"reason": reason, "duration_seconds": duration_seconds}})
        result = await self.adapter.isolate_system(reason, duration_seconds)
        if result["status"] == "success":
            self.logger.info(f"System isolation completed successfully. Reason: {reason}.", extra={"action": result})
            return result
        else:
            self.logger.warning(f"System isolation failed. Reason: {reason}.", extra={"action": result})
            return result