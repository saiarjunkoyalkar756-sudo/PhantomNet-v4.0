# collectors/log_collector.py
import asyncio
import logging
import re
from typing import Dict, Any, List, Optional

from collectors.base import Collector
from schemas.events import LogEvent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class LogCollector(Collector):
    """
    Collects logs by tailing specified log files and sends each new line as a LogEvent.
    Supports configurable regex patterns for parsing structured log data.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.files: List[str] = config.get("files", [])
        self.interval_seconds = self.config.get("interval_seconds", 5)
        self.log_patterns: List[Dict[str, Any]] = config.get("log_patterns", [])
        self.compiled_patterns: List[Dict[str, Any]] = []
        self.last_read_positions: Dict[str, int] = {} # {file_path: last_byte_position}
        
        self._compile_patterns()

    def _compile_patterns(self):
        """Compiles regex patterns provided in the configuration."""
        for pattern_def in self.log_patterns:
            try:
                pattern = re.compile(pattern_def["regex"])
                self.compiled_patterns.append({"pattern": pattern, "fields": pattern_def.get("fields", {})})
            except re.error as e:
                logger.error(f"Invalid regex pattern in LogCollector config: '{pattern_def.get('regex')}' - {e}")

    async def run(self):
        logger.info(f"Starting LogCollector for files: {self.files} with interval: {self.interval_seconds} seconds")
        if not self.files:
            logger.warning("No log files configured for LogCollector. It will not run.")
            return

        # Initialize last read positions
        for f_path in self.files:
            try:
                with open(f_path, 'rb') as f:
                    self.last_read_positions[f_path] = f.seek(0, 2) # Seek to end of file
            except FileNotFoundError:
                logger.warning(f"Log file not found on startup: {f_path}")
                self.last_read_positions[f_path] = 0
            except Exception as e:
                logger.error(f"Error initializing LogCollector for {f_path}: {e}")
                self.last_read_positions[f_path] = 0

        while self.running:
            for log_file in self.files:
                await self._tail_log_file(log_file)
            await asyncio.sleep(self.interval_seconds)

    async def _tail_log_file(self, log_file_path: str):
        """Reads new lines from a log file since the last read position and attempts to parse them."""
        try:
            current_position = self.last_read_positions.get(log_file_path, 0)
            with open(log_file_path, 'r', errors='ignore') as f: # Use errors='ignore' for robust log reading
                f.seek(current_position)
                for line in f:
                    parsed_payload = {}
                    log_severity = "INFO" # Default severity
                    log_message = line.strip()
                    event_type = "generic_log"

                    # Attempt to parse using configured regex patterns
                    matched = False
                    for compiled_pattern_def in self.compiled_patterns:
                        match = compiled_pattern_def["pattern"].match(line)
                        if match:
                            parsed_payload = match.groupdict()
                            # Map extracted fields to LogEvent fields (e.g., if regex named group is 'level', map to 'severity')
                            log_severity = parsed_payload.get("level", log_severity).upper()
                            log_message = parsed_payload.get("message", log_message)
                            event_type = parsed_payload.get("type", event_type)
                            matched = True
                            break # Use the first matching pattern

                    event = LogEvent(
                        agent_id=self.agent_id, # agent_id set during initialization in main.py
                        timestamp=asyncio.get_event_loop().time(),
                        log_source=log_file_path,
                        severity=log_severity,
                        message=log_message,
                        raw_log=line.strip(),
                        # Include all parsed fields in metadata for richer context
                        payload={"parsed_data": parsed_payload, "event_type": event_type} 
                    )
                    await self.orchestrator.ingest_event(event.dict())
                    logger.debug(f"Collected and parsed log from {log_file_path}: {event.dict()}")
                self.last_read_positions[log_file_path] = f.tell()
        except FileNotFoundError:
            logger.warning(f"Log file not found during tailing: {log_file_path}")
        except Exception as e:
            logger.error(f"Error tailing log file {log_file_path}: {e}")

if __name__ == '__main__':
    async def run_example():
        logging.basicConfig(level=logging.DEBUG)
        
        class MockTransport(Transport):
            def __init__(self, endpoint: str, client_cert=None, client_key=None, verify_ca=True):
                super().__init__(endpoint)
                self.client_cert = client_cert
                self.client_key = client_key
                self.verify_ca = verify_ca
            async def send_event(self, topic: str, payload: Dict[str, Any]) -> None:
                print(f"MockTransport: Sending event to {topic}: {payload['event_type']}")
                print(f"Payload: {json.dumps(payload, indent=2)}")
            async def receive_commands(self, topic: str):
                yield
            async def connect(self):
                print("MockTransport: Connected.")
            async def disconnect(self):
                print("MockTransport: Disconnected.")

        mock_transport = MockTransport(endpoint="http://mock-endpoint")

        # Create a dummy log file for testing
        test_log_file = "./test_app.log"
        with open(test_log_file, "w") as f:
            f.write("2023-01-01 10:00:00 INFO App started.\n")
            f.write("2023-01-01 10:00:01 DEBUG User 'alice' logged in from 192.168.1.100.\n")

        # Example configuration with regex patterns
        config = {
            "enabled": True, 
            "interval_seconds": 1, 
            "files": [test_log_file],
            "log_patterns": [
                {
                    "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.*)$",
                    "fields": {"timestamp": "timestamp", "level": "severity", "message": "message", "type": "generic_log"}
                },
                {
                    "regex": r".*User '(?P<username>\w+)' logged in from (?P<ip_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*",
                    "fields": {"username": "user", "ip_address": "src_ip", "type": "auth_login"}
                }
            ]
        }
        collector = LogCollector(mock_transport, config)
        collector.agent_id = "test-agent-1" # Mock agent_id

        try:
            await collector.start()
            print("LogCollector started. Monitor test_app.log...")
            await asyncio.sleep(2) # Initial scan

            print("\nAdding new entries to test_app.log...")
            with open(test_log_file, "a") as f:
                f.write("2023-01-01 10:00:02 DEBUG User 'bob' accessed confidential file.\n")
                f.write("2023-01-01 10:00:05 ERROR Critical process failed on HostX.\n")
            await asyncio.sleep(2)

            print("\nAdding more entries to test_app.log (matching login pattern)...")
            with open(test_log_file, "a") as f:
                f.write("2023-01-01 10:00:10 INFO User 'charlie' logged in from 10.0.0.5.\n")
            await asyncio.sleep(2)

        finally:
            await collector.stop()
            Path(test_log_file).unlink() # Clean up
            print("LogCollector stopped and test log cleaned up.")

    asyncio.run(run_example())

