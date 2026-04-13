import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from core.state import get_agent_state
# No direct import of AgentExecutor here, it will be accessed via agent_state.orchestrator.agent_executor
from api.log_streaming_api import get_recent_logs_from_file, AGENT_OUTPUT_LOG_PATH


class DashboardReporter:
    """
    Provides functions to generate summaries of agent state, recent commands, and logs
    for a conceptual local UI layer or backend consumption.
    """
    def __init__(self):
        self.logger = get_logger("phantomnet_agent.ui.dashboard")
        self.logger.info("DashboardReporter initialized.")

    def get_agent_summary(self) -> Dict[str, Any]:
        """
        Returns a high-level summary of the agent's current state.
        """
        agent_state = get_agent_state()
        uptime_seconds = (datetime.now() - agent_state.started_at).total_seconds()

        summary = {
            "agent_id": agent_state.agent_id,
            "status": agent_state.status,
            "mode": agent_state.mode,
            "hostname": agent_state.hostname,
            "os": agent_state.os,
            "version": agent_state.version,
            "uptime_seconds": round(uptime_seconds, 2),
            "bus_connected": agent_state.bus_connected,
            "last_heartbeat": agent_state.last_heartbeat.isoformat() if agent_state.last_heartbeat else None,
            "num_collectors": len(agent_state.collectors),
            "num_plugins": len(agent_state.plugins),
            "safe_ai_mode": agent_state.config.agent.safe_ai_mode # Access config directly
        }
        self.logger.debug("Generated agent summary.", extra={"summary": summary})
        return summary

    async def get_last_commands_summary(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Returns a summary of the last N executed commands.
        # TODO: Implement proper command storage and retrieval in AgentExecutor or a dedicated CommandManager.
        """
        agent_state = get_agent_state()
        if not agent_state.orchestrator or not hasattr(agent_state.orchestrator, 'agent_executor'):
            self.logger.warning("Orchestrator or AgentExecutor not available to retrieve commands.")
            return []
        
        agent_executor = agent_state.orchestrator.agent_executor
        
        # Sort commands by timestamp and get the last 'count'
        sorted_commands = sorted(
            agent_executor.active_commands.values(), 
            key=lambda cmd: cmd.timestamp, 
            reverse=True
        )
        
        summary_list = []
        for cmd in sorted_commands[:count]:
            summary_list.append({
                "command_id": cmd.command_id,
                "command_type": cmd.command_type,
                "status": cmd.status,
                "timestamp": cmd.timestamp,
                "result_status": cmd.result.get("status", "N/A"),
                "message": cmd.result.get("message", "N/A"),
            })
        self.logger.debug(f"Generated summary for last {len(summary_list)} commands.", extra={"commands_summary": summary_list})
        return summary_list

    async def get_logs_summary(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Returns the most recent N structured log entries from the agent's main log file.
        """
        self.logger.debug(f"Retrieving last {count} log entries.")
        # This directly calls the helper function used by the API endpoint
        logs = await get_recent_logs_from_file(AGENT_OUTPUT_LOG_PATH, count)
        self.logger.debug(f"Retrieved {len(logs)} log entries.")
        return logs
