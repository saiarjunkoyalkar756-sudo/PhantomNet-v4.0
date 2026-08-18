import logging
from phantomnet_agent.bus.base import Transport
import httpx
import asyncio
from typing import Dict, Any, Optional, Tuple, Union, AsyncGenerator

from utils.logger import get_logger # Use the structured logger
from security.jwt_manager import JWTManager # Import JWTManager

class HttpTransport(Transport):
    """
    HTTP-based transport for sending events to a backend API.
    Commands reception is currently a placeholder as HTTP is typically pull-based.
    """
    def __init__(self, endpoint: str, client_cert: Optional[Union[str, Tuple[str, str]]] = None, client_key: Optional[str] = None, verify_ca: Union[str, bool] = True, jwt_manager: Optional[JWTManager] = None, agent_state: Optional[Any] = None):
        self.logger = get_logger("phantomnet_agent.bus.http")
        self.endpoint = endpoint
        self.client_cert = client_cert
        self.client_key = client_key
        self.verify_ca = verify_ca
        self.jwt_manager = jwt_manager # Store JWTManager instance
        self.agent_state = agent_state
        self.client: Optional[httpx.AsyncClient] = None
        self.logger.info(f"HttpTransport initialized for endpoint: {self.endpoint}")

    async def connect(self):
        self.logger.info(f"Connecting to HTTP bus at {self.endpoint}...")
        
        # Build cert argument for httpx
        cert_args = None
        if self.client_cert and self.client_key:
            cert_args = (self.client_cert, self.client_key)
        elif self.client_cert: # If only cert is provided, assuming it's a combined cert/key file
            cert_args = self.client_cert

        self.client = httpx.AsyncClient(
            base_url=self.endpoint,
            cert=cert_args,
            verify=self.verify_ca,
            timeout=10.0 # Default timeout for bus operations
        )
        self.logger.info("Connected to HTTP bus.")
        self._update_component_health("connected", {"endpoint": self.endpoint}, bus_connected=True)


    async def disconnect(self):
        if self.client:
            self.logger.info("Disconnecting from HTTP bus...")
            await self.client.aclose()
            self.logger.info("Disconnected from HTTP bus.")
            self.client = None
            self._update_component_health("disconnected", {}, bus_connected=False)

    async def send_event(self, event_data: Dict[str, Any]):
        """
        Sends an event to a backend endpoint. The actual endpoint path
        is determined by the event_type within the event_data.
        """
        if not self.client:
            self.logger.warning("HTTP client not connected, attempting to reconnect for event sending.")
            await self.connect() # Attempt to reconnect
        
        if not self.client:
            self.logger.error("Failed to connect HTTP client for sending event.", extra={"event_data": event_data})
            return

        event_type = event_data.get("event_type", "generic_event")
        # Define endpoint paths based on event type. This can be more sophisticated.
        path_map = {
            "AGENT_HEARTBEAT": "/agents/heartbeat",
            "AGENT_TELEMETRY": "/api/v1/telemetry/ingest", # Placeholder for telemetry
            "AI_ANALYSIS_RESULT": "/api/v1/analysis/ingest", # Placeholder for AI analysis results
            "default": "/api/v1/events/ingest"
        }
        ingest_path = path_map.get(event_type, path_map["default"])

        headers = {"Content-Type": "application/json"}
        if self.jwt_manager:
            try:
                token = self.jwt_manager.get_token()
                headers["Authorization"] = f"Bearer {token}"
            except Exception as e:
                self.logger.error(f"Failed to generate JWT for event '{event_type}': {e}", exc_info=True)
                # Proceed without token, but log warning
        
        self.logger.debug(f"Sending event '{event_type}' to backend {self.endpoint}{ingest_path}", extra={"event_data": event_data})
        try:
            response = await self.client.post(ingest_path, json=event_data, headers=headers, timeout=5.0)
            response.raise_for_status()
            self.logger.debug(f"Event '{event_type}' sent successfully to backend.", extra={"event_data": event_data})
        except httpx.RequestError as e:
            self.logger.warning(f"Failed to send event '{event_type}' to backend ({self.endpoint}{ingest_path}): Network error - {e}", extra={"event_data": event_data, "error": str(e)})
            self._update_component_health("degraded", {"reason": "Network error sending event", "details": str(e)})
        except httpx.HTTPStatusError as e:
            self.logger.warning(f"Failed to send event '{event_type}' to backend ({self.endpoint}{ingest_path}): HTTP error {e.response.status_code} - {e.response.text}", extra={"event_data": event_data, "error": str(e)})
            self._update_component_health("degraded", {"reason": "HTTP error sending event", "details": str(e)})
        except Exception as e:
            self.logger.error(f"Unexpected error sending event '{event_type}' to backend: {e}", exc_info=True, extra={"event_data": event_data})
            self._update_component_health("error", {"reason": "Unexpected error sending event", "details": str(e)})

    def _update_component_health(self, status: str, details: Dict[str, Any], bus_connected: Optional[bool] = None) -> None:
        """Report optional agent health without requiring a global singleton."""
        if self.agent_state is None:
            return
        if bus_connected is not None:
            self.agent_state.bus_connected = bus_connected
        self.agent_state.update_component_health("bus_http", status, details)

    async def receive_commands(self, commands_topic: str) -> AsyncGenerator[Any, None]:
        """
        Stub for receiving commands over HTTP. HTTP is typically pull-based or uses webhooks.
        This implementation simply logs a warning and yields no commands.
        """
        self.logger.warning(f"Command reception is not actively supported for HTTP bus type on topic '{commands_topic}'. This is a no-op.", extra={"topic": commands_topic})
        if False:
            yield None
