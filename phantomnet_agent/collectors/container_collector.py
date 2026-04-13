# collectors/container_collector.py
import asyncio
import logging
from typing import Dict, Any

import docker
from docker.errors import DockerException

from collectors.base import Collector
from schemas.events import LogEvent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from orchestrator import Orchestrator

logger = logging.getLogger(__name__)

class ContainerCollector(Collector):
    """
    Collects logs from running Docker containers and sends them as LogEvents.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.interval_seconds = self.config.get("interval_seconds", 5)
        try:
            self.docker_client = docker.from_env()
        except DockerException as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.docker_client = None

    async def run(self):
        if not self.docker_client:
            logger.error("ContainerCollector cannot run without a Docker connection.")
            return

        logger.info(f"Starting ContainerCollector with interval: {self.interval_seconds} seconds")

        while self.running:
            await self._stream_container_logs()
            await asyncio.sleep(self.interval_seconds)

    async def _stream_container_logs(self):
        """Streams logs from all running containers."""
        if not self.docker_client:
            return

        try:
            for container in self.docker_client.containers.list():
                try:
                    # Stream new logs since the last check
                    logs = container.logs(stream=True, tail=10, since=int(asyncio.get_event_loop().time()) - self.interval_seconds)
                    for log_line in logs:
                        log_line = log_line.decode('utf-8').strip()
                        if not log_line:
                            continue

                        event = LogEvent(
                            agent_id="agent-id-placeholder",
                            timestamp=asyncio.get_event_loop().time(),
                            payload={
                                "log_source": f"container:{container.name}",
                                "severity": "INFO",  # Placeholder, needs actual parsing
                                "message": log_line,
                                "raw_log": log_line,
                                "container_id": container.id,
                                "container_name": container.name,
                                "container_image": container.image.tags[0] if container.image.tags else 'unknown',
                            }
                        )
                        await self.orchestrator.ingest_event(event.dict())
                        logger.debug(f"Collected log from {container.name}: {log_line}")

                except Exception as e:
                    logger.error(f"Error streaming logs for container {container.name}: {e}")
        except DockerException as e:
            logger.error(f"Error listing containers: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in ContainerCollector: {e}")

if __name__ == '__main__':
    async def run_example():
        logging.basicConfig(level=logging.DEBUG)

        class MockTransport(Transport):
            async def send_event(self, topic: str, payload: Dict[str, Any]) -> None:
                print(f"MockTransport: Sending event to {topic}: {payload['payload']['log_source']}")
            async def receive_commands(self, topic: str):
                yield

        mock_transport = MockTransport(endpoint="http://mock-endpoint")
        config = {"enabled": True, "interval_seconds": 5}
        collector = ContainerCollector(mock_transport, config)

        if not collector.docker_client:
            print("Could not connect to Docker. Please ensure Docker is running.")
            return

        try:
            # Create a test container
            print("Starting a test container...")
            test_container = collector.docker_client.containers.run(
                "alpine", "sh -c 'while true; do echo \"Test log from container at $(date)\"; sleep 2; done'",
                detach=True,
                remove=True,
                name="phantomnet-test-container"
            )
            await asyncio.sleep(2) # Give container time to start

            await collector.start()
            print("ContainerCollector started. Monitoring container logs...")
            await asyncio.sleep(10)

        except docker.errors.ImageNotFound:
            print("Alpine image not found. Please pull it first: docker pull alpine")
        except Exception as e:
            print(f"An error occurred during the example run: {e}")
        finally:
            print("Stopping ContainerCollector and cleaning up...")
            if 'test_container' in locals() and test_container:
                try:
                    test_container.stop()
                except docker.errors.NotFound:
                    pass # Container might already be gone
            await collector.stop()
            print("ContainerCollector stopped.")

    asyncio.run(run_example())
