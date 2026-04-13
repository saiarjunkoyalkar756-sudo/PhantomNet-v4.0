import asyncio
import logging
import json
import httpx
from typing import Dict, Any, List, Optional
from core.state import get_agent_state # To get agent_id and config

logger = logging.getLogger("phantomnet_agent.log_forwarder")

class LogForwarder(logging.Handler):
    """
    A custom logging handler that captures log records, queues them, and
    asynchronously forwards them in batches via HTTP POST to a backend API.
    """
    def __init__(self, backend_url: str, agent_id: str, level=logging.INFO):
        super().__init__(level=level)
        self.backend_url = backend_url
        self.agent_id = agent_id
        self.log_queue = asyncio.Queue()
        self.stop_event = asyncio.Event()
        self._forwarding_task: Optional[asyncio.Task] = None
        self.batch_size = 10  # Number of logs to send in one batch
        self.forward_interval = 5  # Seconds to wait before sending a batch

        # Use the same formatter as utils.logger to ensure structured JSON output
        from utils.logger import JsonFormatter
        self.setFormatter(JsonFormatter(agent_id=agent_id, host="localhost")) # Host will be dynamically set by main logger

        logger.info(f"LogForwarder initialized for backend: {self.backend_url}")

    def emit(self, record: logging.LogRecord):
        """
        Captures a log record, formats it to JSON, and puts it into the queue.
        This method is called by the logging system.
        """
        try:
            formatted_log = self.format(record)
            self.log_queue.put_nowait(formatted_log)
        except Exception as e:
            logger.error(f"Error while emitting log record to queue: {e}", exc_info=True)

    async def _forward_logs_to_backend(self):
        """
        Periodically sends batches of logs from the queue to the backend via HTTP POST.
        """
        while not self.stop_event.is_set():
            batch: List[str] = []
            try:
                # Collect logs from queue, up to batch_size, without blocking for too long
                for _ in range(self.batch_size):
                    try:
                        log_entry = await asyncio.wait_for(self.log_queue.get(), timeout=0.1)
                        batch.append(log_entry)
                    except asyncio.TimeoutError:
                        break # No more logs in queue, send what we have

                if batch:
                    ingest_url = f"{self.backend_url}/api/v1/logs/ingest"
                    headers = {"Content-Type": "application/json"}
                    payload = {"agent_id": self.agent_id, "logs": batch}

                    async with httpx.AsyncClient() as client:
                        response = await client.post(ingest_url, json=payload, headers=headers, timeout=5.0)
                        response.raise_for_status() # Raise an exception for bad status codes
                    
                    logger.debug(f"Successfully forwarded {len(batch)} logs to backend.")
                    for _ in batch: # Mark items as done in queue
                        self.log_queue.task_done()

            except httpx.RequestError as e:
                logger.warning(f"Failed to forward logs to backend ({self.backend_url}): Network error - {e}")
                # Re-add logs to queue for retry, or implement dead-letter queue
                for log_entry in batch:
                    self.log_queue.put_nowait(log_entry)
            except httpx.HTTPStatusError as e:
                logger.warning(f"Failed to forward logs to backend ({self.backend_url}): HTTP error {e.response.status_code} - {e.response.text}")
                for log_entry in batch:
                    self.log_queue.put_nowait(log_entry)
            except Exception as e:
                logger.error(f"Unexpected error in log forwarding task: {e}", exc_info=True)
            
            # Wait for the next forwarding interval
            await asyncio.sleep(self.forward_interval)

    async def start(self):
        """Starts the log forwarding background task."""
        logger.info("LogForwarder starting background task.")
        self._forwarding_task = asyncio.create_task(self._forward_logs_to_backend())

    async def stop(self):
        """Stops the log forwarding background task."""
        logger.info("LogForwarder stopping background task. Waiting for queue to clear...")
        self.stop_event.set()
        if self._forwarding_task:
            self._forwarding_task.cancel()
            await asyncio.gather(self._forwarding_task, return_exceptions=True)
        await self.log_queue.join() # Wait until all logs in queue are processed/retried
        logger.info("LogForwarder background task stopped.")


# The old log_event function is no longer needed here, as it was only for attacks.log.
# attacks.log will be directly managed by utils.logger.log_event as a separate stream.
# Removed old code to tailor this file to the new log forwarding requirements.