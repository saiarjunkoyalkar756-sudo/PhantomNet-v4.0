from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator

class Transport(ABC):
    @abstractmethod
    async def connect(self):
        """Establish connection to the message bus."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection to the message bus."""
        pass

    @abstractmethod
    async def send_event(self, event_data: Dict[str, Any]):
        """Send an event to the message bus or backend."""
        pass

    @abstractmethod
    async def receive_commands(self, commands_topic: str) -> AsyncGenerator[Any, None]:
        """Asynchronously receive commands from the message bus."""
        # This should yield command objects
        pass
