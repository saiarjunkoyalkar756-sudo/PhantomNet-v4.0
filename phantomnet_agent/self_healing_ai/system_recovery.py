# phantomnet_agent/self_healing_ai/system_recovery.py

import logging
import os
import sys
import shutil
import json
import yaml # For config repair
import subprocess
import asyncio
from typing import Dict, Any, List, Tuple, Optional

from utils.logger import get_logger
from shared.platform_utils import SAFE_MODE, IS_WINDOWS, IS_LINUX, IS_TERMUX
from phantomnet_agent.core.config import load_config, AgentConfigSchema # For config validation/repair
from phantomnet_agent.platform_compatibility.os_detector import OSDetector

logger = get_logger(__name__)

class SystemRecovery:
    """
    Implements last-resort recovery actions for critical system failures.
    """
    def __init__(self, agent_dir: str = "phantomnet_agent", venv_path: str = ".venv_phantomnet", cert_dir: str = "certs"):
        self.agent_dir = agent_dir
        self.venv_path = venv_path
        self.cert_dir = cert_dir
        self.safe_mode = SAFE_MODE
        
        self.agent_config_path = os.path.join(agent_dir, "config", "agent.yml")

        self.venv_python = os.path.join(venv_path, "bin", "python") # Linux/Termux
        if IS_WINDOWS:
            self.venv_python = os.path.join(venv_path, "Scripts", "python.exe")
        
        self.os_detector = OSDetector()
        self.platform_adapter = self.os_detector.get_adapter()
        if not self.platform_adapter:
            logger.error("No platform adapter loaded for SystemRecovery. OS-specific actions will be limited.")

    async def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Helper to run a shell command."""
        logger.info(f"Executing command: {' '.join(command)}")
        try:
            result = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            if result.returncode == 0:
                logger.info(f"Command successful: {stdout_str}")
                return True, stdout_str
            else:
                logger.error(f"Command failed with exit code {result.returncode}: {stderr_str}")
                return False, stderr_str
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}")
            return False, f"Command not found: {command[0]}"
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return False, str(e)

    async def rebuild_virtual_environment(self) -> bool:
        """Removes and recreates the Python virtual environment."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping virtual environment rebuild.")
            return False

        logger.info(f"Attempting to rebuild virtual environment at {self.venv_path}")
        try:
            if os.path.exists(self.venv_path):
                logger.info(f"Removing existing virtual environment: {self.venv_path}")
                shutil.rmtree(self.venv_path)
            
            # Recreate venv
            success, _ = await self._run_command([sys.executable, "-m", "venv", self.venv_path])
            if not success:
                return False

            # Reinstall core dependencies (using base requirements)
            if IS_WINDOWS:
                requirements_file = "requirements-windows.txt"
            elif IS_LINUX:
                requirements_file = "requirements-linux.txt"
            elif IS_TERMUX:
                requirements_file = "requirements-termux.txt" # Simplified requirements
            else:
                requirements_file = "requirements.txt" # Fallback

            logger.info(f"Installing core dependencies from {requirements_file}...")
            success, _ = await self._run_command([self.venv_python, "-m", "pip", "install", "-r", requirements_file])
            
            if success:
                logger.info("Virtual environment rebuilt and dependencies reinstalled successfully.")
                return True
            else:
                logger.error("Failed to reinstall dependencies after rebuilding virtual environment.")
                return False
        except Exception as e:
            logger.error(f"Error rebuilding virtual environment: {e}")
            return False

    async def rebuild_agent_certificates(self) -> bool:
        """Removes existing agent certificates and signals for re-registration."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping agent certificate rebuild.")
            return False

        logger.info(f"Attempting to rebuild agent certificates in {self.cert_dir}")
        try:
            if os.path.exists(self.cert_dir):
                shutil.rmtree(self.cert_dir)
                os.makedirs(self.cert_dir) # Recreate empty directory
            logger.info("Agent certificates removed. Agent will attempt re-registration on next start.")
            return True
        except Exception as e:
            logger.error(f"Error rebuilding agent certificates: {e}")
            return False

    async def reset_networking_components(self) -> bool:
        """
        Resets networking components (e.g., restarts network services, clears caches).
        This is OS-specific and highly privileged, delegated to the platform adapter.
        """
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping network component reset.")
            return False
        if not self.platform_adapter:
            logger.error("No platform adapter available for network reset.")
            return False

        logger.info("Attempting to reset networking components (OS-specific and privileged).")
        return await self.platform_adapter.reset_networking_components()

    async def repair_configuration_file(self) -> bool:
        """Attempts to repair the agent's main configuration file (agent.yml)."""
        if self.safe_mode:
            logger.warning(f"SAFE_MODE: Skipping configuration file repair.")
            return False

        logger.info(f"Attempting to repair configuration file: {self.agent_config_path}")
        try:
            # Attempt to load and re-save using Pydantic model for validation/normalization
            config = load_config(self.agent_config_path) # Uses AgentConfigSchema internally
            if config:
                # If loaded, rewrite to normalize format
                with open(self.agent_config_path, 'w') as f:
                    yaml.dump(config.model_dump(exclude_unset=True), f) # Save back
                logger.info(f"Configuration file {self.agent_config_path} repaired/normalized.")
                return True
            else:
                logger.error("Failed to load/validate current configuration for repair.")
                return False
        except Exception as e:
            logger.error(f"Error repairing configuration file {self.agent_config_path}: {e}")
            return False

    async def restore_health_heartbeat(self) -> bool:
        """Conceptual: Ensures the agent's health heartbeat is functioning."""
        logger.info("Attempting to restore health heartbeat (e.g., re-initialize health monitor).")
        # In practice, this would involve signaling the health monitor component
        # to restart its loop or re-establish connection to the backend.
        # For this conceptual implementation, we just log.
        return True # Simulate success

    async def recover(self, recovery_plan: List[str]) -> Tuple[bool, str]:
        """
        Executes a sequence of recovery actions.
        """
        logger.info(f"Initiating system recovery with plan: {recovery_plan}")
        full_success = True
        recovery_log_entries = []

        for action in recovery_plan:
            success = False
            message = ""
            if action == "rebuild_venv":
                success, message = await self.rebuild_virtual_environment(), "Virtual environment rebuild"
            elif action == "rebuild_certs":
                success, message = await self.rebuild_agent_certificates(), "Agent certificates rebuild"
            elif action == "reset_network":
                success, message = await self.reset_networking_components(), "Networking components reset"
            elif action == "repair_config":
                success, message = await self.repair_configuration_file(), "Configuration file repair"
            elif action == "restore_heartbeat":
                success, message = await self.restore_health_heartbeat(), "Health heartbeat restore"
            elif action == "start_safe_mode":
                logger.warning("Recovery plan includes starting in SAFE_MODE. Agent needs to be restarted.")
                recovery_log_entries.append("Agent signaled for restart in SAFE_MODE.")
                success, message = True, "Signal for SAFE_MODE restart"
            else:
                message = f"Unknown recovery action: {action}"
                success = False
            
            recovery_log_entries.append(f"{message}: {'SUCCESS' if success else 'FAILED'}")
            if not success:
                full_success = False
                logger.error(f"Recovery action '{action}' failed.")
            
            await asyncio.sleep(1) # Small delay between actions

        final_status = "SUCCESS" if full_success else "FAILED"
        logger.info(f"System recovery plan executed with status: {final_status}")
        return full_success, "\n".join(recovery_log_entries)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running SystemRecovery example...")
    
    # Create dummy agent config for testing config repair
    os.makedirs("phantomnet_agent/config", exist_ok=True)
    with open("phantomnet_agent/config/agent.yml", "w") as f:
        f.write("invalid yaml content: -")

    # Mock agent_state.config for load_config
    class MockAgentConfig:
        def __init__(self):
            self.agent = self
        def model_dump(self, exclude_unset=True):
            return {"test_key": "test_value"}
    
    from unittest.mock import patch, MagicMock
    with patch('core.config.load_config', return_value=MockAgentConfig()), 
         patch('core.config.AgentConfigSchema', MagicMock()): # Mock the schema as well

        recovery_manager = SystemRecovery()

        async def run_example():
            # Test rebuild venv
            success, log = await recovery_manager.recover(["rebuild_venv"])
            print(f"\nRebuild Venv - Success: {success}, Log:\n{log}")

            # Test repair config
            success, log = await recovery_manager.recover(["repair_config"])
            print(f"\nRepair Config - Success: {success}, Log:\n{log}")

            # Test rebuild certs
            success, log = await recovery_manager.recover(["rebuild_certs"])
            print(f"\nRebuild Certs - Success: {success}, Log:\n{log}")

            # Test full recovery plan
            full_plan = ["rebuild_venv", "rebuild_certs", "reset_network", "repair_config", "restore_heartbeat"]
            success, log = await recovery_manager.recover(full_plan)
            print(f"\nFull Recovery Plan - Success: {success}, Log:\n{log}")

        try:
            asyncio.run(run_example())
        except KeyboardInterrupt:
            logger.info("SystemRecovery example stopped.")
        
        # Cleanup dummy config
        shutil.rmtree("phantomnet_agent/config", ignore_errors=True)
