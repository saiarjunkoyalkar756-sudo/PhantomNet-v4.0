import asyncio
import logging
import psutil
from typing import Dict, Any, Optional
from datetime import datetime
from core.state import get_agent_state # To access agent_state
from utils.logger import get_logger # Use the structured logger factory

class TelemetryCollector:
    """
    Collects internal agent telemetry (CPU, memory, collector status, etc.)
    and emits it as structured log events.
    """
    def __init__(self, interval_seconds: int = 10):
        self.interval_seconds = interval_seconds
        self.logger = get_logger("phantomnet_agent.telemetry_collector")
        self.stop_event = asyncio.Event()
        self._collect_task: Optional[asyncio.Task] = None
        self.logger.info(f"TelemetryCollector initialized with interval: {self.interval_seconds}s.")

    async def _collect_and_emit_telemetry(self):
        """
        Periodically collects system and agent-internal telemetry and emits
        structured log events.
        """
        while not self.stop_event.is_set():
            telemetry_data: Dict[str, Any] = {
                "event_type": "AGENT_TELEMETRY",
                "cpu_percent": None, # Default to None
                "memory_percent": None, # Default to None
                "agent_uptime_seconds": 0,
                "component_health_snapshot": "N/A"
            }
            try:
                agent_state = get_agent_state()
                # Ensure datetime is imported for started_at calculation
                from datetime import datetime

                telemetry_data["agent_uptime_seconds"] = (datetime.now() - agent_state.started_at).total_seconds()
                telemetry_data["component_health_snapshot"] = agent_state.get_health_snapshot()

                try:
                    telemetry_data["cpu_percent"] = psutil.cpu_percent(interval=None) # Non-blocking
                    telemetry_data["memory_percent"] = psutil.virtual_memory().percent
                except (psutil.AccessDenied, PermissionError) as e:
                    self.logger.warning(f"Permission denied for psutil data collection: {e}. CPU/Memory telemetry will be null.", extra={"error": str(e)})
                    # Values remain None as initialized above

                # Detailed collector status (from agent_state.collectors)
                collectors_status = {}
                if hasattr(agent_state, 'collectors') and isinstance(agent_state.collectors, dict):
                    for name, collector_instance in agent_state.collectors.items():
                        collectors_status[name] = {
                            "running": getattr(collector_instance, 'running', False),
                            "status": getattr(collector_instance, 'status', 'N/A'), # Define status in collector base
                            "last_event_count": getattr(collector_instance, 'event_count', 0) # Define event_count in collector base
                        }
                telemetry_data["collectors_status"] = collectors_status

                # Placeholder for event counts from orchestrator (if tracked globally)
                telemetry_data["orchestrator_event_queue_size"] = agent_state.orchestrator.event_queue.qsize() if hasattr(agent_state, 'orchestrator') and hasattr(agent_state.orchestrator, 'event_queue') else 0
                
                self.logger.info("Agent telemetry collected.", extra=telemetry_data)

            except Exception as e:
                self.logger.error(f"Error collecting telemetry: {e}", exc_info=True)
            
            await asyncio.sleep(self.interval_seconds)

    async def start(self):
        """Starts the telemetry collection background task."""
        self.logger.info("TelemetryCollector starting background task.")
        self._collect_task = asyncio.create_task(self._collect_and_emit_telemetry())

    async def stop(self):
        """Stops the telemetry collection background task."""
        self.logger.info("TelemetryCollector stopping background task.")
        self.stop_event.set()
        if self._collect_task:
            self._collect_task.cancel()
            await asyncio.gather(self._collect_task, return_exceptions=True)
        self.logger.info("TelemetryCollector background task stopped.")