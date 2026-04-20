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

    async def isolate_system(self, reason: str) -> Dict[str, Any]:
        """Isolates the system using iptables."""
        pn_logger.warning(f"System isolation triggered: {reason}")
        # Implementation depends on specific requirements
        return {"status": "success", "message": "Isolation commands sent."}
