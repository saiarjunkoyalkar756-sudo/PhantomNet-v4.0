# collectors/process_collector.py
import asyncio
import logging
from typing import Dict, Any, TYPE_CHECKING

from collectors.base import Collector
if TYPE_CHECKING:
    from orchestrator import Orchestrator
from schemas.events import ProcessEvent

logger = logging.getLogger(__name__)

class ProcessCollector(Collector):
    """
    Collects information about running processes and sends them as ProcessEvent.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.interval_seconds = self.config.get("interval_seconds", 5)

    async def run(self):
        """
        Main loop for the Process Collector.
        Continuously gathers process information and sends it as events.
        """
        logger.info(f"Starting ProcessCollector with interval: {self.interval_seconds} seconds")
        while self.running:
            try:
                processes = await self.adapter.get_process_list()
                for proc_info in processes:
                    event = ProcessEvent(
                        agent_id="agent-id-placeholder", # Will be filled by main agent
                        timestamp=asyncio.get_event_loop().time(),
                        payload=proc_info
                    )
                    await self.orchestrator.ingest_event(event.dict())
                logger.debug(f"Collected and sent {len(processes)} process events.")
            except Exception as e:
                logger.error(f"Error in ProcessCollector: {e}")
            await asyncio.sleep(self.interval_seconds)

if __name__ == '__main__':
    # Example usage (for testing purposes)
    async def run_example():
        logging.basicConfig(level=logging.DEBUG)
        
        # Mock Transport for testing
        class MockTransport(Transport):
            async def send_event(self, topic: str, payload: Dict[str, Any]) -> None:
                print(f"MockTransport: Sending event to {topic}: {payload['event_type']}")
                # print(ProcessEvent(**payload).json(indent=2)) # Validate and print
            async def receive_commands(self, topic: str):
                yield

        mock_transport = MockTransport(endpoint="http://mock-endpoint") # endpoint is not used by MockTransport
        config = {"enabled": True, "interval_seconds": 2}
        collector = ProcessCollector(mock_transport, config)

        try:
            # Run for a short period
            await collector.start()
            await asyncio.sleep(6) # Collect for 6 seconds
        finally:
            await collector.stop()
            print("ProcessCollector stopped.")

    # Make sure to install psutil
    # pip install psutil
    try:
        asyncio.run(run_example())
    except ImportError:
        print("\nERROR: 'psutil' is not installed. Please install it: pip install psutil")

