# backend_api/threat_intelligence_service/clients/censys_client.py

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
CENSYS_API_ID = os.getenv("CENSYS_API_ID", "YOUR_CENSYS_API_ID")
CENSYS_API_SECRET = os.getenv("CENSYS_API_SECRET", "YOUR_CENSYS_API_SECRET")
CENSYS_BASE_URL = "https://search.censys.io/api"
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

censys_rate_limiter = RateLimiter(RATE_LIMIT_DELAY)

def censys_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if CENSYS_API_ID == "YOUR_CENSYS_API_ID" or not CENSYS_API_ID or \
           CENSYS_API_SECRET == "YOUR_CENSYS_API_SECRET" or not CENSYS_API_SECRET:
            logger.warning(f"Censys API credentials not configured. Skipping {func.__name__}.")
            return {"error": "Censys API credentials not configured"}
        
        for attempt in range(MAX_RETRIES):
            try:
                async with censys_rate_limiter:
                    return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401: # Unauthorized
                    logger.error(f"Censys API HTTP error ({e.response.status_code}): Invalid credentials for {func.__name__}")
                    raise
                elif e.response.status_code == 404: # Not found, often means no info
                    logger.info(f"Censys returned 404 for {func.__name__}. No information found.")
                    return None
                elif e.response.status_code == 429: # Rate limit exceeded
                    logger.warning(f"Censys rate limit hit. Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Censys API HTTP error ({e.response.status_code}) for {func.__name__}: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"Censys API request error for {func.__name__}: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
        raise Exception(f"Censys API call failed after {MAX_RETRIES} attempts.")
    return wrapper

class CensysClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=CENSYS_BASE_URL, auth=(CENSYS_API_ID, CENSYS_API_SECRET), timeout=DEFAULT_TIMEOUT)
        logger.info("CensysClient initialized.")

    @censys_api_call
    async def get_host_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Retrieves host data for a given IP address."""
        logger.info(f"Fetching Censys host info for {ip_address}")
        response = await self.client.get(f"/v2/hosts/{ip_address}")
        response.raise_for_status()
        return response.json()

    @censys_api_call
    async def get_domain_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """Retrieves domain data for a given domain."""
        logger.info(f"Fetching Censys domain info for {domain}")
        # Censys has a separate API for certificates, but host search can provide domain-related info
        # This is a simplified call to get certificates related to a domain
        response = await self.client.get(f"/v2/certificates/search", params={"q": domain})
        response.raise_for_status()
        return response.json()

    @censys_api_call
    async def search_certificates(self, query: str) -> Optional[Dict[str, Any]]:
        """Performs a certificate search."""
        logger.info(f"Searching Censys certificates for query: {query}")
        response = await self.client.get(f"/v2/certificates/search", params={"q": query})
        response.raise_for_status()
        return response.json()

# For direct testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Running CensysClient example...")
    
    # Set dummy API keys for testing purposes if not in environment
    if "CENSYS_API_ID" not in os.environ:
        os.environ["CENSYS_API_ID"] = "dummy_api_id_for_testing"
    if "CENSYS_API_SECRET" not in os.environ:
        os.environ["CENSYS_API_SECRET"] = "dummy_api_secret_for_testing"

    async def run_example():
        client = CensysClient()

        # --- Test Host info ---
        test_ip = "8.8.8.8"
        try:
            host_info = await client.get_host_info(test_ip)
            logger.info(f"\nCensys Host Info for {test_ip}:\n{json.dumps(host_info, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting Host info: {e}")

        # --- Test Domain info (certificate search) ---
        test_domain = "google.com"
        try:
            domain_info = await client.get_domain_info(test_domain)
            logger.info(f"\nCensys Domain Info (Certificates) for {test_domain}:\n{json.dumps(domain_info, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting Domain info: {e}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("CensysClient example stopped.")
