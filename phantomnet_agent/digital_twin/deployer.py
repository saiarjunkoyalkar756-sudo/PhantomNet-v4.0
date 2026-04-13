import logging
import asyncio # For async operations in store_evidence
import tempfile
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any

from .models import TwinInstance
from evidence_vault import EvidenceVault # Import the EvidenceVault
from utils.logger import get_logger # Use the structured logger

class TwinDeployer:
    """
    Deploys and manages digital twin instances, optionally linking deployment
    artifacts to the forensic evidence vault.
    """
    def __init__(self, evidence_vault: EvidenceVault):
        self.logger = get_logger("phantomnet_agent.digital_twin.deployer")
        self.evidence_vault = evidence_vault
        self.logger.info("TwinDeployer initialized.")

    async def deploy_instance(self, instance: TwinInstance, workdir_base: Path = Path("/var/lib/phantomnet/instances")) -> str:
        """
        Deploys a digital twin instance by writing its docker-compose.yaml
        and (conceptually) running `docker-compose up -d`.
        Deployment artifacts are stored as evidence.
        """
        wd = workdir_base / instance.instance_id
        os.makedirs(wd, exist_ok=True)
        path = wd / "docker-compose.yml"

        try:
            # Store docker-compose.yml as evidence
            compose_evidence_id = await self.evidence_vault.store_evidence(
                data=instance.docker_compose_yaml.encode('utf-8'),
                source="twin_deployment",
                tags=["digital_twin", "docker-compose", "configuration"],
                filename=f"{instance.instance_id}_docker-compose.yml"
            )
            self.logger.debug(f"Stored docker-compose.yml for twin {instance.instance_id} as evidence: {compose_evidence_id}")

            await asyncio.to_thread(lambda: path.write_text(instance.docker_compose_yaml))
            self.logger.info(f"Docker Compose YAML written to {path} for twin {instance.instance_id}.")

            # Run docker-compose (conceptually)
            if os.getenv("DEPLOY_ALLOW") == "true":
                self.logger.info(f"Executing docker compose up -d for twin {instance.instance_id} in {wd}")
                process = await asyncio.create_subprocess_exec(
                    "docker", "compose", "up", "-d",
                    cwd=str(wd),
                    stdout=asyncio.PIPE,
                    stderr=asyncio.PIPE
                )
                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode().strip()
                stderr_str = stderr.decode().strip()

                if process.returncode == 0:
                    self.logger.info(f"Digital Twin {instance.instance_id} deployed successfully.", extra={"stdout": stdout_str})
                    # Store deployment log as evidence
                    await self.evidence_vault.store_evidence(
                        data=stdout_str,
                        source="twin_deployment_log",
                        tags=["digital_twin", "deployment", "log"],
                        filename=f"{instance.instance_id}_deployment_stdout.log"
                    )
                else:
                    self.logger.error(f"Failed to deploy Digital Twin {instance.instance_id}: {stderr_str}", extra={"stderr": stderr_str})
                    await self.evidence_vault.store_evidence(
                        data=stderr_str,
                        source="twin_deployment_error",
                        tags=["digital_twin", "deployment", "error"],
                        filename=f"{instance.instance_id}_deployment_stderr.log"
                    )
                    raise Exception(f"Docker Compose failed: {stderr_str}")
            else:
                self.logger.info(f"Dry-run mode: docker-compose command not executed for twin {instance.instance_id}.")
            
            return str(wd) # Return working directory path
        except Exception as e:
            self.logger.error(f"Error deploying Digital Twin {instance.instance_id}: {e}", exc_info=True)
            raise

    async def destroy_instance(self, instance_id: str, workdir_base: Path = Path("/var/lib/phantomnet/instances")) -> bool:
        """
        Destroys a digital twin instance.
        """
        wd = workdir_base / instance_id
        if not wd.is_dir():
            self.logger.warning(f"Working directory for twin {instance_id} not found: {wd}")
            return False

        try:
            if os.getenv("DEPLOY_ALLOW") == "true":
                self.logger.info(f"Executing docker compose down for twin {instance_id} in {wd}")
                process = await asyncio.create_subprocess_exec(
                    "docker", "compose", "down",
                    cwd=str(wd),
                    stdout=asyncio.PIPE,
                    stderr=asyncio.PIPE
                )
                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode().strip()
                stderr_str = stderr.decode().strip()

                if process.returncode == 0:
                    self.logger.info(f"Digital Twin {instance_id} destroyed successfully.", extra={"stdout": stdout_str})
                    shutil.rmtree(wd) # Clean up working directory
                    self.logger.info(f"Cleaned up working directory {wd} for twin {instance_id}.")
                    return True
                else:
                    self.logger.error(f"Failed to destroy Digital Twin {instance_id}: {stderr_str}", extra={"stderr": stderr_str})
                    raise Exception(f"Docker Compose down failed: {stderr_str}")
            else:
                self.logger.info(f"Dry-run mode: docker-compose down command not executed for twin {instance_id}.")
                shutil.rmtree(wd) # Still clean up workdir in dry-run if it exists
                self.logger.info(f"Dry-run: Cleaned up working directory {wd} for twin {instance_id}.")
                return True
        except Exception as e:
            self.logger.error(f"Error destroying Digital Twin {instance_id}: {e}", exc_info=True)
            raise