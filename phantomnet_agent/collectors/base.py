# collectors/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from orchestrator import Orchestrator
    from phantomnet_agent.platform_compatibility.linux_adapter import LinuxAdapter
    from phantomnet_agent.platform_compatibility.windows_adapter import WindowsAdapter
    from phantomnet_agent.platform_compatibility.termux_adapter import TermuxAdapter

class Collector(ABC):
    """
    Abstract base class for all collectors.
    Collectors are responsible for gathering telemetry and sending it to the orchestrator.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Union["LinuxAdapter", "WindowsAdapter", "TermuxAdapter"], config: Dict[str, Any]):
        self.orchestrator = orchestrator
        self.adapter = adapter
        self.config = config
        self.running = False
        self.name = self.__class__.__name__ # Add a name attribute for better logging/monitoring

    @abstractmethod
    async def run(self):
        """
        The main loop for the collector. Implementations should
        periodically gather data and send events via self.orchestrator.ingest_event.
        """
        pass

    async def start(self):
        """Starts the collector's main loop."""
        self.running = True
        await self.run()

    async def stop(self):
        """Stops the collector's main loop."""
        self.running = False

