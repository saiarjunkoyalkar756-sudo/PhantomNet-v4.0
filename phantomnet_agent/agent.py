import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

from core.state import get_agent_state
from plugins.loader import PluginLoader
from api.log_streaming_api import manager as log_streaming_manager
from schemas.actions import AgentCommand
from bus.base import Transport

from networking.network_sensor import NetworkSensor
from networking.backend_client import BackendClient

from actions.network_actions import NetworkActions
from actions.system_actions import SystemActions
from actions.process_actions import ProcessActions

from core.health_monitor import AgentHealthMonitor

PID_FILE = Path(get_agent_state().config.agent.log_dir) / "agent.pid"

class AgentExecutor:
    """
    Handles the execution of agent-specific commands and manages the agent's lifecycle
    and self-healing capabilities.
    """

    def __init__(
        self, agent_id: str, plugin_loader: PluginLoader, transport: Optional[Transport] = None
    ):
        self.logger = logging.getLogger("phantomnet_agent.agent_executor")
        self.plugin_loader = plugin_loader
        self.transport = transport
        self.active_commands: Dict[str, AgentCommand] = {}

        # Core Components
        self.event_queue = asyncio.Queue()
        ws_url = (
            get_agent_state().config.agent.manager_url.replace("http", "ws")
            + "/ws/network"
        )
        self.backend_client = BackendClient(
            agent_id=agent_id, uri=ws_url, event_queue=self.event_queue
        )

        # Action Handlers
        self.network_actions = NetworkActions(self.logger, transport=self.transport)
        self.system_actions = SystemActions(self.logger, transport=self.transport)
        self.process_actions = ProcessActions(self.logger, transport=self.transport)

        # Collectors - Must be registered here for health monitoring
        self.network_sensor = NetworkSensor(event_queue=self.event_queue)
        self.collectors: Dict[str, Any] = {
            "network_sensor": self.network_sensor,
            # In the future, other collectors like FileMonitor, ProcessMonitor would be added here
        }

        # Self-Healing and Monitoring
        self.health_monitor = AgentHealthMonitor(self)

        self.logger.info("AgentExecutor initialized with all components.")

    async def _stream_response_to_ui(
        self,
        command_id: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Streams a response update back to the UI Console via WebSocket."""
        # Update the internal command status
        if command_id in self.active_commands:
            command = self.active_commands[command_id]
            command.status = status
            command.result.update({"message": message, "details": details or {}})
            command.timestamp = datetime.now().isoformat()

        response_event = {
            "event_type": "AGENT_COMMAND_RESPONSE",
            "command_id": command_id,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "message": message,
            "details": details or {},
        }
        await log_streaming_manager.broadcast(json.dumps(response_event))

    async def execute_command(self, command: AgentCommand) -> AgentCommand:
        """
        Main entry point for dispatching and executing an AgentCommand.
        """
        command.status = "in_progress"
        self.active_commands[command.command_id] = command
        self.logger.info(
            f"Executing command: {command.command_type} (ID: {command.command_id})",
            extra={"command": command.model_dump()},
        )
        await self._stream_response_to_ui(
            command.command_id,
            "in_progress",
            f"Command '{command.command_type}' is in progress.",
        )

        result_details: Dict[str, Any] = {}
        try:
            handler_map = {
                "execute_os_command": lambda: self.system_actions.execute_os_command(
                    command.payload.get("cmd", ""),
                    shell=command.payload.get("shell", False),
                    command_id=command.command_id,
                ),
                "control_collector": lambda: self._control_collector_from_command(
                    command
                ),
                "run_scan_task": lambda: self._run_scan_task(command),
                "ping_host": lambda: self.network_actions.ping_host(
                    command.payload.get("target")
                ),
                "block_network_address": lambda: self.network_actions.block_address(
                    command.payload.get("address")
                ),
                "isolate_system": lambda: self.system_actions.isolate_system(
                    command.payload.get("reason")
                ),
            }
            if command.command_type in handler_map:
                result_details = await handler_map[command.command_type]()
            else:
                raise ValueError(f"Unknown command type: {command.command_type}")

            result_status = result_details.get("status", "completed")
            command.result = result_details
            await self._stream_response_to_ui(
                command.command_id,
                result_status,
                f"Command '{command.command_type}' {result_status}.",
                result_details,
            )

        except Exception as e:
            result_status = "failed"
            command.result = {"error": str(e)}
            self.logger.error(
                f"Error executing command '{command.command_type}': {e}",
                exc_info=True,
                extra={"command": command.model_dump()},
            )
            await self._stream_response_to_ui(
                command.command_id, "failed", f"Command '{command.command_type}' failed: {e}", {"error": str(e)}
            )

        command.status = result_status
        return command

    async def _control_collector_from_command(
        self, command: AgentCommand
    ) -> Dict[str, Any]:
        """
        Parses a 'control_collector' command and calls the generic control logic.
        """
        collector_name = command.payload.get("collector_name")
        action = command.payload.get("action")  # "start", "stop", or "restart"
        return await self.control_collector(collector_name, action)

    async def control_collector(
        self, collector_name: str, action: str
    ) -> Dict[str, Any]:
        """
        Generic logic to control a collector. Reusable by the health monitor.
        """
        if collector_name not in self.collectors:
            return {"status": "failed", "message": f"Collector '{collector_name}' not found."}

        collector = self.collectors[collector_name]
        is_running = hasattr(collector, "is_alive") and collector.is_alive()

        try:
            if action == "start":
                if is_running:
                    return {"status": "success", "message": f"Collector '{collector_name}' is already running."}
                collector.start()
                return {"status": "success", "message": f"Collector '{collector_name}' started successfully."}
            elif action == "stop":
                if not is_running:
                    return {"status": "success", "message": f"Collector '{collector_name}' is already stopped."}
                collector.stop()
                return {"status": "success", "message": f"Collector '{collector_name}' stopped successfully."}
            elif action == "restart":
                if is_running:
                    collector.stop()
                    # Give it a moment to stop before restarting
                    await asyncio.sleep(1)
                collector.start()
                return {"status": "success", "message": f"Collector '{collector_name}' restarted successfully."}
            else:
                return {"status": "failed", "message": f"Invalid action '{action}' for collector '{collector_name}'."}
        except Exception as e:
            self.logger.error(
                f"Error controlling collector '{collector_name}' with action '{action}': {e}",
                exc_info=True,
            )
            return {"status": "error", "message": f"Failed to {action} collector '{collector_name}': {e}"}

    async def _run_scan_task(self, command: AgentCommand) -> Dict[str, Any]:
        """Helper to execute a scan task using a plugin."""
        plugin_name = command.payload.get("plugin_name")
        args = command.payload.get("args", {})

        plugin = self.plugin_loader.loaded_plugins.get(plugin_name)
        if not plugin:
            return {"status": "failed", "message": f"Plugin '{plugin_name}' not found."}

        if "network:scan" not in plugin.manifest.permissions:
            return {
                "status": "failed",
                "message": f"Plugin '{plugin_name}' does not have 'network:scan' permission.",
            }

        try:
            sandbox = self.plugin_loader.get_sandbox(
                self.plugin_loader.allowed_permissions
            )
            entrypoint = plugin.get_entrypoint()
            plugin_result = await sandbox.run_plugin_function(
                entrypoint, plugin.manifest.permissions, **args
            )

            if plugin_result["status"] == "success":
                return {"status": "completed", "plugin_output": plugin_result["result"]}
            else:
                return {"status": "failed", "plugin_output": plugin_result["reason"]}
        except Exception as e:
            self.logger.error(
                f"Error running scan task with plugin '{plugin_name}': {e}", exc_info=True
            )
            return {"status": "error", "message": f"Error executing plugin '{plugin_name}': {e}"}

    async def start(self):
        """Starts all agent background tasks and creates the PID file."""
        self.logger.info("AgentExecutor starting all background tasks...")
        
        # Write PID file for tamper detection
        try:
            with open(PID_FILE, "w") as f:
                f.write(str(os.getpid()))
            self.logger.info(f"Agent PID file created at {PID_FILE}")
        except IOError as e:
            self.logger.error(f"Failed to create PID file: {e}")

        for name, collector in self.collectors.items():
            if hasattr(collector, "start") and callable(collector.start):
                collector.start()
                self.logger.info(f"Collector '{name}' started.")
        
        asyncio.create_task(self.backend_client.run())
        self.logger.info("Backend client task created.")
        
        self.health_monitor.start()
        self.logger.info("Agent Health Monitor started.")

    async def stop(self):
        """Stops all agent background tasks and cleans up the PID file."""
        self.logger.info("AgentExecutor stopping all background tasks...")
        self.health_monitor.stop()
        for name, collector in self.collectors.items():
            if hasattr(collector, "stop") and callable(collector.stop):
                collector.stop()
                self.logger.info(f"Collector '{name}' stopped.")

        self.backend_client.stop()
        self.logger.info("Backend client stopped.")

        # Clean up PID file
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
                self.logger.info("Agent PID file removed.")
        except IOError as e:
            self.logger.error(f"Failed to remove PID file: {e}")