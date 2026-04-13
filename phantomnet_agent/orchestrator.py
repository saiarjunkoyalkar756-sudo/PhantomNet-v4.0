import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import httpx # For fan-out to backend API
import os # For Kafka config
from kafka import KafkaConsumer # Import KafkaConsumer
from datetime import datetime # For NormalizedEvent timestamp
from phantomnet_agent.networking.network_sensor import NetworkSensor # Import the new NetworkSensor

# Corrected imports based on local file structure
from phantomnet_agent.ai_analyzer import AIAnalyzer # Import the new AIAnalyzer class
from phantomnet_agent.schemas.events import AIAnalysisResult # Import new event schemas
from phantomnet_agent.plugins.loader import PluginLoader # Assuming PluginLoader is available for executing plugins
from phantomnet_agent.core.state import get_agent_state
from phantomnet_agent.api.log_streaming_api import manager as log_streaming_manager # For fan-out to dashboard
from phantomnet_agent.bus.base import Transport # Assuming a transport mechanism to send to backend
from phantomnet_agent.bus.http_bus import HttpTransport # Required for type checking in _fan_out_event
from phantomnet_agent.agent import AgentExecutor # Import AgentExecutor
from pydantic import BaseModel, Field # For NormalizedEvent model

logger = logging.getLogger("phantomnet_agent.orchestrator")

# Define NormalizedEvent schema (moved here for simplicity if not in a separate file yet)
class NormalizedEvent(BaseModel):
    agent_id: str
    timestamp: datetime
    event_type: str
    payload: Dict[str, Any]
    ai_analysis_result: Optional[AIAnalysisResult] = None


class Orchestrator:
    """
    The central orchestrator for the PhantomNet agent.
    It now acts as an event processing graph, handling incoming events,
    orchestrating AI reasoning, correlating events, and fanning out results.
    """

    def __init__(self, transport: Transport, plugin_loader: PluginLoader):
        self.logger = logging.getLogger("phantomnet_agent.orchestrator")
        self.event_queue = asyncio.Queue()
        self.transport = transport
        self.plugin_loader = plugin_loader
        self.stop_event = asyncio.Event()
        self._processing_task = None
        self._command_consumer_task = None # New task for Kafka command consumer
        self.safe_ai_mode = get_agent_state().config.agent.safe_ai_mode

        # Initialize AIAnalyzer
        self.ai_analyzer = AIAnalyzer()
        if self.safe_ai_mode:
            self.logger.warning("Orchestrator operating with AIAnalyzer in SAFE AI MODE (simulated inference).")
        else:
            self.logger.info("Orchestrator operating with AIAnalyzer in full AI mode.")
        
        self.agent_executor = AgentExecutor(
            agent_id=get_agent_state().agent_id,
            plugin_loader=self.plugin_loader,
            transport=self.transport
        ) # Initialize AgentExecutor

        # Kafka Consumer for Agent Commands
        self.KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
        self.AGENT_COMMANDS_TOPIC = 'agent-commands'
        self.COMMAND_CONSUMER_GROUP = f'agent-{get_agent_state().agent_id}-commands'
        self._kafka_command_consumer: Optional[KafkaConsumer] = None # Will be initialized in start_consumer

        self.logger.info("PhantomNet Orchestrator Initialized as Event Processing Graph.")


    async def ingest_event(self, event: Dict[str, Any]):
        """
        Ingests a raw event into the orchestrator's processing queue.
        """
        await self.event_queue.put(event)
        logger.debug(f"Event ingested into orchestrator queue: {event.get('event_type', 'N/A')}")

    async def _consume_agent_commands(self):
        """
        Consumes commands from the Kafka topic and ingests them into the event queue.
        """
        agent_id = get_agent_state().agent_id
        self.logger.info(f"Starting Kafka command consumer for agent {agent_id} on topic: {self.AGENT_COMMANDS_TOPIC}")

        # Wait for Kafka to be ready
        await asyncio.sleep(10)

        try:
            self._kafka_command_consumer = KafkaConsumer(
                self.AGENT_COMMANDS_TOPIC,
                bootstrap_servers=self.KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=self.COMMAND_CONSUMER_GROUP,
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
        except Exception as e:
            self.logger.error(f"Failed to connect Kafka command consumer: {e}", exc_info=True)
            return

        self.logger.info("Kafka command consumer connected. Waiting for commands...")
        for message in self._kafka_command_consumer:
            if self.stop_event.is_set():
                break

            command_data = message.value
            
            # Filter commands by agent_id and tenant_id
            target_agent_id = command_data.get("target_agent_id")
            command_tenant_id = command_data.get("tenant_id")
            current_agent_tenant_id = str(get_agent_state().config.agent.tenant_id) # Assuming agent config holds its tenant ID

            if target_agent_id == agent_id and command_tenant_id == current_agent_tenant_id:
                self.logger.info(f"Received command for this agent: {command_data.get('command_type')}")
                
                # Push the command into the event_queue for processing by _process_event_loop
                # Format it as an AGENT_COMMAND_FROM_UI event, as the orchestrator already handles this structure.
                await self.event_queue.put({
                    "event_type": "AGENT_COMMAND_FROM_UI",
                    "command_id": command_data.get("task_id"),
                    "command_type": command_data.get("command_type"),
                    "payload": command_data.get("arguments", {}),
                    "issued_by": command_data.get("issued_by"),
                    "issued_at": command_data.get("issued_at"),
                    "source": "kafka_command_bus"
                })
            else:
                self.logger.debug(f"Ignoring command for agent {target_agent_id} (tenant {command_tenant_id}). Not for this agent ({agent_id}, tenant {current_agent_tenant_id}).")
        
        self.logger.info("Kafka command consumer loop finished.")
        if self._kafka_command_consumer:
            self._kafka_command_consumer.close()
            self._kafka_command_consumer = None

    async def _process_event_loop(self):
        """
        Continuous loop to pull events from the queue, process them, and fan out.
        """
        while not self.stop_event.is_set():
            try:
                event = await self.event_queue.get()
                self.event_queue.task_done()
                
                # Step 1: Normalize Event
                # TODO: Implement a more sophisticated normalization step using schemas/events.py
                # For now, we assume event is mostly in a usable format for AIAnalyzer
                normalized_event = NormalizedEvent(
                    agent_id=get_agent_state().agent_id,
                    timestamp=datetime.now(),
                    event_type=event.get("event_type", "UNKNOWN_EVENT"),
                    payload=event # For now, payload is the raw event
                )
                self.logger.debug(f"Normalized event: {normalized_event.event_type}")

                # Handle AGENT_COMMAND_FROM_UI events first, as they trigger immediate actions
                if normalized_event.event_type == "AGENT_COMMAND_FROM_UI":
                    command_type = normalized_event.payload.get("command_type")
                    command_payload = normalized_event.payload.get("payload", {})
                    command_id = normalized_event.payload.get("command_id")

                    if command_type == "execute_os_command":
                        await self.agent_executor.execute_os_command(command_id, cmd=command_payload.get("cmd"), shell=command_payload.get("shell", False))
                    elif command_type == "control_collector":
                        await self.agent_executor.control_collector(command_id, collector_name=command_payload.get("collector_name"), action=command_payload.get("action"))
                    elif command_type == "run_scan_task":
                        await self.agent_executor.run_scan_task(command_id, plugin_name=command_payload.get("plugin_name"), args=command_payload.get("args", {}))
                    else:
                        self.logger.warning(f"Unknown AGENT_COMMAND_FROM_UI command type: {command_type}")
                        await self.agent_executor._stream_response_to_ui(command_id, "failed", f"Unknown command type: {command_type}")
                    
                    # Do not process further down the AI/Correlation pipeline for direct UI commands
                    continue 

                # Step 2: AI Reasoning Upgrade (Threat context, confidence, attribution, risk)
                # Assuming events from collectors/logs will be the 'threat_event' for AIAnalyzer
                ai_analysis_result: AIAnalysisResult = await self.ai_analyzer.reason_on_threat(normalized_event.payload)
                normalized_event.ai_analysis_result = ai_analysis_result
                self.logger.info(f"Event {normalized_event.event_type} (ID: {normalized_event.payload.get('event_id', 'N/A')}) enriched by AI reasoning. Status: {ai_analysis_result.status}", extra={"ai_result": ai_analysis_result.model_dump()})

                # Step 3: Event Correlation (Placeholder)
                # This would involve looking at multiple events over time,
                # e.g., identifying sequences of reconnaissance followed by exploitation.
                # Pass the entire normalized_event for correlation
                correlated_findings = await self._correlate_event(normalized_event) 
                if correlated_findings:
                    normalized_event.payload["correlated_findings"] = correlated_findings
                    self.logger.info(f"Event {normalized_event.event_type} (ID: {normalized_event.payload.get('event_id', 'N/A')}) correlated with findings: {correlated_findings}")

                # Step 4: Plugin Execution Flow
                # Pass the entire normalized_event for plugin execution
                await self._execute_plugins_for_event(normalized_event)

                # Step 5: Fan-out Delivery
                await self._fan_out_event(normalized_event)

            except asyncio.CancelledError:
                logger.info("Event processing loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}", exc_info=True)
                await asyncio.sleep(1) # Prevent tight loop on error

    async def _correlate_event(self, normalized_event: NormalizedEvent) -> List[str]:
        """
        Conceptual event correlation logic.
        In a real system, this would be complex, involving stateful analysis
        across multiple events over a time window.
        """
        findings = []
        event_payload = normalized_event.payload

        if event_payload.get("event_type") == "NETWORK_CONNECTION" and event_payload.get("remote_address", "").startswith("1.2.3.4"):
            findings.append("Connection to known suspicious IP.")
        if event_payload.get("event_type") == "PROCESS_CREATED" and "sudo" in event_payload.get("cmdline", "").lower():
            findings.append("Potential privileged command execution.")
        
        # Integrate with CognitiveCore for high-level correlation (now via AIAnalyzer)
        # Placeholder for more advanced correlation using AIAnalyzer results if needed
        if normalized_event.ai_analysis_result and normalized_event.ai_analysis_result.risk_score > 50:
            findings.append(f"High risk score ({normalized_event.ai_analysis_result.risk_score:.2f}) indicates potential severe incident.")

        await asyncio.sleep(0.01) # Simulate async operation
        return findings

    async def _execute_plugins_for_event(self, normalized_event: NormalizedEvent):
        """
        Triggers relevant plugins based on the event.
        """
        event_id = normalized_event.payload.get("event_id", "N/A")
        risk_score = normalized_event.ai_analysis_result.risk_score if normalized_event.ai_analysis_result else 0.0

        # Example: If a threat is detected, run an incident response plugin
        if risk_score > 70: # Using the 0-100 scale now
            self.logger.info(f"High risk event detected. Attempting to trigger response plugins for event {event_id}", extra={"event_id": event_id, "risk_score": risk_score})
            for plugin_name, plugin in self.plugin_loader.loaded_plugins.items():
                if "response" in plugin.manifest.permissions: # Check for a conceptual 'response' permission
                    self.logger.debug(f"Executing response plugin: {plugin_name}", extra={"plugin_name": plugin_name, "event_id": event_id})
                    try:
                        sandbox = self.plugin_loader.get_sandbox() # Get sandbox instance
                        entrypoint = plugin.get_entrypoint()
                        # Pass a copy of the normalized event's payload to avoid plugins modifying the original
                        result = await sandbox.run_plugin_function(entrypoint, plugin.manifest.permissions, normalized_event.payload.copy()) 
                        self.logger.info(f"Plugin {plugin_name} executed for event {event_id}. Result: {result}", extra={"plugin_name": plugin_name, "event_id": event_id, "plugin_result": result})
                    except Exception as e:
                        self.logger.error(f"Error executing plugin {plugin_name} for event {event_id}: {e}", exc_info=True, extra={"plugin_name": plugin_name, "event_id": event_id})
        await asyncio.sleep(0.01) # Simulate async operation


    async def _fan_out_event(self, normalized_event: NormalizedEvent):
        """
        Sends the processed and enriched event to various downstream consumers.
        """
        event_json = normalized_event.model_dump_json() # Use pydantic's method to get JSON string
        event_id = normalized_event.payload.get("event_id", "N/A")

        # 1. To Dashboard (via WebSocket)
        await log_streaming_manager.ingest_log(event_json)
        self.logger.debug(f"Fanned out event to dashboard: {event_id}", extra={"event_id": event_id})

        # 2. To Backend API /api/v1/logs/ingest
        backend_ingest_url = f"{get_agent_state().config.agent.manager_url}/api/v1/logs/ingest"
        try:
            # Use the transport's send_logs_to_backend if it's an HttpTransport
            # This method will be implemented in http_bus.py later
            if isinstance(self.transport, HttpTransport):
                await self.transport.send_logs_to_backend(normalized_event.model_dump()) # Send dict
            else: # Fallback to generic httpx for other transports if needed, or error
                async with httpx.AsyncClient() as client:
                    response = await client.post(backend_ingest_url, content=event_json, headers={"Content-Type": "application/json"}, timeout=5.0)
                    response.raise_for_status()
            self.logger.debug(f"Fanned out event to backend API: {event_id}", extra={"event_id": event_id})
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Failed to fan out event to backend API - HTTP Error: {e.response.status_code} {e.response.text}", extra={"event_id": event_id, "error": str(e)})
        except httpx.RequestError as e:
            self.logger.error(f"Failed to fan out event to backend API - Network Error: {e}", extra={"event_id": event_id, "error": str(e)})
        except Exception as e:
            self.logger.error(f"Unexpected error fanning out event to backend API: {e}", exc_info=True, extra={"event_id": event_id})

        # 3. To SOC Copilot (conceptual)
        # This would typically be a specific endpoint or queue for the SOC Copilot
        if normalized_event.ai_analysis_result and normalized_event.ai_analysis_result.risk_score > 50: # Using 0-100 scale
            self.logger.info(f"Forwarding high-risk event {event_id} to SOC Copilot (conceptual).", extra={"event_id": event_id, "risk_score": normalized_event.ai_analysis_result.risk_score})
            # await self.transport.send_event("soc_copilot_channel", normalized_event.model_dump()) # Example using transport

        # 4. To Red Team Simulator (conceptual)
        if normalized_event.event_type == "NETWORK_CONNECTION" and normalized_event.payload.get("remote_address", "").startswith("1.2.3.4"):
             self.logger.info(f"Notifying Red Team Simulator about suspicious network activity (conceptual).", extra={"event_id": event_id, "remote_address": normalized_event.payload.get("remote_address")})
            # await self.transport.send_event("red_team_simulator_channel", normalized_event.model_dump()) # Example using transport
        
        await asyncio.sleep(0.01) # Small delay to prevent busy-looping

    async def start(self):
        """Starts the orchestrator's event processing and command consumption."""
        self.logger.info("Orchestrator starting event processing.")
        await self.agent_executor.start()
        self._processing_task = asyncio.create_task(self._process_event_loop())
        # Start the command consumer task
        self._command_consumer_task = asyncio.create_task(self._consume_agent_commands())
        self.logger.info("Kafka command consumer task started.")

    async def stop(self):
        """Stops the orchestrator's event processing and command consumption."""
        self.logger.info("Orchestrator stopping event processing.")
        self.stop_event.set()
        await self.agent_executor.stop()
        if self._processing_task:
            self._processing_task.cancel()
            await asyncio.gather(self._processing_task, return_exceptions=True)
        
        # Cancel the command consumer task
        if self._command_consumer_task:
            self._command_consumer_task.cancel()
            try:
                await self._command_consumer_task
            except asyncio.CancelledError:
                self.logger.info("Kafka command consumer task cancelled.")
        if self._kafka_command_consumer:
            self._kafka_command_consumer.close()
            self.logger.info("Kafka command consumer closed.")

        await self.event_queue.join() # Wait until all queued tasks are done
        self.logger.info("Orchestrator event processing stopped.")