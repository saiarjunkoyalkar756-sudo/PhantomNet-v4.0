# collectors/dns_collector.py
import asyncio
import logging
import re
from typing import Dict, Any, List

from collectors.base import Collector
from schemas.events import DnsEvent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class DnsCollector(Collector):
    """
    Collects DNS queries by parsing specified log files.
    This is a simplified implementation that assumes common log formats.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.log_files: List[str] = config.get("log_files", [])
        self.interval_seconds = self.config.get("interval_seconds", 30)
        self.last_read_positions: Dict[str, int] = {f: 0 for f in self.log_files}
        # Regex to find DNS queries, this is highly dependent on log format
        # Example for systemd-resolved: "query (A|AAAA) example.com"
        # Example for dnsmasq: "query[A] example.com from 192.168.1.1"
        self.dns_query_regex = re.compile(
            r"(?:query|request)\S*\s*(?:\[(A|AAAA|PTR|CNAME)\])?\s*(\S+)(?:\s+from\s+(\S+))?"
        )

    async def run(self):
        logger.info(f"Starting DnsCollector for log files: {self.log_files} with interval: {self.interval_seconds} seconds")
        if not self.log_files:
            logger.warning("No log files configured for DnsCollector. It will not run.")
            return

        while self.running:
            for log_file in self.log_files:
                await self._process_log_file(log_file)
            await asyncio.sleep(self.interval_seconds)

    async def _process_log_file(self, log_file_path: str):
        """Reads new lines from a log file and processes them for DNS queries."""
        try:
            with open(log_file_path, 'r') as f:
                f.seek(self.last_read_positions.get(log_file_path, 0))
                for line in f:
                    match = self.dns_query_regex.search(line)
                    if match:
                        query_type = match.group(1) or "UNKNOWN"
                        query_name = match.group(2)
                        resolver = match.group(3) if match.group(3) else "UNKNOWN_RESOLVER" # Placeholder
                        
                        event = DnsEvent(
                            agent_id="agent-id-placeholder",
                            timestamp=asyncio.get_event_loop().time(),
                            payload={
                                "query_name": query_name,
                                "query_type": query_type,
                                "answer": None, # This might require further lookup or more advanced parsing
                                "resolver": resolver,
                                "process_pid": None # Cannot easily get PID from log parsing alone
                            }
                        )
                        await self.orchestrator.ingest_event(event.dict())
                        logger.debug(f"Detected DNS query: {query_name} ({query_type})")
                self.last_read_positions[log_file_path] = f.tell()
        except FileNotFoundError:
            logger.warning(f"DNS log file not found: {log_file_path}")
        except Exception as e:
            logger.error(f"Error processing DNS log file {log_file_path}: {e}")

if __name__ == '__main__':
    async def run_example():
        logging.basicConfig(level=logging.DEBUG)
        
        class MockTransport(Transport):
            async def send_event(self, topic: str, payload: Dict[str, Any]) -> None:
                print(f"MockTransport: Sending event to {topic}: {payload['event_type']}")
                # print(DnsEvent(**payload).json(indent=2))
            async def receive_commands(self, topic: str):
                yield

        mock_transport = MockTransport(endpoint="http://mock-endpoint")

        # Create a dummy log file for testing
        test_log_file = "./test_dns.log"
        with open(test_log_file, "w") as f:
            f.write("Dec  4 10:00:01 host systemd-resolved[123]: query example.com\n")
            f.write("Dec  4 10:00:02 host dnsmasq[456]: query[A] google.com from 192.168.1.100\n")

        config = {"enabled": True, "interval_seconds": 2, "log_files": [test_log_file]}
        collector = DnsCollector(mock_transport, config)

        try:
            await collector.start()
            print("DnsCollector started. Monitor test_dns.log...")
            await asyncio.sleep(3) # Initial scan

            print("\nAdding new entries to test_dns.log...")
            with open(test_log_file, "a") as f:
                f.write("Dec  4 10:00:05 host systemd-resolved[123]: query www.anothersite.org\n")
                f.write("Dec  4 10:00:06 host dnsmasq[456]: query[AAAA] ipv6.google.com from 192.168.1.101\n")
            await asyncio.sleep(3)
        finally:
            await collector.stop()
            Path(test_log_file).unlink() # Clean up
            print("DnsCollector stopped and test log cleaned up.")

    asyncio.run(run_example())
