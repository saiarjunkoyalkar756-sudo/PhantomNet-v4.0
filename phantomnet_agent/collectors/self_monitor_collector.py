# collectors/self_monitor_collector.py
import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import os

from collectors.base import Collector
if TYPE_CHECKING:
    from orchestrator import Orchestrator
from schemas.events import LogEvent # Using LogEvent for simplicity

logger = logging.getLogger(__name__)

class SelfMonitorCollector(Collector):
    """
    Collects information about the agent's own process and monitors critical files for tampering.
    Sends alerts (LogEvents) if anomalies or tampering are detected.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.interval_seconds = self.config.get("interval_seconds", 10)
        self.critical_files: List[str] = self.config.get("critical_files", [])
        self.agent_pid = os.getpid() # The agent's own process ID
        self.initial_checksums: Dict[str, str] = {}
        
        self._initialize_file_checksums()

    def _initialize_file_checksums(self):
        """Calculates initial checksums for critical files."""
        for file_path_str in self.critical_files:
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                try:
                    self.initial_checksums[file_path_str] = self._calculate_file_checksum(file_path)
                    logger.debug(f"Initial checksum for {file_path_str}: {self.initial_checksums[file_path_str]}")
                except Exception as e:
                    logger.warning(f"Could not calculate initial checksum for {file_path_str}: {e}")
            else:
                logger.warning(f"Critical file not found or is not a file: {file_path_str}")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculates SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(4096) # Read in 4KB chunks
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    async def run(self):
        """
        Main loop for the Self-Monitor Collector.
        Periodically checks agent's process integrity and file integrity.
        """
        logger.info(f"Starting SelfMonitorCollector with interval: {self.interval_seconds} seconds")
        while self.running:
            await self._check_process_integrity()
            await self._check_file_integrity()
            await asyncio.sleep(self.interval_seconds)

    async def _check_process_integrity(self):
        """Checks for unexpected changes in the agent's own process."""
        try:
            # Basic checks: PID, status, memory usage (can expand)
            proc_info = await self.adapter.get_process_by_pid(self.agent_pid)
            if not proc_info:
                await self._send_alert("CRITICAL", "Agent process is not running!", {"pid": self.agent_pid, "status": "terminated"})
                self.stop() # Attempt to stop the collector if agent process is gone
                return

        except Exception as e:
            logger.error(f"Error checking process integrity: {e}")
            await self._send_alert("ERROR", f"Error during process integrity check: {e}")

    async def _check_file_integrity(self):
        """Checks critical agent files for unauthorized modifications."""
        for file_path_str, initial_checksum in self.initial_checksums.items():
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                try:
                    current_checksum = self._calculate_file_checksum(file_path)
                    if current_checksum != initial_checksum:
                        await self._send_alert("CRITICAL", f"Critical file '{file_path_str}' has been tampered with!", {
                            "file": file_path_str,
                            "initial_checksum": initial_checksum,
                            "current_checksum": current_checksum
                        })
                except Exception as e:
                    logger.error(f"Error checking checksum for {file_path_str}: {e}")
                    await self._send_alert("ERROR", f"Error during file integrity check for '{file_path_str}': {e}")
            else:
                await self._send_alert("CRITICAL", f"Critical file '{file_path_str}' is missing!", {"file": file_path_str})

    async def _send_alert(self, severity: str, message: str, details: Dict[str, Any]):
        """Sends a LogEvent as an alert for self-monitoring issues."""
        event = LogEvent(
            agent_id=self.agent_id, # agent_id set during initialization in main.py
            timestamp=asyncio.get_event_loop().time(),
            log_source="self_monitor_collector",
            severity=severity,
            message=message,
            payload={"details": details, "event_type": "agent_self_monitor_alert"}
        )
        await self.orchestrator.ingest_event(event.dict())
        logger.warning(f"Self-monitoring alert sent: {message}")


if __name__ == '__main__':
    async def run_example():
        logging.basicConfig(level=logging.DEBUG)
        
        # Mock Orchestrator for testing
        class MockOrchestrator:
            async def ingest_event(self, event: Dict[str, Any]) -> None:
                print(f"MockOrchestrator: Ingesting event: {event['payload']['event_type']} - {event['severity']}")
                print(f"Payload: {json.dumps(event, indent=2)}")

        mock_orchestrator = MockOrchestrator()

        # Mock Adapter for testing
        class MockAdapter:
            async def get_process_by_pid(self, pid: int) -> Dict[str, Any]:
                if pid == os.getpid():
                    return {"pid": pid, "name": "python", "status": "running"}
                return {}
            # Add other methods if needed by the collector's tests
            async def get_installed_software(self) -> List[Dict[str, str]]: return []
            async def get_netstat_info(self) -> List[Dict[str, Any]]: return []
            async def get_process_list(self) -> List[Dict[str, Any]]: return []
            async def ping_host(self, target: str) -> Dict[str, Any]: return {}
            async def block_address(self, address: str) -> Dict[str, Any]: return {}
            async def execute_command(self, cmd: str, shell: bool = False) -> Dict[str, Any]: return {}
            async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]: return {}
        mock_adapter = MockAdapter()
        
        # Create dummy critical files
        critical_file_1 = Path("./agent_config.yml")
        critical_file_2 = Path("./agent_binary")
        critical_file_1.write_text("config: value")
        critical_file_2.write_text("binary_content")

        config = {
            "enabled": True, 
            "interval_seconds": 2,
            "critical_files": [str(critical_file_1), str(critical_file_2)]
        }
        collector = SelfMonitorCollector(mock_orchestrator, mock_adapter, config)
        collector.agent_id = "test-agent-1" # Mock agent_id

        try:
            await collector.start()
            print("SelfMonitorCollector started. Waiting for checks...")
            await asyncio.sleep(3) # Initial checks

            print("\nTampering with agent_config.yml...")
            critical_file_1.write_text("config: new_value")
            await asyncio.sleep(3) # Should detect tampering

            print("\nDeleting agent_binary...")
            critical_file_2.unlink()
            await asyncio.sleep(3) # Should detect missing file
            
        finally:
            await collector.stop()
            critical_file_1.unlink(missing_ok=True)
            critical_file_2.unlink(missing_ok=True)
            print("SelfMonitorCollector stopped and test files cleaned up.")

    try:
        asyncio.run(run_example())
    except Exception as e:
        print(f"\nAn error occurred during SelfMonitorCollector example execution: {e}")
