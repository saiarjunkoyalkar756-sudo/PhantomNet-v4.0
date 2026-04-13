# runners/process_runner.py
import asyncio
import os
import sys
import threading
from typing import Dict, Any, Optional

from .base import HoneypotRunner

class ProcessHoneypotRunner(HoneypotRunner):
    """
    Manages a honeypot instance as a separate local process.
    """
    def __init__(self, honeypot_id: str, honeypot_type: str, config: Dict[str, Any]):
        super().__init__(honeypot_id, honeypot_type, config)
        self._process: Optional[asyncio.Process] = None

    async def start(self) -> None:
        if self.status == "running" and self._process and self._process.returncode is None:
            return # Already running

        # Path to the run_honeypot_process.py script
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_honeypot_process.py'))

        # Prepare command-line arguments for the subprocess
        cmd = [
            sys.executable, # Use the same Python interpreter
            script_path,
            "--honeypot_id", self.honeypot_id,
            "--honeypot_type", self.honeypot_type,
            "--port", str(self.config["port"])
        ]

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self.status = "running"
        asyncio.create_task(self._monitor_process()) # Start monitoring the process
        
    async def stop(self) -> None:
        if self._process and self._process.returncode is None:
            self._process.terminate()
            await self._process.wait() # Wait for the process to actually terminate
        self.status = "stopped"
        self._process = None

    async def get_status(self) -> str:
        if self._process and self._process.returncode is None:
            return "running"
        elif self._process and self._process.returncode is not None:
            return "exited" # Process exited
        return "stopped"

    async def get_pid(self) -> Any:
        return self._process.pid if self._process else None

    async def _monitor_process(self):
        """Monitors the subprocess for output and termination."""
        if not self._process:
            return

        while self._process.returncode is None:
            # Read stdout and stderr without blocking indefinitely
            stdout_data = await self._process.stdout.readline()
            if stdout_data:
                print(f"[Honeypot {self.honeypot_id} STDOUT]: {stdout_data.decode().strip()}")
            
            stderr_data = await self._process.stderr.readline()
            if stderr_data:
                print(f"[Honeypot {self.honeypot_id} STDERR]: {stderr_data.decode().strip()}")
            
            await asyncio.sleep(0.1) # Prevent busy-waiting

        print(f"Honeypot {self.honeypot_id} process exited with code {self._process.returncode}")
        self.status = "exited"
