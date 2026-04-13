# backend_api/threat_intelligence_service/clients/shodan_client.py

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
SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "YOUR_SHODAN_API_KEY")
SHODAN_BASE_URL = "https://api.shodan.io"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
DEFAULT_TIMEOUT = 30
RATE_LIMIT_DELAY = 1 # Shodan's API is complex, start with 1 sec delay

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

shodan_rate_limiter = RateLimiter(RATE_LIMIT_DELAY)

def shodan_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if SHODAN_API_KEY == "YOUR_SHODAN_API_KEY" or not SHODAN_API_KEY:
            logger.warning(f"Shodan API key not configured. Skipping {func.__name__}.")
            return {"error": "Shodan API key not configured"}
        
        for attempt in range(MAX_RETRIES):
            try:
                async with shodan_rate_limiter:
                    return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401: # Invalid API key
                    logger.error(f"Shodan API HTTP error ({e.response.status_code}): Invalid API key for {func.__name__}")
                    raise
                elif e.response.status_code == 404: # Not found, often means no info
                    logger.info(f"Shodan returned 404 for {func.__name__}. No information found.")
                    return None
                elif e.response.status_code == 429: # Rate limit exceeded
                    logger.warning(f"Shodan rate limit hit. Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Shodan API HTTP error ({e.response.status_code}) for {func.__name__}: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"Shodan API request error for {func.__name__}: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
        raise Exception(f"Shodan API call failed after {MAX_RETRIES} attempts.")
    return wrapper

class ShodanClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=SHODAN_BASE_URL, timeout=DEFAULT_TIMEOUT)
        logger.info("ShodanClient initialized.")

    @shodan_api_call
    async def get_ip_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Retrieves all available information for an IP address."""
        logger.info(f"Fetching Shodan IP info for {ip_address}")
        response = await self.client.get(f"/shodan/host/{ip_address}", params={"key": SHODAN_API_KEY})
        response.raise_for_status()
        return response.json()

    @shodan_api_call
    async def search_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Searches Shodan for hosts related to a domain."""
        logger.info(f"Searching Shodan for domain {domain}")
        # Shodan doesn't have a direct "domain report" but you can search for hosts
        # that resolve to the domain or have the domain in their certificates.
        # This is a basic search for hosts found on the domain.
        response = await self.client.get(f"/shodan/host/search", params={"query": f"hostname:{domain}", "key": SHODAN_API_KEY})
        response.raise_for_status()
        return response.json()
    
    @shodan_api_call
    async def get_api_info(self) -> Optional[Dict[str, Any]]:
        """Returns information about the API key's current plan limits."""
        logger.info("Fetching Shodan API key info.")
        response = await self.client.get(f"/api-info", params={"key": SHODAN_API_KEY})
        response.raise_for_status()
        return response.json()

# For direct testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Running ShodanClient example...")
    
    # Set a dummy API key for testing purposes if not in environment
    if "SHODAN_API_KEY" not in os.environ:
        os.environ["SHODAN_API_KEY"] = "dummy_api_key_for_testing"

    async def run_example():
        client = ShodanClient()

        # --- Test API Info ---
        try:
            api_info = await client.get_api_info()
            logger.info(f"\nShodan API Info:\n{json.dumps(api_info, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting Shodan API info: {e}")

        # --- Test IP info ---
        test_ip = "8.8.8.8"
        try:
            ip_info = await client.get_ip_info(test_ip)
            logger.info(f"\nShodan IP Info for {test_ip}:\n{json.dumps(ip_info, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting IP info: {e}")

        # --- Test Domain Search ---
        test_domain = "google.com"
        try:
            domain_search = await client.search_domain(test_domain)
            logger.info(f"\nShodan Domain Search for {test_domain}:\n{json.dumps(domain_search, indent=2)}")
        except Exception as e:
            logger.error(f"Error searching domain: {e}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("ShodanClient example stopped.")
