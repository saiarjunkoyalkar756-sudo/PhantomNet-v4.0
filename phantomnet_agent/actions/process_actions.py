import asyncio
import logging
from typing import Dict, Any, Optional, List

from actions.base import Action
from schemas.config_schema import PhantomNetAgentConfig

class ProcessActions(Action):
    """
    Implements actions related to process management, such as listing or killing processes.
    """
    def __init__(self, logger: logging.Logger, transport: Optional[Transport] = None, config: Optional[PhantomNetAgentConfig] = None, adapter: Optional[Any] = None):
        super().__init__(logger, transport, config, adapter)
        self.logger.info("ProcessActions initialized.")

    async def list_processes(self) -> Dict[str, Any]:
        """
        Lists all running processes with relevant details.
        """
        self.logger.info("Listing all running processes.")
        processes_data = await self.adapter.get_process_list()
        return {"status": "success", "message": "Processes listed.", "details": {"processes": processes_data}}

    async def kill_process(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Kills a process by its PID.
        """
        self.logger.info(f"Attempting to kill process with PID: {pid} (force={force}).")
        return await self.adapter.kill_process(pid)