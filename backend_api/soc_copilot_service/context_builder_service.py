# backend_api/soc_copilot_service/context_builder.py

import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
import os
from datetime import datetime, timedelta
import json

from shared.logger_config import logger

logger = logger

# --- Configuration for other services (conceptual URLs) ---
SIEM_SERVICE_URL = os.getenv("SIEM_SERVICE_URL", "http://localhost:8000/siem")
THREAT_INTEL_SERVICE_URL = os.getenv("THREAT_INTEL_SERVICE_URL", "http://localhost:8000/threat-intel")
ASSET_INVENTORY_SERVICE_URL = os.getenv("ASSET_INVENTORY_SERVICE_URL", "http://localhost:8000/asset-inventory")
SOAR_SERVICE_URL = os.getenv("SOAR_SERVICE_URL", "http://localhost:8000/soar")

class ContextBuilder:
    """
    Gathers and aggregates relevant context from various PhantomNet services
    to provide a comprehensive view for the AI Copilot.
    """
    def __init__(self):
        self.httpx_client = httpx.AsyncClient()
        logger.info("ContextBuilder initialized.")

    async def _fetch_from_siem(self, query: str, time_range_start: Optional[datetime] = None, time_range_end: Optional[datetime] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Conceptual: Fetches log data from SIEM service."""
        try:
            response = await self.httpx_client.post(
                f"{SIEM_SERVICE_URL}/query",
                json={
                    "query_string": query,
                    "time_range_start": time_range_start.isoformat() if time_range_start else None,
                    "time_range_end": time_range_end.isoformat() if time_range_end else None,
                    "limit": limit
                }
            )
            response.raise_for_status()
            return response.json().get("logs", [])
        except httpx.RequestError as e:
            logger.error(f"Error fetching from SIEM service: {e}")
            return []

    async def _fetch_from_threat_intel(self, indicator_value: str, indicator_type: str) -> Optional[Dict[str, Any]]:
        """Conceptual: Fetches threat intelligence for an indicator."""
        try:
            response = await self.httpx_client.post(
                f"{THREAT_INTEL_SERVICE_URL}/lookup",
                json={"value": indicator_value, "type": indicator_type}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error fetching from Threat Intel service: {e}")
            return None

    async def _fetch_from_asset_inventory(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Conceptual: Fetches asset details from Asset Inventory service."""
        try:
            response = await self.httpx_client.get(f"{ASSET_INVENTORY_SERVICE_URL}/assets/{asset_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error fetching from Asset Inventory service: {e}")
            return None

    async def _fetch_soar_playbook_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Conceptual: Fetches SOAR playbook run status."""
        try:
            response = await self.httpx_client.get(f"{SOAR_SERVICE_URL}/playbook_runs/{run_id}")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error fetching SOAR playbook run status: {e}")
            return None

    async def build_context_for_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds a comprehensive context for an alert by querying various services.
        """
        context: Dict[str, Any] = {"alert": alert_data}
        
        # Extract potential indicators from alert
        source_ip = alert_data.get("source_ip")
        destination_ip = alert_data.get("destination_ip")
        domain = alert_data.get("domain")
        
        ti_tasks = []
        if source_ip:
            ti_tasks.append(self._fetch_from_threat_intel(source_ip, "ip"))
        if destination_ip and destination_ip != source_ip: # Avoid duplicate lookup
            ti_tasks.append(self._fetch_from_threat_intel(destination_ip, "ip"))
        if domain:
            ti_tasks.append(self._fetch_from_threat_intel(domain, "domain"))
        
        if ti_tasks:
            ti_results = await asyncio.gather(*ti_tasks, return_exceptions=True)
            context["threat_intelligence"] = [r for r in ti_results if not isinstance(r, Exception) and r is not None]

        # Fetch SIEM logs related to the alert's source IP or host
        siem_query_parts = []
        if source_ip:
            siem_query_parts.append(f"source_ip='{source_ip}'")
        if alert_data.get("host_id"):
            siem_query_parts.append(f"host_id='{alert_data['host_id']}'")
        
        if siem_query_parts:
            siem_query_string = " OR ".join(siem_query_parts)
            siem_logs = await self._fetch_from_siem(
                siem_query_string,
                time_range_start=datetime.utcnow() - timedelta(hours=1),
                limit=20
            )
            context["siem_logs"] = siem_logs

        # Fetch asset details if host_id is available
        if alert_data.get("host_id"):
            asset_details = await self._fetch_from_asset_inventory(alert_data["host_id"])
            if asset_details:
                context["asset_details"] = asset_details

        return context

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running ContextBuilder example...")
    
    # Needs mock FastAPI apps for SIEM, Threat Intel, Asset Inventory to run.
    # For this example, we'll mock the httpx client calls.
    from unittest.mock import patch, AsyncMock
    
    async def mock_siem_query_logs(query, time_range_start, limit):
        logger.info(f"Mock SIEM query: {query}")
        return [{"message": "Mock SIEM log entry", "event_type": "process.create"}]
    
    async def mock_threat_intel_lookup(indicator_value, indicator_type):
        logger.info(f"Mock TI lookup: {indicator_value} ({indicator_type})")
        return {"indicator": {"value": indicator_value, "type": indicator_type}, "reputation_score": 70}
        
    async def mock_asset_fetch(asset_id):
        logger.info(f"Mock Asset fetch: {asset_id}")
        return {"asset_id": asset_id, "os": "Linux", "criticality": 90}

    async def mock_soar_run_status(run_id):
        logger.info(f"Mock SOAR run status: {run_id}")
        return {"run_id": run_id, "status": "completed"}

    async def run_example():
        builder = ContextBuilder()
        
        mock_alert = {
            "alert_id": "ALERT-007",
            "title": "Suspicious Outbound Connection",
            "description": "Connection to known C2 server observed.",
            "source_ip": "192.168.1.100",
            "destination_ip": "1.1.1.1",
            "domain": "malicious.com",
            "host_id": "server-critical-01",
            "timestamp": datetime.utcnow().isoformat()
        }

        with patch('backend_api.soc_copilot_service.context_builder_service.ContextBuilder._fetch_from_siem', AsyncMock(side_effect=mock_siem_query_logs)), \
             patch('backend_api.soc_copilot_service.context_builder_service.ContextBuilder._fetch_from_threat_intel', AsyncMock(side_effect=mock_threat_intel_lookup)), \
             patch('backend_api.soc_copilot_service.context_builder_service.ContextBuilder._fetch_from_asset_inventory', AsyncMock(side_effect=mock_asset_fetch)), \
             patch('backend_api.soc_copilot_service.context_builder_service.ContextBuilder._fetch_soar_playbook_run_status', AsyncMock(side_effect=mock_soar_run_status)):
            
            full_context = await builder.build_context_for_alert(mock_alert)
            logger.info(f"\nFull Context for Alert:\n{json.dumps(full_context, indent=2)}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("ContextBuilder example stopped.")
