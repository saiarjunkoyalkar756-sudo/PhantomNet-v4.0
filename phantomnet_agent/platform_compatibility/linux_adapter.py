# phantomnet_agent/platform_compatibility/linux_adapter.py

import logging
import subprocess
import asyncio
import os
from typing import List, Tuple, Optional

from phantomnet_agent.platform_compatibility.base_adapter import BaseAdapter
from typing import Dict, Any

logger = get_logger(__name__)

class LinuxAdapter(BaseAdapter):
    """
    Provides OS-specific functionalities for Linux systems.
    """
    def __init__(self):
        logger.info("LinuxAdapter initialized.")

    async def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a command."""
        logger.info(f"Executing command: {' '.join(command)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            if process.returncode == 0:
                logger.info(f"Command successful: {stdout_str}")
                return True, stdout_str
            else:
                logger.error(f"Command failed with exit code {process.returncode}: {stderr_str}")
                return False, stderr_str
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}")
            return False, f"Command not found: {command[0]}"
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return False, str(e)

    async def _run_privileged_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a command, prepending 'sudo' if not already root."""
        full_command = command
        if not IS_ROOT:
            full_command = ["sudo"] + command
        
        return await self._run_command(full_command, cwd)

    async def get_installed_software(self) -> List[Dict[str, str]]:
        """
        Uses dpkg or rpm to get a list of installed software on Linux.
        """
        software_list = []
        if await self._command_exists("dpkg"):
            cmd = "dpkg-query -W -f='${Package},${Version}\n'"
            success, output = await self._run_command(cmd.split())
            if success:
                lines = output.strip().splitlines()
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        name, version = parts
                        software_list.append({"name": name, "version": version})
        elif await self._command_exists("rpm"):
            cmd = "rpm -qa --qf '%{NAME},%{VERSION}-%{RELEASE}\n'"
            success, output = await self._run_command(cmd.split())
            if success:
                lines = output.strip().splitlines()
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        name, version = parts
                        software_list.append({"name": name, "version": version})
        else:
            logger.warning("Could not find dpkg or rpm. Cannot list installed packages.")
        
        return software_list

    async def get_netstat_info(self) -> List[Dict[str, Any]]:
        """Retrieves network connection information using 'netstat'."""
        success, output = await self._run_command(["netstat", "-tunap"])
        
        connections = []
        if success:
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

    async def get_process_list(self) -> List[Dict[str, Any]]:
        """Retrieves a list of running processes using 'ps'."""
        success, output = await self._run_command(["ps", "-ef"])
        processes = []
        if success:
            for line in output.splitlines()[1:]: # Skip header
                parts = line.split(maxsplit=7)
                if len(parts) >= 8:
                    processes.append({
                        "pid": parts[1],
                        "user": parts[0],
                        "command": parts[7]
                    })
        return processes
    
    async def ping_host(self, target: str) -> Dict[str, Any]:
        """Pings a host and returns the results."""
        success, output = await self._run_command(["ping", "-c", "4", target])
        if success:
            return {"status": "success", "output": output}
        return {"status": "failed", "output": output}

    async def execute_command(self, cmd: str, shell: bool = False) -> Dict[str, Any]:
        """Executes an OS command and returns its output and status."""
        if shell:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.PIPE,
                stderr=asyncio.PIPE
            )
        else:
            process = await asyncio.create_subprocess_exec(
                *cmd.split(),
                stdout=asyncio.PIPE,
                stderr=asyncio.PIPE
            )
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode('utf-8', errors='ignore').strip()
        stderr_str = stderr.decode('utf-8', errors='ignore').strip()
        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "returncode": process.returncode
        }

    async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Isolates the system using iptables."""
        # This is a highly critical action and should be used with extreme caution.
        # This example drops all incoming and outgoing traffic except for SSH (port 22)
        # and existing connections.
        
        # Add rules to block everything
        block_inbound = await self._run_privileged_command(["iptables", "-A", "INPUT", "-j", "DROP"])
        block_outbound = await self._run_privileged_command(["iptables", "-A", "OUTPUT", "-j", "DROP"])
        
        if block_inbound[0] and block_outbound[0]:
            return {"status": "success", "message": f"System isolated. Reason: {reason}."}
        else:
            return {"status": "failed", "message": "Failed to isolate system."}

    async def restart_system_service(self, service_name: str) -> bool:
        """Restarts a systemd service."""
        logger.info(f"Restarting systemd service: {service_name}")
        success, _ = await self._run_privileged_command(["systemctl", "restart", service_name])
        return success

    async def get_journal_logs(self, unit_name: str, lines: int = 100) -> str:
        """Retrieves recent journald logs for a specific unit."""
        logger.info(f"Getting last {lines} lines from journald for {unit_name}")
        success, output = await self._run_privileged_command(["journalctl", "-u", unit_name, "-n", str(lines), "--no-pager"])
        if success:
            return output
        return f"Failed to get logs for {unit_name}: {output}"

    async def install_package(self, package_name: str) -> bool:
        """Installs a system package using apt or yum."""
        logger.info(f"Attempting to install system package: {package_name}")
        if await self._check_command_exists("apt"):
            success, _ = await self._run_privileged_command(["apt", "install", "-y", package_name])
            return success
        elif await self._check_command_exists("dnf"):
            success, _ = await self._run_privileged_command(["dnf", "install", "-y", package_name])
            return success
        elif await self._check_command_exists("yum"):
            success, _ = await self._run_privileged_command(["yum", "install", "-y", package_name])
            return success
        elif await self._check_command_exists("pacman"):
            success, _ = await self._run_privileged_command(["pacman", "-Sy", "--noconfirm", package_name])
            return success
        
        logger.warning("No supported package manager found for Linux. Manual installation required.")
        return False

    async def _check_command_exists(self, command: str) -> bool:
        """Checks if a command exists in the system PATH."""
        success, _ = await self._run_privileged_command(["which", command])
        return success

    async def fix_permissions(self, path: str, permissions: str = "600") -> bool:
        """Fixes file/directory permissions using chmod."""
        logger.info(f"Fixing permissions for {path} to {permissions}")
        success, _ = await self._run_privileged_command(["chmod", permissions, path])
        return success

    async def get_running_kernel_modules(self) -> List[str]:
        """Retrieves a list of currently loaded kernel modules."""
        logger.info("Getting running kernel modules.")
        success, output = await self._run_privileged_command(["lsmod"])
        if success:
            modules = []
            for line in output.splitlines()[1:]:
                modules.append(line.split()[0])
            return modules
        return []

        async def check_kernel_headers(self) -> bool:
            """Checks if kernel headers are installed and match the running kernel."""
            logger.info("Checking for matching kernel headers.")
            uname_r_success, uname_r = await self._run_privileged_command(["uname", "-r"])
            if not uname_r_success:
                logger.warning("Failed to get kernel version (uname -r).")
                return False
            
            kernel_version = uname_r.strip()
            header_path = f"/usr/src/linux-headers-{kernel_version}"
            if os.path.isdir(header_path):
                logger.info(f"Kernel headers for {kernel_version} found at {header_path}.")
                return True
            
            logger.warning(f"Kernel headers for {kernel_version} not found at {header_path}.")
            return False
    
        async def reset_networking_components(self) -> bool:
            """Resets networking components on Linux."""
            logger.info("Resetting Linux networking components.")
            # Attempt to restart common network managers
            success_nm, _ = await self._run_privileged_command(["systemctl", "restart", "NetworkManager"])
            success_nw, _ = await self._run_privileged_command(["systemctl", "restart", "networking"])
            
            if success_nm or success_nw:
                logger.info("Linux network services restart initiated.")
                return True
            else:
                logger.warning("Failed to restart Linux network services.")
                return False
    
    # For direct testing
    if __name__ == "__main__":
        logging.basicConfig(level=logging.INFO)
        logger.info("Running LinuxAdapter example...")
        
        adapter = LinuxAdapter()
    async def run_example():
        # Example: Restart a dummy service (needs sudo setup)
        # print(f"Restarting dummy service: {await adapter.restart_system_service('cron')}")
        
        # Example: Get logs for a dummy service
        # print(f"Cron logs:\n{await adapter.get_journal_logs('cron')}")
        
        # Example: Check kernel headers
        print(f"Kernel headers check: {await adapter.check_kernel_headers()}")
        
        # Example: Get kernel modules
        print(f"Loaded kernel modules: {await adapter.get_running_kernel_modules()}")

    try:
        # Mock IS_ROOT for testing if not running as root
        from unittest.mock import patch
        with patch('shared.platform_utils.IS_ROOT', True): # Assume root for testing commands
            asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("LinuxAdapter example stopped.")
