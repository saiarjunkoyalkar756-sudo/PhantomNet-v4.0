# phantomnet_agent/collectors/ebpf_simulator.py

import asyncio
import logging
from typing import Dict, Any, Optional

from collectors.base import Collector
from bus.base import Transport # Assuming a Transport is available for event sending
from utils.logger import get_logger
from shared.platform_utils import IS_LINUX, HAS_EBPF

logger = get_logger(__name__)

class EbpfSimulator(Collector):
    """
    A simulated eBPF collector that produces synthetic eBPF-like events
    for development, testing, or environments where real eBPF is not available.
    """
    def __init__(self, orchestrator: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, config)
        self.name = "ebpf_simulator"
        self.logger = get_logger(f"phantomnet_agent.{self.name}")
        self.interval_seconds = config.get("interval_seconds", 5) # How often to generate events

    async def _generate_simulated_event(self):
        """Generates a single simulated eBPF event."""
        event_type = "PROCESS_EXEC_EBPF_SIMULATED"
        pid = asyncio.current_task().get_name() # Use task name for a pseudo-PID
        
        simulated_event = {
            "pid": pid,
            "tgid": pid,
            "comm": "simulated_process",
            "filename": "/usr/bin/simulated_binary",
            "retval": 0,
            "message": "Simulated eBPF process execution event."
        }

        self.logger.info(
            f"Simulated eBPF event: {simulated_event['comm']} (PID: {simulated_event['pid']})",
            extra={"event_type": event_type, **simulated_event},
        )
        
        # In a real scenario, this would send an event via orchestrator
        # await self.orchestrator.ingest_event(simulated_event)

    async def run(self):
        """
        Main loop for the simulated eBPF collector.
        """
        if HAS_EBPF and IS_LINUX:
            self.logger.info("Real eBPF detected. EbpfSimulator will not run. Consider disabling this collector.")
            return

        self.logger.info(f"EbpfSimulator starting. Generating simulated events every {self.interval_seconds} seconds.")

        while self.running:
            await self._generate_simulated_event()
            await asyncio.sleep(self.interval_seconds)

    async def stop(self):
        """
        Stops the simulated eBPF collector.
        """
        self.running = False
        self.logger.info("EbpfSimulator stopped.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running EbpfSimulator example...")
    
    # Mock Orchestrator and config for example
    class MockOrchestrator:
        async def ingest_event(self, event: Dict[str, Any]):
            logger.info(f"MockOrchestrator: Ingested event {event.get('event_type')}")

    mock_orchestrator = MockOrchestrator()
    config = {"interval_seconds": 1}

    async def run_example():
        simulator = EbpfSimulator(mock_orchestrator, config)
        await simulator.start()
        await asyncio.sleep(5) # Run for 5 seconds
        await simulator.stop()

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("EbpfSimulator example stopped.")
