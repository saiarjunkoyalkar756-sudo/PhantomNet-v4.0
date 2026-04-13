# backend_api/honeypot_service/manager.py
import asyncio
import logging
import importlib
import threading
from typing import Dict, Any, List, Optional

from .models import HoneypotConfig
from .forwarder import forward_event
from .metrics import honeypot_errors_total
from runners.base import HoneypotRunner
from runners.process_runner import ProcessHoneypotRunner # Import the process runner

logger = logging.getLogger(__name__)

class HoneypotManager:
    def __init__(self):
        self.running_honeypots: Dict[str, HoneypotRunner] = {} # Store runner instances
        self.honeypots_store: Dict[str, HoneypotConfig] = {}
        # self.shutdown_events: Dict[str, threading.Event] = {} # Shutdown is now handled by the runner

    async def start_honeypot(self, config: HoneypotConfig):
        if config.honeypot_id in self.running_honeypots and \
           await self.running_honeypots[config.honeypot_id].get_status() == "running":
            logger.warning(f"Honeypot {config.honeypot_id} is already running.")
            return

        logger.info(f"Starting honeypot {config.honeypot_id} of type {config.type} on {config.host}:{config.port}")
        
        try:
            # Instantiate the ProcessHoneypotRunner
            runner = ProcessHoneypotRunner(config.honeypot_id, config.type, config.dict())
            await runner.start() # Start the honeypot process

            self.running_honeypots[config.honeypot_id] = runner
            config.status = await runner.get_status()
            config.pid = await runner.get_pid()
            self.honeypots_store[config.honeypot_id] = config

        except Exception as e:
            logger.error(f"Error starting honeypot {config.honeypot_id}: {e}")
            honeypot_errors_total.labels(
                honeypot_id=config.honeypot_id,
                honeypot_type=config.type,
                error_type=e.__class__.__name__
            ).inc()
            raise

    async def stop_honeypot(self, honeypot_id: str):
        if honeypot_id not in self.running_honeypots:
            logger.warning(f"Honeypot {honeypot_id} is not running or managed by this manager.")
            return

        logger.info(f"Stopping honeypot {honeypot_id}")
        
        runner = self.running_honeypots.pop(honeypot_id)
        try:
            await runner.stop()
        except Exception as e:
            logger.error(f"Error stopping honeypot {honeypot_id}: {e}")
            honeypot_errors_total.labels(
                honeypot_id=honeypot_id,
                honeypot_type=self.honeypots_store.get(honeypot_id).type if self.honeypots_store.get(honeypot_id) else "unknown",
                error_type=e.__class__.__name__
            ).inc()
        
        if honeypot_id in self.honeypots_store:
            config = self.honeypots_store[honeypot_id]
            config.status = await runner.get_status()
            config.pid = await runner.get_pid()
            self.honeypots_store[honeypot_id] = config

    async def get_honeypot_status(self, honeypot_id: str) -> Optional[HoneypotConfig]:
        if honeypot_id in self.honeypots_store:
            config = self.honeypots_store[honeypot_id]
            if honeypot_id in self.running_honeypots:
                runner = self.running_honeypots[honeypot_id]
                config.status = await runner.get_status()
                config.pid = await runner.get_pid()
            return config
        return None

    async def list_honeypots(self) -> List[HoneypotConfig]:
        updated_honeypots = []
        for honeypot_id, config in self.honeypots_store.items():
            if honeypot_id in self.running_honeypots:
                runner = self.running_honeypots[honeypot_id]
                config.status = await runner.get_status()
                config.pid = await runner.get_pid()
            updated_honeypots.append(config)
        return updated_honeypots

# Instantiate the manager
honeypot_manager = HoneypotManager()
