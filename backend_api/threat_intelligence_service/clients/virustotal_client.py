# backend_api/threat_intelligence_service/clients/virustotal_client.py

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
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "YOUR_VIRUSTOTAL_API_KEY")
VIRUSTOTAL_BASE_URL = "https://www.virustotal.com/api/v3"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
DEFAULT_TIMEOUT = 30
RATE_LIMIT_PER_MINUTE = 4 # Public API limit

# --- Rate Limiter ---
class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.interval = 60.0 / calls_per_minute
        self.last_call_time = 0.0
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        async with self.lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_call_time
            if elapsed < self.interval:
                await sleep(self.interval - elapsed)
            self.last_call_time = asyncio.get_event_loop().time()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

virustotal_rate_limiter = RateLimiter(RATE_LIMIT_PER_MINUTE)

def virustotal_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if VIRUSTOTAL_API_KEY == "YOUR_VIRUSTOTAL_API_KEY" or not VIRUSTOTAL_API_KEY:
            logger.warning(f"VirusTotal API key not configured. Skipping {func.__name__}.")
            return {"error": "VirusTotal API key not configured"}
        
        for attempt in range(MAX_RETRIES):
            try:
                async with virustotal_rate_limiter:
                    return await func(*args, **kwargs)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429: # Rate limit exceeded
                    logger.warning(f"VirusTotal rate limit hit. Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"VirusTotal API HTTP error ({e.response.status_code}) for {func.__name__}: {e.response.text}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"VirusTotal API request error for {func.__name__}: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {RETRY_DELAY_SECONDS}s (attempt {attempt + 1}/{MAX_RETRIES}).")
                    await sleep(RETRY_DELAY_SECONDS)
                else:
                    raise
        raise Exception(f"VirusTotal API call failed after {MAX_RETRIES} attempts.")
    return wrapper

class VirusTotalClient:
    def __init__(self):
        self.headers = {
            "x-apikey": VIRUSTOTAL_API_KEY,
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(base_url=VIRUSTOTAL_BASE_URL, headers=self.headers, timeout=DEFAULT_TIMEOUT)
        logger.info("VirusTotalClient initialized.")

    @virustotal_api_call
    async def get_ip_report(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Retrieves a report for an IP address."""
        logger.info(f"Fetching VirusTotal IP report for {ip_address}")
        response = await self.client.get(f"/ip_addresses/{ip_address}")
        response.raise_for_status()
        return response.json().get("data")

    @virustotal_api_call
    async def get_domain_report(self, domain: str) -> Optional[Dict[str, Any]]:
        """Retrieves a report for a domain."""
        logger.info(f"Fetching VirusTotal Domain report for {domain}")
        response = await self.client.get(f"/domains/{domain}")
        response.raise_for_status()
        return response.json().get("data")

    @virustotal_api_call
    async def get_file_report(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieves a report for a file hash (MD5, SHA1, SHA256)."""
        logger.info(f"Fetching VirusTotal File report for {file_hash}")
        response = await self.client.get(f"/files/{file_hash}")
        response.raise_for_status()
        return response.json().get("data")

    @virustotal_api_call
    async def get_url_report(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieves a report for a URL (after submitting it for analysis)."""
        logger.info(f"Fetching VirusTotal URL report for {url}")
        # First, submit the URL for analysis if not already done
        submit_response = await self.client.post("/urls", data={"url": url})
        submit_response.raise_for_status()
        analysis_id = submit_response.json().get("data", {}).get("id")

        if analysis_id:
            # Then, get the report for the analysis ID
            report_response = await self.client.get(f"/analyses/{analysis_id}")
            report_response.raise_for_status()
            return report_response.json().get("data")
        return None

# For direct testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running VirusTotalClient example...")
    
    # Set a dummy API key for testing purposes if not in environment
    if "VIRUSTOTAL_API_KEY" not in os.environ:
        os.environ["VIRUSTOTAL_API_KEY"] = "dummy_api_key_for_testing"

    async def run_example():
        client = VirusTotalClient()

        # --- Test IP report ---
        test_ip = "8.8.8.8" # Google DNS (should be clean)
        # test_ip = "1.1.1.1" # Cloudflare DNS (should be clean)
        # test_ip = "45.153.181.189" # Example of a known malicious IP (check actual threats)
        try:
            ip_report = await client.get_ip_report(test_ip)
            logger.info(f"\nVirusTotal IP Report for {test_ip}:\n{json.dumps(ip_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting IP report: {e}")

        # --- Test Domain report ---
        test_domain = "google.com"
        try:
            domain_report = await client.get_domain_report(test_domain)
            logger.info(f"\nVirusTotal Domain Report for {test_domain}:\n{json.dumps(domain_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting Domain report: {e}")

        # --- Test File hash report (example hash, may not exist in VT) ---
        test_hash = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f" # Example SHA256
        try:
            file_report = await client.get_file_report(test_hash)
            logger.info(f"\nVirusTotal File Report for {test_hash}:\n{json.dumps(file_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting File report: {e}")
            
        # --- Test URL report ---
        test_url = "http://example.com"
        try:
            url_report = await client.get_url_report(test_url)
            logger.info(f"\nVirusTotal URL Report for {test_url}:\n{json.dumps(url_report, indent=2)}")
        except Exception as e:
            logger.error(f"Error getting URL report: {e}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("VirusTotalClient example stopped.")
