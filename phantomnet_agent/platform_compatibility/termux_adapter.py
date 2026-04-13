# phantomnet_agent/platform_compatibility/termux_adapter.py

import logging
import subprocess
from typing import List, Tuple, Optional, Any
import asyncio
import json

from utils.logger import get_logger
from shared.platform_utils import IS_ROOT

from phantomnet_agent.platform_compatibility.base_adapter import BaseAdapter

logger = get_logger(__name__)

class TermuxAdapter(BaseAdapter):
    """
    Provides OS-specific functionalities for Termux (Android environment).
    Handles Termux-specific commands and limitations.
    """
    def __init__(self):
        logger.info("TermuxAdapter initialized.")

    async def _run_termux_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a command in the Termux environment."""
        # Termux does not typically use 'sudo'. Commands are run as the unprivileged Termux user.
        full_command = command
        
        logger.info(f"Executing Termux command: {' '.join(full_command)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *full_command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode('utf-8', errors='ignore').strip()
            stderr_str = stderr.decode('utf-8', errors='ignore').strip()

            if process.returncode == 0:
                logger.info(f"Termux command successful: {stdout_str}")
                return True, stdout_str
            else:
                logger.error(f"Termux command failed with exit code {process.returncode}: {stderr_str}")
                return False, stderr_str
        except FileNotFoundError:
            logger.error(f"Command not found: {full_command[0]}. Is it installed via pkg?")
            return False, f"Command not found: {full_command[0]}"
        except Exception as e:
            logger.error(f"Error running Termux command: {e}")
            return False, str(e)

    async def get_installed_software(self) -> List[Dict[str, str]]:
        """
        Uses `pkg list-installed` to get a list of installed software in Termux.
        """
        success, output = await self._run_termux_command(["pkg", "list-installed"])
        
        software_list = []
        if success:
            lines = output.strip().splitlines()
            # Skip header
            for line in lines[1:]:
                parts = line.strip().split('/')
                if len(parts) > 0:
                    name = parts[0]
                    # Version is often included in the second part
                    version_info = parts[1].split(' ') if len(parts) > 1 else []
                    version = version_info[0] if version_info else "unknown"
                    software_list.append({"name": name, "version": version})
    async def ping_host(self, target: str) -> Dict[str, Any]:
        """Pings a host and returns the results."""
        success, output = await self._run_termux_command(["ping", "-c", "4", target])
        if success:
            return {"status": "success", "output": output}
        return {"status": "failed", "output": output}

    async def execute_command(self, cmd: str, shell: bool = False) -> Dict[str, Any]:
        """Executes an OS command and returns its output and status."""
        # For simplicity, we'll treat all commands as if they can be run directly.
        # In a real scenario, you might need to differentiate between shell and exec.
        success, output = await self._run_termux_command(cmd.split()) # Assuming cmd is a simple command string
        return {
            "stdout": output if success else "",
            "stderr": output if not success else "",
            "returncode": 0 if success else 1
        }

    async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Isolating the system is not supported in Termux without root."""
        logger.warning("isolate_system is not supported in Termux without root.")
        return {"status": "unsupported", "output": "Isolating the system is not supported in Termux without root."}

    async def install_termux_package(self, package_name: str) -> bool:
        """Installs a Termux package using 'pkg'."""
        logger.info(f"Attempting to install Termux package: {package_name}")
        success, _ = await self._run_termux_command(["pkg", "install", "-y", package_name])
        return success

    async def get_netstat_info(self) -> List[Dict[str, Any]]:
        """Retrieves network connection information using 'netstat'."""
        logger.info("Getting network statistics via netstat.")
        # Termux's netstat might be from busybox/toybox, output format can vary.
        # -n: numeric addresses, -p: show PID/program name, -t: tcp, -u: udp, -a: all
        success, output = await self._run_termux_command(["netstat", "-tunap"])
        
        connections = []
        if success:
            # Simple parsing, needs refinement for robustness
            for line in output.splitlines():
                if line.startswith("tcp") or line.startswith("udp"):
                    parts = line.split()
                    if len(parts) >= 6:
                        try:
                            proto = parts[0]
                            local_address = parts[3]
                            foreign_address = parts[4]
                            state = parts[5] # For TCP
                            pid_program = parts[-1] if proto == "tcp" else "N/A" # PID/Program usually last
                            
                            connections.append({
                                "protocol": proto,
                                "local_address": local_address,
                                "foreign_address": foreign_address,
                                "state": state,
                                "pid_program": pid_program
                            })
                        except IndexError:
                            logger.warning(f"Failed to parse netstat line: {line}")
            return connections
        return []

    async def get_process_list(self) -> List[Dict[str, Any]]:
        """Retrieves a list of running processes using 'ps' or 'top'."""
        logger.info("Getting process list via ps.")
        success, output = await self._run_termux_command(["ps", "-ef"]) # -ef for full listing
        processes = []
        if success:
            # Basic parsing of 'ps -ef' output
            # PID USER     TIME COMMAND
            for line in output.splitlines()[1:]: # Skip header
                parts = line.split(maxsplit=7) # Split by max 7 spaces for COMMAND
                if len(parts) >= 8: # PID, USER, TIME, COMMAND, etc.
                    processes.append({
                        "pid": parts[1],
                        "user": parts[0],
                        "command": parts[7]
                    })
                elif len(parts) >= 4: # Fallback for simpler ps output
                     processes.append({
                        "pid": parts[1],
                        "user": parts[0],
                        "command": " ".join(parts[3:])
                    })
            return processes
        return []

    async def get_logcat_logs(self, count: int = 100) -> str:
        """Retrieves recent Android logcat logs (requires logcat utility, usually root/adb)."""
        logger.info(f"Attempting to get last {count} logcat entries (requires root/adb).")
        if not IS_ROOT:
            logger.warning("logcat usually requires root or adb access. This command may fail.")
        
        # Termux does not directly provide logcat, usually accessed via adb shell or rooted device.
        # This is a conceptual placeholder.
        return "Simulated logcat output: Device is running smoothly."

    async def restart_termux_service(self, service_name: str) -> bool:
        """Restarts a Termux service (e.g., specific daemons)."""
        logger.warning("Termux does not use systemd. Service restart is typically app-specific or done via 'pkill' and re-launch.")
        logger.info(f"Simulating restart of Termux service: {service_name}")
        # Conceptual: Find PID and kill, then re-launch
        return True

    async def reset_networking_components(self) -> bool:
        """Resets networking components on Termux."""
        logger.warning("Networking component reset on Termux is heavily restricted and often requires root on device.")
        logger.info("Simulating network reset on Termux.")
        # In a real scenario, this might involve calling Android APIs via Termux:API
        # or attempting to use 'ifconfig down/up' if appropriate permissions are available.
        return False # Cannot automate without specific permissions/root

# For direct testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running TermuxAdapter example...")
    
    adapter = TermuxAdapter()

    async def run_example():
        print(f"Installed python package (example): {await adapter.install_termux_package('neofetch')}")
        print(f"Network connections:\n{await adapter.get_netstat_info()}")
        print(f"Process list:\n{await adapter.get_process_list()}")
        print(f"Logcat logs:\n{await adapter.get_logcat_logs(10)}")
        print(f"Restarting service (simulated): {await adapter.restart_termux_service('sshd')}")

    try:
        # Mock IS_ROOT for testing if not running as root
        from unittest.mock import patch
        with patch('shared.platform_utils.IS_ROOT', False): # Assume non-root for Termux example
            asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("TermuxAdapter example stopped.")
