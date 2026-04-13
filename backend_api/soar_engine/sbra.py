# backend_api/soar_engine/sbra.py
import logging
from typing import Dict, Any, List, Tuple
import httpx
import os

from backend_api.shared.resilience import CircuitBreaker

# Configure logger
logger = logging.getLogger(__name__)

# Get the Asset Inventory Service URL from environment variables, with a default for local dev
ASSET_INVENTORY_URL = os.environ.get(
    "ASSET_INVENTORY_URL", "http://localhost:8008"
)


class SimulationBlastRadiusAnalyzer:
    """
    Simulates playbook actions and calculates the potential business impact.
    Uses a circuit breaker to handle failures of the asset inventory service.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=ASSET_INVENTORY_URL, timeout=5.0)
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        logger.info("Simulation & Blast Radius Analyzer (SBRA) initialized with Circuit Breaker.")

    async def _get_dependents_from_api(self, asset_id: str) -> List[Dict[str, Any]]:
        """
        Internal method to query the Asset Inventory Service.
        This is the method that will be wrapped by the circuit breaker.
        """
        response = await self.client.get(f"/assets/{asset_id}/dependents")
        response.raise_for_status()  # Will raise an exception for 4xx/5xx responses
        data = response.json()
        return data.get("dependents", [])

    async def _get_dependents(self, asset_id: str) -> List[Dict[str, Any]]:
        """
        Safely queries the Asset Inventory Service using a circuit breaker.
        """
        try:
            # Wrap the API call with the circuit breaker
            dependents = await self.circuit_breaker.call(
                self._get_dependents_from_api, asset_id
            )
            return dependents
        except ConnectionError as e:
            # This is raised by the circuit breaker when it's OPEN
            logger.error(
                f"Circuit breaker is open for Asset Inventory Service. Returning empty blast radius. Error: {e}"
            )
            return []
        except httpx.RequestError as e:
            # This is a network error during the request
            logger.error(
                f"Could not connect to Asset Inventory Service at {ASSET_INVENTORY_URL}. Error: {e}"
            )
            # This failure is recorded by the circuit breaker via the .call method's exception handling
            return []
        except httpx.HTTPStatusError as e:
            # The service responded with an error (e.g., 404, 500)
            logger.error(
                f"Asset Inventory Service returned an error for asset '{asset_id}': {e.response.status_code}"
            )
            # We don't trip the breaker for client/server errors unless they are persistent,
            # but the .call method will record a failure, contributing to the threshold.
            return []

    async def calculate_impact(
        self, target_asset_id: str, action: str
    ) -> Tuple[int, List[str]]:
        """
        Calculates the business impact score and blast radius for a given action on a target asset.
        """
        if action not in ["isolate_host", "shutdown_service", "block_ip"]:
            return 1, []

        logger.info(
            f"Calculating blast radius for action '{action}' on asset '{target_asset_id}'"
        )
        dependents = await self._get_dependents(target_asset_id)

        if not dependents:
            logger.info(f"No dependent assets found for '{target_asset_id}'. Impact is low.")
            return 2, [f"Impact limited to the target asset: {target_asset_id}"]

        total_criticality = sum(asset.get("criticality", 1) for asset in dependents)
        blast_radius_details = [
            f"Service '{asset.get('asset_id')}' (Criticality: {asset.get('criticality')}) would be affected."
            for asset in dependents
        ]

        business_impact_score = total_criticality / len(dependents)
        final_score = int(min(10, max(1, business_impact_score)))
        
        logger.info(
            f"Calculated Business Impact Score: {final_score}/10 for action on '{target_asset_id}'"
        )

        return final_score, blast_radius_details

# ... (Example usage main function remains the same)
