import asyncio
import logging
import platform
import subprocess
from typing import Dict, Any, List

from .base import Collector

logger = logging.getLogger("phantomnet_agent.collectors.software")

class SoftwareCollector(Collector):
    """
    A collector for gathering information about installed software on the host.
    """

    def __init__(self, orchestrator, adapter, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.interval = self.config.get("interval", 3600)  # Default to 1 hour

    async def run(self):
        logger.info("Starting software collector...")
        while self.running:
            await self.collect_and_send_software_data()
            await asyncio.sleep(self.interval)

    async def collect_and_send_software_data(self):
        """Collects software data and sends it to the orchestrator."""
        software_list = await self.get_installed_software()
        if software_list:
            event_data = {
                "event_type": "SOFTWARE_INVENTORY",
                "software": software_list,
                "hostname": platform.node(),
            }
            # Ingest data into the orchestrator
            await self.orchestrator.ingest_event(event_data)
            logger.info(f"Collected and sent inventory of {len(software_list)} installed software packages.")
        else:
            logger.warning("Could not retrieve installed software list.")

    async def get_installed_software(self) -> List[Dict[str, str]]:
        """
        Gathers a list of installed software using the platform adapter.
        """
        return await self.adapter.get_installed_software()
