# backend_api/threat_intelligence_service/clients/abuseipdb_client.py

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
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "YOUR_ABUSEIPDB_API_KEY")
ABUSEIPDB_BASE_URL = "https://api.abuseipdb.com/api/v2"
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

abuseipdb_rate_limiter = RateLimiter(RATE_LIMIT_DELAY)

def abuseipdb_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if ABUSEIPDB_API_KEY == "YOUR_ABUSEIPDB_API_KEY" or not ABUSEIPDB_API_KEY:
            logger.warning(f"AbuseIPDB API key not configured. Skipping {func.__name__}.")
            return {"error": "AbuseIPDB API key not configured"}
        
        for attempt in range(MAX_RETRIES):
            try:
                async with abuseipdb_rate_limiter:
                    return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: # Rate limit exceeded
                    logger.warning(f"AbuseIPDB rate limit hit. Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                elif e.response.status_code == 404: # Not found
                    logger.info(f"AbuseIPDB returned 404 for {func.__name__}. No information found.")
                    return None
                else:
                    logger.error(f"AbuseIPDB API HTTP error ({e.response.status_code}) for {func.__name__}: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"AbuseIPDB API request error for {func.__name__}: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
        raise Exception(f"AbuseIPDB API call failed after {MAX_RETRIES} attempts.")
    return wrapper

class AbuseIPDBClient:
    def __init__(self):
        self.headers = {
            "Key": ABUSEIPDB_API_KEY,
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(base_url=ABUSEIPDB_BASE_URL, headers=self.headers, timeout=DEFAULT_TIMEOUT)
        logger.info("AbuseIPDBClient initialized.")

    @abuseipdb_api_call
    async def check_ip(self, ip_address: str, days: int = 90, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """Checks an IP address against the AbuseIPDB database."""
        logger.info(f"Fetching AbuseIPDB report for IP: {ip_address}")
        params = {
            "ipAddress": ip_address,
            "maxAgeInDays": days,
            "verbose": verbose
        }
        response = await self.client.get("/check", params=params)
        response.raise_for_status()
        return response.json().get("data")

# For direct testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Running AbuseIPDBClient example...")
    
    # Set a dummy API key for testing purposes if not in environment
    if "ABUSEIPDB_API_KEY" not in os.environ:
        os.environ["ABUSEIPDB_API_KEY"] = "dummy_api_key_for_testing"

    async def run_example():
        client = AbuseIPDBClient()

        # --- Test IP report ---
        test_ip = "8.8.8.8"
        try:
            ip_report = await client.check_ip(test_ip)
            logger.info(f"\nAbuseIPDB Report for {test_ip}:\n{json.dumps(ip_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting IP report: {e}")

        # --- Test a known bad IP (example, might change) ---
        # test_bad_ip = "185.222.208.205" 
        # try:
        #     bad_ip_report = await client.check_ip(test_bad_ip)
        #     logger.info(f"\nAbuseIPDB Report for known bad IP {test_bad_ip}:\n{json.dumps(bad_ip_report, indent=2)}")
        # except Exception as e:
        #     logger.error(f"Error getting bad IP report: {e}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("AbuseIPDBClient example stopped.")
