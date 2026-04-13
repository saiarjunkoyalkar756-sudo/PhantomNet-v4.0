# phantomnet_agent/platform_compatibility/windows_adapter.py

import logging
import subprocess
from typing import List, Tuple, Optional, Any
import asyncio

from utils.logger import get_logger
from shared.platform_utils import IS_ROOT

logger = get_logger(__name__)

# Conditional import for pywin32, wmi
try:
    import win32serviceutil
    import wmi
    PYWIN32_WMI_AVAILABLE = True
except ImportError:
    PYWIN32_WMI_AVAILABLE = False
    logger.warning("pywin32 or WMI not available. Windows-specific features may be limited.")

from phantomnet_agent.platform_compatibility.base_adapter import BaseAdapter
import json

logger = get_logger(__name__)

# Conditional import for pywin32, wmi
try:
    import win32serviceutil
    import wmi
    PYWIN32_WMI_AVAILABLE = True
except ImportError:
    PYWIN32_WMI_AVAILABLE = False
    logger.warning("pywin32 or WMI not available. Windows-specific features may be limited.")

class WindowsAdapter(BaseAdapter):
    """
    Provides OS-specific functionalities for Windows systems.
    """
    def __init__(self):
        logger.info("WindowsAdapter initialized.")
        if not PYWIN32_WMI_AVAILABLE:
            logger.error("Required Python libraries (pywin32, wmi) for WindowsAdapter are not installed.")

    async def _run_powershell_command(self, script: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a PowerShell command."""
        logger.info(f"Executing PowerShell command: {script}")
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-Command",
                script,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW # Hide console window
            )
            stdout, stderr = await process.communicate()
            stdout_str = stdout.decode('utf-8', errors='ignore').strip()
            stderr_str = stderr.decode('utf-8', errors='ignore').strip()

            if process.returncode == 0:
                logger.info(f"PowerShell command successful: {stdout_str}")
                return True, stdout_str
            else:
                logger.error(f"PowerShell command failed with exit code {process.returncode}: {stderr_str}")
                return False, stderr_str
        except FileNotFoundError:
            logger.error("PowerShell executable not found. Ensure PowerShell is installed and in PATH.")
            return False, "PowerShell not found."
        except Exception as e:
            logger.error(f"Error running PowerShell command: {e}")
            return False, str(e)

    async def get_installed_software(self) -> List[Dict[str, str]]:
        """
        Uses WMIC to get a list of installed software on Windows.
        """
        success, output = await self._run_powershell_command("wmic product get Name,Version /format:csv")
        
        software_list = []
        if success:
            lines = output.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        name = parts[1]
                        version = parts[2]
                        if name:
                            software_list.append({"name": name, "version": version})
        return software_list

    async def get_netstat_info(self) -> List[Dict[str, Any]]:
        """Retrieves network connection information using 'netstat'."""
        success, output = await self._run_powershell_command("netstat -ano")
        
        connections = []
        if success:
            for line in output.splitlines():
                if line.strip().startswith("TCP") or line.strip().startswith("UDP"):
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            proto = parts[0]
                            local_address = parts[1]
                            foreign_address = parts[2]
                            state = parts[3] if proto == "TCP" else "N/A"
                            pid = parts[4] if len(parts) > 4 else "N/A"
                            
                            connections.append({
                                "protocol": proto,
                                "local_address": local_address,
                                "foreign_address": foreign_address,
                                "state": state,
                                "pid_program": pid
                            })
                        except IndexError:
                            logger.warning(f"Failed to parse netstat line: {line}")
        return connections

    async def get_process_list(self) -> List[Dict[str, Any]]:
        """Retrieves a list of running processes using 'tasklist'."""
        success, output = await self._run_powershell_command("tasklist /v /fo csv")
        processes = []
        if success:
            import csv
            from io import StringIO
            
            reader = csv.DictReader(StringIO(output))
            for row in reader:
                processes.append({
                    "pid": row["PID"],
                    "user": row["User Name"],
                    "command": row["Image Name"]
                })
    async def ping_host(self, target: str) -> Dict[str, Any]:
        """Pings a host and returns the results."""
        success, output = await self._run_powershell_command(f"Test-Connection -ComputerName {target} -Count 4 | ConvertTo-Json")
        if success:
            import json
            try:
                return {"status": "success", "output": json.loads(output)}
            except json.JSONDecodeError:
                return {"status": "failed", "output": output}
        return {"status": "failed", "output": output}

    async def execute_command(self, cmd: str, shell: bool = False) -> Dict[str, Any]:
        """Executes an OS command and returns its output and status."""
        # For security, always prefer shell=False where possible to avoid shell injection.
        # PowerShell handles both simple commands and scripts well.
        success, output = await self._run_powershell_command(cmd) # PowerShell executes commands
        return {
            "stdout": output if success else "",
            "stderr": output if not success else "",
            "returncode": 0 if success else 1
        }

    async def isolate_system(self, reason: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Isolates the system using Windows Firewall."""
        # This is a highly critical action and should be used with extreme caution.
        # This example blocks all inbound and outbound traffic.
        
        # Block all inbound traffic
        block_inbound_script = "New-NetFirewallRule -DisplayName 'Block All Inbound PhantomNet' -Direction Inbound -Action Block -Profile Any"
        success_inbound, _ = await self._run_powershell_command(block_inbound_script)

        # Block all outbound traffic
        block_outbound_script = "New-NetFirewallRule -DisplayName 'Block All Outbound PhantomNet' -Direction Outbound -Action Block -Profile Any"
        success_outbound, _ = await self._run_powershell_command(block_outbound_script)

        if success_inbound and success_outbound:
            return {"status": "success", "message": f"System isolated. Reason: {reason}."}
        else:
            return {"status": "failed", "message": "Failed to isolate system."}

    async def restart_windows_service(self, service_name: str) -> bool:
        """Restarts a Windows service."""
        if not PYWIN32_WMI_AVAILABLE: return False
        logger.info(f"Restarting Windows service: {service_name}")
        try:
            win32serviceutil.RestartService(service_name)
            logger.info(f"Service {service_name} restarted successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False

    async def get_windows_event_logs(self, log_name: str = "System", count: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent Windows Event Logs."""
        if not PYWIN32_WMI_AVAILABLE: return []
        logger.info(f"Getting last {count} entries from Windows Event Log: {log_name}")
        try:
            # Using WMI for event logs
            conn = wmi.WMI()
            query = f"SELECT * FROM Win32_NTLogEvent WHERE Logfile = '{log_name}' ORDER BY TimeWritten DESC"
            events = conn.query(query)
            
            log_entries = []
            for i, event in enumerate(events):
                if i >= count: break
                log_entries.append({
                    "time_generated": event.TimeGenerated,
                    "source": event.SourceName,
                    "event_id": event.EventCode,
                    "message": event.Message,
                    "type": event.Type,
                    "user": event.User,
                })
            return log_entries
        except Exception as e:
            logger.error(f"Failed to retrieve Windows Event Logs: {e}")
            return []

    async def check_windows_defender_status(self) -> Dict[str, Any]:
        """Checks the status of Windows Defender."""
        script = """
        Get-MpComputerStatus | Select-Object AntivirusEnabled, AntispywareEnabled, RealTimeProtectionEnabled, FullScanRequired, SignatureVersion, AntivirusProductVersion | ConvertTo-Json
        """
        success, output = await self._run_powershell_command(script)
        if success:
            try:
                status = json.loads(output)
                logger.info(f"Windows Defender Status: {status}")
                return status
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Defender status JSON: {output}")
                return {"error": "Failed to parse JSON output"}
        return {"error": output}

    async def repair_file_permissions(self, path: str, owner: str = "Administrators", permissions: str = "FullControl") -> bool:
        """Repairs file permissions on Windows using icacls (simplified)."""
        logger.info(f"Repairing permissions for {path} for {owner} with {permissions}.")
        # Example: Grant FullControl to Administrators group
        script = f"icacls \"{path}\" /grant \"{owner}\":\"{permissions}\""
        success, output = await self._run_powershell_command(script)
        if success:
            logger.info(f"Permissions repaired for {path}.")
            return True
        logger.error(f"Failed to repair permissions for {path}: {output}")
        return False

    async def reset_networking_components(self) -> bool:
        """Resets networking components on Windows."""
        logger.info("Resetting Windows networking components (ipconfig /release; ipconfig /renew).")
        script = """
        ipconfig /release
        ipconfig /renew
        """
        success, output = await self._run_powershell_command(script)
        if success:
            logger.info("Windows IP configuration released and renewed.")
            return True
        logger.error(f"Failed to renew Windows IP configuration: {output}")
        return False

# For direct testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running WindowsAdapter example...")
    
    adapter = WindowsAdapter()

    async def run_example():
        # Requires Administrator privileges to run most commands
        if not IS_ROOT:
            logger.warning("Most WindowsAdapter functions require Administrator privileges to run effectively.")

        # print(f"Windows Defender Status: {await adapter.check_windows_defender_status()}")
        # print(f"Last 5 System Events:\n{await adapter.get_windows_event_logs('System', 5)}")
        # print(f"Restarting BITS service: {await adapter.restart_windows_service('BITS')}")
        # print(f"Repairing permissions for C:\\temp: {await adapter.repair_file_permissions('C:\\temp')}")
        
        logger.info("WindowsAdapter example functions require administrative privileges and may interact with system services.")
        logger.info("Please run this example in an environment with necessary permissions and caution.")

    try:
        # Mock IS_ROOT for testing if not running as root
        from unittest.mock import patch
        with patch('shared.platform_utils.IS_ROOT', True): # Assume root for testing commands
            asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("WindowsAdapter example stopped.")
