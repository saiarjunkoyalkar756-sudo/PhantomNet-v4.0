import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, TYPE_CHECKING, Optional
import httpx

from core.state import get_agent_state
from utils.logger import get_logger # Use structured logger
from security.jwt_manager import JWTManager # Import JWTManager

if TYPE_CHECKING:
    from collectors.base import Collector

class AgentHealthMonitor:
    def __init__(self, agent_manager_url: str, heartbeat_interval: int = 30, jwt_manager: Optional[JWTManager] = None):
        self.logger = get_logger("phantomnet_agent.self_healing")
        self.agent_manager_url = agent_manager_url
        self.heartbeat_interval = heartbeat_interval
        self.jwt_manager = jwt_manager # Store JWTManager instance
        self.stop_event = asyncio.Event()
        self._heartbeat_task = None
        self.logger.info(f"AgentHealthMonitor initialized. Heartbeat interval: {self.heartbeat_interval}s")

    async def _send_heartbeat(self):
        agent_state = get_agent_state()
        agent_state.last_heartbeat = datetime.now() # Update local heartbeat timestamp

        # Get comprehensive health snapshot from agent_state
        heartbeat_data = agent_state.get_health_snapshot()
        heartbeat_data["event_type"] = "AGENT_HEARTBEAT" # Add event type for structured logging
        
        try:
            headers = {}
            if self.jwt_manager:
                try:
                    token = self.jwt_manager.get_token()
                    headers["Authorization"] = f"Bearer {token}"
                except Exception as e:
                    self.logger.error(f"Failed to generate JWT for heartbeat: {e}", exc_info=True)
                    # Proceed without token, but log warning

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_manager_url}/agents/heartbeat",
                    json=heartbeat_data,
                    headers=headers, # Pass headers here
                    timeout=5.0
                )
                response.raise_for_status()
                self.logger.debug(f"Heartbeat sent successfully for agent {agent_state.agent_id}", extra={"status": "success", "heartbeat_data": heartbeat_data})
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Failed to send heartbeat - HTTP Error: {e.response.status_code} {e.response.text}", extra={"reason": "HTTP_ERROR", "details": str(e), "heartbeat_data": heartbeat_data})
        except httpx.RequestError as e:
            self.logger.error(f"Failed to send heartbeat - Network Error: {e}", extra={"reason": "NETWORK_ERROR", "details": str(e), "heartbeat_data": heartbeat_data})
        except Exception as e:
            self.logger.error(f"Unexpected error sending heartbeat: {e}", exc_info=True, extra={"reason": "UNEXPECTED_ERROR", "details": str(e), "heartbeat_data": heartbeat_data})

    async def _monitor_components(self):
        """
        Monitors the health of individual agent components (e.g., collectors)
        and triggers self-healing actions if necessary.
        """
        agent_state = get_agent_state()
        if not hasattr(agent_state, 'collectors') or not isinstance(agent_state.collectors, dict):
            self.logger.warning("Agent state does not have a valid 'collectors' attribute for monitoring.")
            return

        for name, collector in agent_state.collectors.items():
            collector_running = getattr(collector, 'running', False)
            collector_status = getattr(collector, 'status', 'unknown') # Assuming collector has a status attribute
            
            if not collector_running or collector_status == 'failed':
                self.logger.warning(f"Collector '{name}' is reported as not running or failed. Attempting restart.", extra={"collector": name, "status": collector_status})
                agent_state.update_component_health(name, "restarting", {"reason": "Collector not running or failed", "current_status": collector_status})
                await self._restart_collector(collector)
            else:
                agent_state.update_component_health(name, "running", {"current_status": collector_status})
            # Add more sophisticated checks here (e.g., last data collection time, error rates)

    async def _restart_collector(self, collector: "Collector"):
        """Attempts to restart a given collector."""
        agent_state = get_agent_state()
        collector_name = getattr(collector, 'name', 'unknown_collector')
        self.logger.info(f"Attempting to restart collector '{collector_name}'...", extra={"collector": collector_name, "action": "restart_attempt"})
        agent_state.update_component_health(collector_name, "restarting", {"action": "restart_attempt"})
        try:
            if getattr(collector, 'running', False):
                await collector.stop()
            await collector.start()
            self.logger.info(f"Collector '{collector_name}' restarted successfully.", extra={"collector": collector_name, "action": "restart_success"})
            agent_state.update_component_health(collector_name, "running", {"action": "restart_success"})
        except Exception as e:
            self.logger.error(f"Failed to restart collector '{collector_name}': {e}", exc_info=True, extra={"collector": collector_name, "action": "restart_failed", "error": str(e)})
            agent_state.update_component_health(collector_name, "failed", {"action": "restart_failed", "error": str(e)})

    async def run(self):
        """Main loop for sending heartbeats and monitoring components."""
        while not self.stop_event.is_set():
            await self._send_heartbeat()
            await self._monitor_components() # Check component health after sending heartbeat
            await asyncio.sleep(self.heartbeat_interval)

    async def start(self):
        """Starts the health monitor tasks."""
        logger.info("Starting AgentHealthMonitor.")
        self._heartbeat_task = asyncio.create_task(self.run())

    async def stop(self):
        """Stops the health monitor tasks."""
        logger.info("Stopping AgentHealthMonitor.")
        self.stop_event.set()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            await asyncio.gather(self._heartbeat_task, return_exceptions=True)
        logger.info("AgentHealthMonitor stopped.")