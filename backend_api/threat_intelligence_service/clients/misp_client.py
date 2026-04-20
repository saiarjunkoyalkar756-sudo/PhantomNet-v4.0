import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("misp_client")

class MISPClient:
    """
    MISP (Malware Information Sharing Platform) API Client.
    Integrates with MISP instances to fetch threat indicators, attributes, and events.
    """

    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or os.getenv("MISP_URL", "https://misp.phantomnet.local")
        self.api_key = api_key or os.getenv("MISP_API_KEY", "")
        self.headers = {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        logger.info(f"MISP Client initialized for {self.api_url}")

    async def search_indicator(self, value: str) -> Optional[Dict[str, Any]]:
        """
        Searches for a specific indicator across all MISP events.
        """
        if not self.api_key:
            logger.warning("MISP API Key missing. Skipping real-time lookup.")
            return None

        endpoint = f"{self.api_url}/attributes/restSearch"
        payload = {
            "value": value,
            "limit": 10,
            "includeContext": True
        }

        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    attributes = data.get("Attribute", [])
                    if attributes:
                        logger.info(f"MISP match found for {value}: {len(attributes)} attributes.")
                        return data
                    return None
                else:
                    logger.error(f"MISP Search Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"MISP Connection Failure: {e}")
            return None

import os
