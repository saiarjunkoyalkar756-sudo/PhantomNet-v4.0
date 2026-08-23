from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from backend_api.core.logging import logger as pn_logger
from backend_api.core.response import error_response


router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])

class ThreatData(BaseModel):
    threat_string: str

@router.post("/threats")
async def analyze_threat_endpoint(threat_data: ThreatData):
    """
    Endpoint to analyze threat data using the Cognitive Core.
    """
    pn_logger.warning("Orchestrator threat analysis is currently disabled.")
    return error_response(code="DISABLED", message="Orchestrator threat analysis is currently disabled.", status_code=501)

def _retired_legacy_blockchain_api():
    return error_response(
        code="LEGACY_GATEWAY_BLOCKCHAIN_API_RETIRED",
        message=(
            "The legacy gateway blockchain disclosure and verification surface is retired. "
            "Use a governed, tenant-scoped audit-evidence control plane."
        ),
        status_code=410,
    )


@router.get("/blockchain", include_in_schema=False)
async def get_blockchain_data():
    """Fail closed instead of disclosing globally scoped conceptual chain records."""
    return _retired_legacy_blockchain_api()


@router.post("/blockchain/verify", include_in_schema=False)
async def verify_blockchain_integrity():
    """Fail closed instead of reporting conceptual chain-link verification as audit proof."""
    return _retired_legacy_blockchain_api()

def _retired_legacy_orchestrator_mutation():
    return error_response(
        code="LEGACY_GATEWAY_ORCHESTRATOR_MUTATION_RETIRED",
        message=(
            "This legacy gateway orchestrator mutation route is retired. Use governed, "
            "tenant-scoped workflows with required approval and auditable evidence."
        ),
        status_code=410,
    )


@router.api_route(
    "/blockchain/add_transaction",
    methods=["POST"],
    include_in_schema=False,
)
async def retired_blockchain_transaction_mutation():
    """Fail closed instead of mining caller-supplied transactions through the gateway."""
    return _retired_legacy_orchestrator_mutation()


@router.api_route(
    "/honeypot/control",
    methods=["POST"],
    include_in_schema=False,
)
async def retired_honeypot_control_mutation():
    """Fail closed instead of exposing gateway-controlled honeypot lifecycle actions."""
    return _retired_legacy_orchestrator_mutation()


@router.api_route(
    "/honeypot/simulate_attack",
    methods=["POST"],
    include_in_schema=False,
)
async def retired_honeypot_attack_simulation_mutation():
    """Fail closed instead of forwarding caller-defined simulated attacks to ingestion."""
    return _retired_legacy_orchestrator_mutation()
