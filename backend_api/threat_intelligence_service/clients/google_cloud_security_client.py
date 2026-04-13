# backend_api/threat_intelligence_service/clients/google_cloud_security_client.py

import os
import httpx
import asyncio
import json
from typing import Dict, Any, Optional
from functools import wraps
from asyncio import sleep

from shared.logger_config import logger

logger = logger

# --- Configuration ---
GOOGLE_CLOUD_SECURITY_API_KEY = os.getenv("GOOGLE_CLOUD_SECURITY_API", "YOUR_GOOGLE_CLOUD_SECURITY_API")
# For a real integration, you'd use Google Cloud SDK with service accounts for authentication
# and specific Google Cloud APIs (e.g., Security Command Center, Cloud Asset Inventory).
# This is a highly simplified conceptual client using a generic API key.
GOOGLE_CLOUD_SECURITY_BASE_URL = "https://example.google.cloud.api/v1" # Placeholder URL
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
DEFAULT_TIMEOUT = 30
RATE_LIMIT_DELAY = 1 # 1 request per second

# --- Rate Limiter ---
class RateLimiter:
    def __init__(self, delay_seconds: float):
        self.delay_seconds = delay_seconds
        self.last_call_time = 0.0
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_call_time
            if elapsed < self.delay_seconds:
                await sleep(self.delay_seconds - elapsed)
            self.last_call_time = asyncio.get_event_loop().time()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

google_cloud_security_rate_limiter = RateLimiter(RATE_LIMIT_DELAY)

def google_cloud_security_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if GOOGLE_CLOUD_SECURITY_API_KEY == "YOUR_GOOGLE_CLOUD_SECURITY_API" or not GOOGLE_CLOUD_SECURITY_API_KEY:
            logger.warning(f"Google Cloud Security API key not configured. Skipping {func.__name__}.")
            return {"error": "Google Cloud Security API key not configured"}
        
        for attempt in range(MAX_RETRIES):
            try:
                async with google_cloud_security_rate_limiter:
                    return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: # Rate limit exceeded
                    logger.warning(f"Google Cloud Security rate limit hit. Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                elif e.response.status_code == 404: # Not found, often means no info
                    logger.warning(f"Google Cloud Security returned 404 for {func.__name__}. No information found.")
                    return None
                else:
                    logger.error(f"Google Cloud Security API HTTP error ({e.response.status_code}) for {func.__name__}: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"Google Cloud Security API request error for {func.__name__}: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
        raise Exception(f"Google Cloud Security API call failed after {MAX_RETRIES} attempts.")
    return wrapper

class GoogleCloudSecurityClient:
    def __init__(self):
        # For a real client, authentication would be more complex (e.g., service account JSON)
        self.client = httpx.AsyncClient(base_url=GOOGLE_CLOUD_SECURITY_BASE_URL, timeout=DEFAULT_TIMEOUT)
        logger.info("GoogleCloudSecurityClient initialized.")

    @google_cloud_security_api_call
    async def get_resource_security_posture(self, cloud_resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Conceptual: Retrieves the security posture (e.g., misconfigurations, findings)
        for a given Google Cloud resource ID.
        """
        logger.info(f"Fetching Google Cloud Security posture for resource ID: {cloud_resource_id}")
        # Placeholder for actual API call, Google Cloud APIs are more complex.
        # This would typically involve Security Command Center API, Cloud Asset Inventory API, etc.
        # Example URL: f"/organizations/{org_id}/assets/{asset_id}/securityPosture"
        response = await self.client.get(f"/securityPosture/{cloud_resource_id}", params={"key": GOOGLE_CLOUD_SECURITY_API_KEY})
        response.raise_for_status()
        return response.json()

    @google_cloud_security_api_call
    async def list_security_findings(self, project_id: str, filter_str: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Conceptual: Lists security findings for a given Google Cloud project.
        """
        logger.info(f"Fetching Google Cloud Security findings for project: {project_id}")
        params = {"key": GOOGLE_CLOUD_SECURITY_API_KEY, "filter": filter_str}
        response = await self.client.get(f"/projects/{project_id}/securityFindings", params=params)
        response.raise_for_status()
        return response.json()


# For direct testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Running GoogleCloudSecurityClient example...")
    
    # Set a dummy API key for testing purposes if not in environment
    if "GOOGLE_CLOUD_SECURITY_API" not in os.environ:
        os.environ["GOOGLE_CLOUD_SECURITY_API"] = "dummy_api_key_for_testing"

    async def run_example():
        client = GoogleCloudSecurityClient()

        # --- Test Resource Security Posture ---
        test_resource_id = "projects/my-project/locations/global/containerAnalysis/occurrences/12345"
        try:
            resource_posture = await client.get_resource_security_posture(test_resource_id)
            logger.info(f"\nGoogle Cloud Security Posture for {test_resource_id}:\n{json.dumps(resource_posture, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting resource security posture: {e}")

        # --- Test List Security Findings ---
        test_project_id = "my-gcp-project-123"
        try:
            findings = await client.list_security_findings(test_project_id)
            logger.info(f"\nGoogle Cloud Security Findings for {test_project_id}:\n{json.dumps(findings, indent=2)}")
        except Exception as e:
            logger.error(f"Error listing security findings: {e}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("GoogleCloudSecurityClient example stopped.")
