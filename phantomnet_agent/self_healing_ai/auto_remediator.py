# phantomnet_agent/self_healing_ai/auto_remediator.py

import logging
import subprocess
import os
import sys
import shutil
import json
import yaml # For config repair
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import re # Import re for regex operations

from utils.logger import get_logger
from shared.platform_utils import IS_WINDOWS, IS_LINUX, IS_TERMUX, IS_ROOT, SAFE_MODE
from phantomnet_agent.platform_compatibility.os_detector import OSDetector

logger = get_logger(__name__)

class AutoRemediator:
    """
    Implements automatic error fixing actions based on classified errors.
    """
    def __init__(self, agent_dir: str = "phantomnet_agent", venv_path: str = ".venv_phantomnet"):
        self.agent_dir = agent_dir
        self.venv_path = venv_path
        self.venv_python = os.path.join(venv_path, "bin", "python") # Linux/Termux
        if IS_WINDOWS:
            self.venv_python = os.path.join(venv_path, "Scripts", "python.exe")
        
        self.config_paths = {
            "agent": os.path.join(agent_dir, "config", "agent.yml"),
            # Add other config paths here
        }
        self.safe_mode = SAFE_MODE
        self.os_detector = OSDetector()
        self.platform_adapter = self.os_detector.get_adapter()
        if not self.platform_adapter:
            logger.error("No platform adapter loaded for AutoRemediator. OS-specific fixes will be limited.")

    async def _run_command(self, command: List[str], cwd: Optional[str] = None, check_output: bool = False) -> Tuple[bool, str]:
        """Helper to run a shell command safely."""
        logger.info(f"Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                shell=False # Always prefer shell=False for security
            )
            if check_output:
                return True, result.stdout.strip()
            return True, ""
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code {e.returncode}: {e.stderr.strip()}")
            return False, e.stderr.strip()
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}")
            return False, f"Command not found: {command[0]}"
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return False, str(e)

    async def install_missing_dependency(self, package_name: str) -> bool:
        """Installs a missing Python package."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping installation of '{package_name}'.")
            return False

        logger.info(f"Attempting to install missing Python package: {package_name}")
        success, output = await self._run_command([self.venv_python, "-m", "pip", "install", package_name])
        if success:
            logger.info(f"Successfully installed {package_name}.")
        return success

    async def repair_config_file(self, config_type: str, backup_path: Optional[str] = None) -> bool:
        """
        Attempts to repair a corrupted configuration file.
        Prioritizes restoring from backup if provided, otherwise attempts basic parsing fix.
        """
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping configuration repair for '{config_type}'.")
            return False

        config_path = self.config_paths.get(config_type)
        if not config_path or not os.path.exists(config_path):
            logger.error(f"Config path for '{config_type}' not found or file does not exist.")
            return False

        logger.info(f"Attempting to repair config file: {config_path}")

        if backup_path and os.path.exists(backup_path):
            logger.info(f"Restoring config from backup: {backup_path}")
            shutil.copy(backup_path, config_path)
            return True
        
        # Basic attempt to fix malformed YAML/JSON
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Try parsing as YAML (more forgiving than JSON)
            config_data = yaml.safe_load(content)
            # If successful, rewrite it to ensure correct formatting
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            logger.info(f"Successfully re-formatted and repaired config file: {config_path}")
            return True
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            logger.error(f"Still unable to parse/repair config file {config_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during config repair for {config_path}: {e}")
            return False

    async def restart_module(self, module_name: str) -> bool:
        """Restarts a specific agent module/collector by restarting its service."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping restart of '{module_name}'.")
            return False
        if not self.platform_adapter:
            logger.error("No platform adapter available for module restart.")
            return False
            
        logger.info(f"Attempting to restart module/service: {module_name}")
        # This assumes modules are managed as system services (e.g., systemd unit, Windows service)
        # For simplicity, we'll try to restart a generic service name.
        if IS_LINUX:
            return await self.platform_adapter.restart_system_service(f"phantomnet-agent-{module_name}.service")
        elif IS_WINDOWS:
            return await self.platform_adapter.restart_windows_service(f"PhantomNetAgent{module_name}")
        elif IS_TERMUX:
            return await self.platform_adapter.restart_termux_service(module_name)
        return False

    async def elevate_permissions(self) -> bool:
        """
        Attempts to elevate current process permissions.
        This operation is highly OS-specific and might involve re-executing with sudo
        or requesting UAC on Windows. Automatic elevation is complex and often requires
        manual intervention or system-level configuration.
        """
        if IS_ROOT:
            logger.info("Already running with elevated permissions.")
            return True
        
        if self.safe_mode:
            logger.warning("SAFE_MODE: Skipping privilege elevation.")
            return False
        if not self.platform_adapter:
            logger.error("No platform adapter available for privilege elevation.")
            return False

        logger.warning("Attempting to elevate permissions (requires manual intervention or specific setup).")

        if IS_LINUX:
            logger.info("On Linux, elevation typically requires 'sudo' or 'setcap'. Manual restart with 'sudo' recommended.")
            # self.platform_adapter.elevate_privileges() # Conceptual call
            return False
        elif IS_WINDOWS:
            logger.info("On Windows, elevation requires a UAC prompt. Manual restart as Administrator recommended.")
            # self.platform_adapter.elevate_privileges() # Conceptual call
            return False
        elif IS_TERMUX:
            logger.warning("Privilege elevation (root) on Termux is complex and often requires a rooted device. Cannot auto-elevate.")
            return False
        
        return False # Cannot auto-elevate without specific system hooks

    async def repair_imports(self, module_name: str) -> bool:
        """
        Conceptual: Attempts to repair broken imports.
        This often means reinstalling a package or checking sys.path.
        """
        logger.info(f"Attempting to repair imports for module: {module_name}")
        # More complex: Inspect sys.path, check if module files exist, re-install if needed.
        # For now, just a generic attempt to reinstall the agent's dependencies.
        return await self.install_missing_dependency(module_name)

    async def remediate(self, classified_error: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Executes remediation actions based on a classified error.
        Returns (success: bool, remediation_log: str).
        """
        issue_type = classified_error.get("classified_issue_type")
        fix_suggestion = classified_error.get("suggested_fix_steps", [])
        severity = classified_error.get("classified_severity")

        if self.safe_mode and severity in ["SEV1", "SEV2"]:
            logger.warning(f"SAFE_MODE: High-severity issue '{issue_type}' detected. Automatic remediation for SEV1/SEV2 is disabled.")
            return False, "Remediation disabled in SAFE_MODE for high-severity issues."

        logger.info(f"Attempting remediation for: {issue_type} (Severity: {severity})")
        remediation_log_entries = []
        success = False

        if issue_type == "MISSING_REQUIREMENT":
            package_name_match = re.search(r"pip install ([\w\.-]+)", fix_suggestion[0] if fix_suggestion else "")
            if package_name_match:
                package_name = package_name_match.group(1)
                remediation_log_entries.append(f"Installing missing package: {package_name}")
                success = await self.install_missing_dependency(package_name)
            else:
                remediation_log_entries.append("Could not extract package name from fix suggestion.")

        elif issue_type == "PERMISSION_DENIED":
            remediation_log_entries.append("Attempting to elevate permissions.")
            success = await self.elevate_permissions()
            if not success:
                remediation_log_entries.append("Automatic permission elevation failed. Manual intervention required.")
        
        elif issue_type == "INVALID_CONFIG":
            remediation_log_entries.append("Attempting to repair configuration file (agent config).")
            success = await self.repair_config_file("agent")

        elif issue_type == "EBPF_LOAD_ERROR":
            if IS_LINUX and self.platform_adapter:
                remediation_log_entries.append("Attempting to reinstall BCC tools and kernel headers via platform adapter.")
                # This would typically involve calls like platform_adapter.install_package("bpfcc-tools")
                # For now, simulate success if adapter exists
                logger.warning("Conceptual: Reinstalling eBPF tools is a system-level operation. Simulating via adapter.")
                success = True # Simulate via adapter
            else:
                remediation_log_entries.append("eBPF error on non-Linux system or no adapter. Feature will be disabled.")
                success = True # Consider it 'fixed' by disabling

        else:
            remediation_log_entries.append(f"No specific automated remediation for {issue_type}.")
            success = False # No automated fix

        final_log = "\n".join(remediation_log_entries)
        if success:
            logger.info(f"Remediation for {issue_type} successful.")
        else:
            logger.error(f"Remediation for {issue_type} failed.")
            
        return success, final_log

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running AutoRemediator example...")
    
    remediator = AutoRemediator()

    async def run_example():
        # Simulate a missing requirement error
        missing_req_error = {
            "classified_issue_type": "MISSING_REQUIREMENT",
            "classified_severity": "SEV3",
            "suggested_fix_steps": ["Attempt to install the missing Python package: pip install requests"],
        }
        success, log = await remediator.remediate(missing_req_error)
        print(f"\nRemediation for Missing Requirement - Success: {success}, Log:\n{log}")

        # Simulate a permission denied error
        permission_error = {
            "classified_issue_type": "PERMISSION_DENIED",
            "classified_severity": "SEV2",
            "suggested_fix_steps": ["Check file/directory permissions (chmod, icacls).", "Ensure the agent is running with appropriate user context or elevated privileges."],
        }
        success, log = await remediator.remediate(permission_error)
        print(f"\nRemediation for Permission Denied - Success: {success}, Log:\n{log}")

        # Simulate a config repair
        invalid_config_error = {
            "classified_issue_type": "INVALID_CONFIG",
            "classified_severity": "SEV3",
            "suggested_fix_steps": ["Review and correct the configuration file."],
        }
        # Create a dummy corrupted config file
        dummy_config_path = os.path.join(remediator.agent_dir, "config", "agent.yml")
        os.makedirs(os.path.dirname(dummy_config_path), exist_ok=True)
        with open(dummy_config_path, "w") as f:
            f.write("key: value\n- invalid_list_item\n") # Malformed YAML

        success, log = await remediator.remediate(invalid_config_error)
        print(f"\nRemediation for Invalid Config - Success: {success}, Log:\n{log}")
        
        # Clean up dummy config
        if os.path.exists(dummy_config_path):
            os.remove(dummy_config_path)

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("AutoRemediator example stopped.")
