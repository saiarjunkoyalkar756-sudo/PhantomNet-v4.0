import asyncio
import logging
from typing import Dict, Any, List, TYPE_CHECKING

from collectors.base import Collector
if TYPE_CHECKING:
    from orchestrator import Orchestrator
from schemas.events import NetworkEvent

logger = logging.getLogger(__name__)

class NetworkCollector(Collector):
    """
    Collects information about network connections and sends them as NetworkEvent.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.interval_seconds = self.config.get("interval_seconds", 10)
        self.known_connections = set() # To track established connections and detect new ones
        self.use_scapy = self.config.get("use_scapy", False) or not IS_ROOT

    async def run(self):
        logger.info(f"Starting NetworkCollector with interval: {self.interval_seconds} seconds")
        while self.running:
            await self.collect()
            await asyncio.sleep(self.interval_seconds)

    async def collect(self):
        try:
            connections = await self.adapter.get_netstat_info()
            current_connections = set()

            for conn_info in connections:
                conn_tuple = self._conn_to_tuple(conn_info)
                current_connections.add(conn_tuple)
                
                if conn_tuple not in self.known_connections:
                    event = NetworkEvent(
                        agent_id="agent-id-placeholder",
                        timestamp=asyncio.get_event_loop().time(),
                        payload=conn_info
                    )
                    await self.orchestrator.ingest_event(event.dict())

            self.known_connections = current_connections
            logger.debug(f"Collected and sent {len(current_connections)} network connection events.")
        except Exception as e:
            logger.error(f"Error in NetworkCollector: {e}")

    def _conn_to_tuple(self, conn_info: Dict[str, Any]) -> tuple:
        """Converts connection info dict to a hashable tuple for comparison."""
        return (
            conn_info.get('local_address'), conn_info.get('local_port'),
            conn_info.get('remote_address'), conn_info.get('remote_port'),
            conn_info.get('protocol')
        )
