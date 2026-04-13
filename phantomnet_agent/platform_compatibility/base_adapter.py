from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseAdapter(ABC):
    """
    Abstract base class for platform-specific adapters.
    """

    @abstractmethod
    async def get_installed_software(self) -> List[Dict[str, str]]:
        """
        Gathers a list of installed software.
        """
        pass

    @abstractmethod
    async def get_netstat_info(self) -> List[Dict[str, Any]]:
        """
        Retrieves network connection information.
        """
        pass

    @abstractmethod
    async def get_process_list(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of running processes.
        """
        pass

    @abstractmethod
    async def get_process_by_pid(self, pid: int) -> Dict[str, Any]:
        """
        Retrieves information about a specific process by its PID.
        """
        pass

    @abstractmethod
    async def ping_host(self, target: str) -> Dict[str, Any]:
        """
        Pings a host and returns the results.
        """
        pass

    @abstractmethod
    async def block_address(self, address: str) -> Dict[str, Any]:
        """
        Blocks an IP address.
        """
        pass

    @abstractmethod
    async def kill_process(self, pid: int) -> Dict[str, Any]:
        """
        Kills a process by its PID.
        """
        pass

    @abstractmethod
    async def execute_command(self, cmd: str, shell: bool = False) -> Dict[str, Any]:
        """
        Executes an OS command and returns its output and status.
        """
        pass

    @abstractmethod
    async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Isolates the system (e.g., blocks all network traffic except to management interfaces).
        """
        pass
