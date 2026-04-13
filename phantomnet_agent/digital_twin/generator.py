import uuid
import datetime
import yaml
import jinja2
import logging
from typing import Dict, Any, List

from .models import TwinTemplate, TwinInstance, ForensicEvidenceMetadata
from backend_api.evidence_vault.evidence_vault import EvidenceVault # Import the EvidenceVault
from utils.logger import get_logger # Use the structured logger

class TwinGenerator:
    """
    Generates digital twin instances from templates, optionally linking them
    to forensic evidence.
    """
    def __init__(self, evidence_vault: EvidenceVault):
        self.logger = get_logger("phantomnet_agent.digital_twin.generator")
        self.evidence_vault = evidence_vault
        self.logger.info("TwinGenerator initialized.")

    async def render_template(self, template: TwinTemplate, params: dict) -> TwinInstance:
        inst_id = f"twin-{uuid.uuid4().hex[:8]}"
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        # render service files using Jinja2 for placeholders
        compose = {"version": "3.8", "services": {}}
        for svc in template.services:
            name = svc.name
            service_def = {
                "image": svc.image or "alpine:latest",
                "environment": svc.env,
                "ports": svc.ports,
            }
            # add volumes for files; create local bind-mounts with generated content
            compose["services"][name] = service_def
        docker_compose_yaml = yaml.dump(compose)
        instance = TwinInstance(
            instance_id=inst_id,
            template_id=template.template_id,
            created_at=ts,
            params=params,
            docker_compose_yaml=docker_compose_yaml,
        )
        self.logger.info(f"Generated Digital Twin instance {inst_id} from template {template.template_id}.")

        # Conceptually store the generated Docker Compose YAML as evidence
        try:
            evidence_id = await self.evidence_vault.store_evidence(
                data=docker_compose_yaml,
                source="digital_twin_generation",
                tags=["digital_twin", "configuration", "yaml"],
                filename=f"{inst_id}_docker-compose.yaml"
            )
            self.logger.debug(f"Stored generated Docker Compose YAML as evidence: {evidence_id}")
            # Optionally link this evidence to the TwinInstance or its metadata
        except Exception as e:
            self.logger.error(f"Failed to store Docker Compose YAML as evidence for twin {inst_id}: {e}", exc_info=True)

        return instance