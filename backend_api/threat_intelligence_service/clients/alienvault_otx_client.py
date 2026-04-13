# backend_api/threat_intelligence_service/clients/alienvault_otx_client.py

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
ALIENVAULT_OTX_API_KEY = os.getenv("ALIENVAULT_OTX_API", "YOUR_ALIENVAULT_OTX_KEY")
ALIENVAULT_OTX_BASE_URL = "https://otx.alienvault.com/api/v1"
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

alienvault_otx_rate_limiter = RateLimiter(RATE_LIMIT_DELAY)

def alienvault_otx_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if ALIENVAULT_OTX_API_KEY == "YOUR_ALIENVAULT_OTX_KEY" or not ALIENVAULT_OTX_API_KEY:
            logger.warning(f"Alienvault OTX API key not configured. Skipping {func.__name__}.")
            return {"error": "Alienvault OTX API key not configured"}
        
        for attempt in range(MAX_RETRIES):
            try:
                async with alienvault_otx_rate_limiter:
                    return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: # Rate limit exceeded
                    logger.warning(f"Alienvault OTX rate limit hit. Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                elif e.response.status_code == 404: # Not found, often means no info
                    logger.info(f"Alienvault OTX returned 404 for {func.__name__}. No information found.")
                    return None
                else:
                    logger.error(f"Alienvault OTX API HTTP error ({e.response.status_code}) for {func.__name__}: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"Alienvault OTX API request error for {func.__name__}: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
        raise Exception(f"Alienvault OTX API call failed after {MAX_RETRIES} attempts.")
    return wrapper

class AlienvaultOTXClient:
    def __init__(self):
        self.headers = {
            "X-OTX-API-KEY": ALIENVAULT_OTX_API_KEY,
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(base_url=ALIENVAULT_OTX_BASE_URL, headers=self.headers, timeout=DEFAULT_TIMEOUT)
        logger.info("AlienvaultOTXClient initialized.")

    @alienvault_otx_api_call
    async def get_ip_reputation(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Retrieves IP reputation from Alienvault OTX."""
        logger.info(f"Fetching Alienvault OTX IP reputation for {indicator}")
        response = await self.client.get(f"/indicators/IPv4/{indicator}/general")
        response.raise_for_status()
        return response.json()

    @alienvault_otx_api_call
    async def get_domain_reputation(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Retrieves Domain reputation from Alienvault OTX."""
        logger.info(f"Fetching Alienvault OTX Domain reputation for {indicator}")
        response = await self.client.get(f"/indicators/domain/{indicator}/general")
        response.raise_for_status()
        return response.json()

    @alienvault_otx_api_call
    async def get_hash_reputation(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Retrieves File Hash reputation from Alienvault OTX."""
        logger.info(f"Fetching Alienvault OTX File Hash reputation for {indicator}")
        # OTX supports MD5, SHA1, SHA256
        response = await self.client.get(f"/indicators/file/{indicator}/general")
        response.raise_for_status()
        return response.json()

    @alienvault_otx_api_call
    async def get_url_reputation(self, indicator: str) -> Optional[Dict[str, Any]]:
        """Retrieves URL reputation from Alienvault OTX."""
        logger.info(f"Fetching Alienvault OTX URL reputation for {indicator}")
        response = await self.client.get(f"/indicators/url/{indicator}/general")
        response.raise_for_status()
        return response.json()

# For direct testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Running AlienvaultOTXClient example...")
    
    # Set a dummy API key for testing purposes if not in environment
    if "ALIENVAULT_OTX_API" not in os.environ:
        os.environ["ALIENVAULT_OTX_API"] = "dummy_api_key_for_testing"

    async def run_example():
        client = AlienvaultOTXClient()

        # --- Test IP report ---
        test_ip = "8.8.8.8"
        try:
            ip_report = await client.get_ip_reputation(test_ip)
            logger.info(f"\nAlienvault OTX IP Report for {test_ip}:\n{json.dumps(ip_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting IP report: {e}")

        # --- Test Domain report ---
        test_domain = "google.com"
        try:
            domain_report = await client.get_domain_reputation(test_domain)
            logger.info(f"\nAlienvault OTX Domain Report for {test_domain}:\n{json.dumps(domain_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting Domain report: {e}")

        # --- Test File hash report (example hash, may not exist in OTX) ---
        test_hash = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f" # Example SHA256
        try:
            hash_report = await client.get_hash_reputation(test_hash)
            logger.info(f"\nAlienvault OTX Hash Report for {test_hash}:\n{json.dumps(hash_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting Hash report: {e}")
            
        # --- Test URL report ---
        test_url = "http://example.com"
        try:
            url_report = await client.get_url_reputation(test_url)
            logger.info(f"\nAlienvault OTX URL Report for {test_url}:\n{json.dumps(url_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting URL report: {e}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("AlienvaultOTXClient example stopped.")
