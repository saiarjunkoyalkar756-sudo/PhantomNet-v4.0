# phantomnet_agent/platform_compatibility/linux_adapter.py
import logging
import subprocess
import asyncio
import os
import re
from typing import List, Tuple, Optional, Dict, Any

from phantomnet_agent.platform_compatibility.base_adapter import BaseAdapter

# Simple root check
IS_ROOT = os.getuid() == 0

logger = logging.getLogger(__name__)

class LinuxAdapter(BaseAdapter):
    """
    Provides OS-specific functionalities for Linux systems with WSL2 resilience.
    """
    def __init__(self):
        logger.info("LinuxAdapter initialized.")

    async def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a command."""
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
                return True, stdout_str
            else:
                return False, stderr_str
        except Exception as e:
            return False, str(e)

    async def _run_privileged_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a command, prepending 'sudo' if not already root."""
        full_command = command
        if not IS_ROOT:
            full_command = ["sudo"] + command
        return await self._run_command(full_command, cwd)

    async def get_installed_software(self) -> List[Dict[str, str]]:
        """Return Debian package inventory when the local package manager is available."""
        success, output = await self._run_command(
            ["dpkg-query", "-W", "-f=${Package}\\t${Version}\\n"]
        )
        if not success:
            logger.warning("Package inventory is unavailable: %s", output)
            return []
        software: list[Dict[str, str]] = []
        for line in output.splitlines():
            name, separator, version = line.partition("\\t")
            if separator and name and version:
                software.append({"name": name, "version": version})
        return software

    async def get_process_by_pid(self, pid: int) -> Dict[str, Any]:
        """Return a bounded process record without invoking a shell."""
        if pid <= 0:
            return {"status": "failed", "detail": "PID must be a positive integer."}
        success, output = await self._run_command(["ps", "-p", str(pid), "-o", "pid=,user=,args="])
        if not success or not output:
            return {"status": "failed", "detail": "Process was not found or cannot be inspected."}
        parts = output.split(maxsplit=2)
        if len(parts) < 3:
            return {"status": "failed", "detail": "Process inspection returned an unexpected format."}
        return {"status": "success", "pid": int(parts[0]), "user": parts[1], "command": parts[2]}

    async def ping_host(self, target: str) -> Dict[str, Any]:
        """Run a bounded single ICMP probe without shell interpolation."""
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.:-]{0,252}", target):
            return {"status": "failed", "detail": "Target is not a valid hostname or IP literal."}
        success, output = await self._run_command(["ping", "-c", "1", "-W", "2", target])
        return {
            "status": "success" if success else "failed",
            "output": output,
        }

    async def block_address(self, address: str) -> Dict[str, Any]:
        """Fail closed until an allowlisted, verified firewall provider is configured."""
        return {
            "status": "failed",
            "enforced": False,
            "verified": False,
            "detail": f"Address blocking for {address} requires the governed local or cloud firewall adapter; no rule was changed.",
        }

    async def kill_process(self, pid: int) -> Dict[str, Any]:
        """Fail closed until a policy-bound process-response provider is configured."""
        return {
            "status": "failed",
            "enforced": False,
            "verified": False,
            "detail": f"Process termination for PID {pid} requires a configured verified endpoint provider; no process was terminated.",
        }

    async def execute_command(self, cmd: str, shell: bool = False) -> Dict[str, Any]:
        """Reject generic command execution in the endpoint adapter safety boundary."""
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": "Generic OS command execution is disabled without a policy-bound endpoint provider.",
            "enforced": False,
            "verified": False,
        }

    async def get_netstat_info(self) -> List[Dict[str, Any]]:
        """Retrieves network connection information with fallbacks for WSL2."""
        connections = []
        
        # Try conntrack first if available
        conntrack_data = await self.get_conntrack_info()
        if conntrack_data:
            return conntrack_data

        # Fallback to netstat
        success, output = await self._run_command(["netstat", "-tunap"])
        if success:
            for line in output.splitlines():
                if line.startswith(("tcp", "udp")):
                    parts = line.split()
                    if len(parts) >= 6:
                        connections.append({
                            "protocol": parts[0],
                            "local_address": parts[3],
                            "foreign_address": parts[4],
                            "state": parts[5] if parts[0].startswith("tcp") else "N/A",
                            "pid_program": parts[-1]
                        })
        
        # Final fallback to /proc/net/tcp for basic info
        if not connections:
            connections = await self._parse_proc_net_tcp()
            
        return connections

    async def get_conntrack_info(self) -> List[Dict[str, Any]]:
        """
        Parses /proc/net/nf_conntrack with WSL2 fallbacks for missing counters.
        """
        conntrack_path = "/proc/net/nf_conntrack"
        if not os.path.exists(conntrack_path):
            return []

        connections = []
        try:
            with open(conntrack_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    # Example conntrack line:
                    # ipv4 2 tcp 6 299 ESTABLISHED src=172.17.0.2 dst=172.17.0.1 sport=5432 dport=56788 packages=1 bytes=120
                    
                    conn = {"protocol": parts[2], "state": parts[3] if parts[2] == "tcp" else "N/A"}
                    
                    # Extract key-value pairs
                    for p in parts:
                        if '=' in p:
                            key, val = p.split('=', 1)
                            if key == "src": conn["local_address"] = val
                            elif key == "dst": conn["foreign_address"] = val
                            elif key == "sport": conn["local_port"] = val
                            elif key == "dport": conn["foreign_port"] = val
                            elif key == "packets":
                                try:
                                    conn["packet_count"] = int(val)
                                except ValueError:
                                    conn["packet_count"] = 0
                            elif key == "bytes":
                                try:
                                    conn["byte_count"] = int(val)
                                except ValueError:
                                    conn["byte_count"] = 0
                    
                    # WSL2 Fallback: If packet_count is missing, default to 0 to avoid casting errors
                    if "packet_count" not in conn:
                        conn["packet_count"] = 0
                        
                    connections.append(conn)
        except Exception as e:
            logger.error(f"Error reading conntrack: {e}")
            
        return connections

    async def _parse_proc_net_tcp(self) -> List[Dict[str, Any]]:
        """Directly parses /proc/net/tcp for stealthier or fallback collection."""
        connections = []
        for proto in ["tcp", "tcp6", "udp", "udp6"]:
            path = f"/proc/net/{proto}"
            if not os.path.exists(path):
                continue
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()[1:] # Skip header
                    for line in lines:
                        parts = line.strip().split()
                        local_addr, local_port = self._decode_address(parts[1])
                        rem_addr, rem_port = self._decode_address(parts[2])
                        connections.append({
                            "protocol": proto,
                            "local_address": f"{local_addr}:{local_port}",
                            "foreign_address": f"{rem_addr}:{rem_port}",
                            "state": parts[3],
                            "inode": parts[9]
                        })
            except Exception:
                continue
        return connections

    def _decode_address(self, addr_hex: str) -> Tuple[str, int]:
        """Decodes hex addresses from /proc/net/tcp."""
        parts = addr_hex.split(':')
        ip_hex = parts[0]
        port = int(parts[1], 16)
        
        if len(ip_hex) == 8: # IPv4
            ip = ".".join(str(int(ip_hex[i:i+2], 16)) for i in range(6, -1, -2))
        else: # IPv6 (simplified)
            ip = ip_hex # Keep hex for IPv6 for now
            
        return ip, port

    async def get_process_list(self) -> List[Dict[str, Any]]:
        """Retrieves process list with 'ps'."""
        success, output = await self._run_command(["ps", "-ef"])
        processes = []
        if success:
            for line in output.splitlines()[1:]:
                parts = line.split(maxsplit=7)
                if len(parts) >= 8:
                    processes.append({"pid": parts[1], "user": parts[0], "command": parts[7]})
        return processes

    async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Fail closed until a configured endpoint provider can prove host isolation.

        The backend must not interpret command acceptance as endpoint enforcement. A local
        host-isolation implementation needs an explicit management-path allowlist, an
        operator confirmation boundary, and post-command verification; none is inferred
        from a generic agent command.
        """
        logger.error(
            "Host isolation was requested without a configured verified provider: %s; duration=%s",
            reason,
            duration_seconds,
        )
        return {
            "status": "failed",
            "enforced": False,
            "verified": False,
            "rollback_available": False,
            "detail": "Host isolation requires a configured and verifiable endpoint-management provider; no firewall state was changed.",
        }
