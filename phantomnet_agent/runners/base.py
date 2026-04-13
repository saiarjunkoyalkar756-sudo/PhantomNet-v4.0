# runners/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class HoneypotRunner(ABC):
    """
    Abstract base class for honeypot runners.
    Defines the interface for starting, stopping, and managing honeypot processes.
    """
    def __init__(self, honeypot_id: str, honeypot_type: str, config: Dict[str, Any]):
        self.honeypot_id = honeypot_id
        self.honeypot_type = honeypot_type
        self.config = config
        self.status = "stopped"

    @abstractmethod
    async def start(self) -> None:
        """Starts the honeypot."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stops the honeypot."""
        pass

    @abstractmethod
    async def get_status(self) -> str:
        """Returns the current status of the honeypot (e.g., "running", "stopped")."""
        return self.status

    @abstractmethod
    async def get_pid(self) -> Any:
        """Returns the process ID or container ID of the honeypot."""
        pass
