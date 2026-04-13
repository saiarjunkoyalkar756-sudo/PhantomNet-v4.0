import asyncio
import logging
from typing import Dict, Any, Optional

from actions.base import Action
from schemas.config_schema import PhantomNetAgentConfig

class NetworkActions(Action):
    """
    Implements actions related to network management, such as pinging hosts or blocking IP addresses.
    """
    def __init__(self, logger: logging.Logger, transport: Optional[Transport] = None, config: Optional[PhantomNetAgentConfig] = None, adapter: Optional[Any] = None):
        super().__init__(logger, transport, config, adapter)
        self.logger.info("NetworkActions initialized.")

    async def ping_host(self, target: str) -> Dict[str, Any]:
        """
        Executes a ping command to a target host and returns the results.
        """
        self.logger.info(f"Pinging host: {target}")
        return await self.adapter.ping_host(target)

    async def block_address(self, address: str, port: Optional[int] = None, protocol: Optional[str] = None, direction: Optional[str] = None) -> Dict[str, Any]:
        """
        Blocks a network address using the platform-specific adapter.
        """
        self.logger.info(f"Blocking address: {address}")
        return await self.adapter.block_address(address)