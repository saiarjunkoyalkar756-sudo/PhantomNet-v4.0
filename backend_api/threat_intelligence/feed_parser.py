import json
import logging
import time
import httpx
import asyncio
from typing import List, Dict, Any

logger = logging.getLogger("feed_parser")

# --- Real Threat Intelligence Feed Fetchers ---

async def fetch_urlhaus_recent():
    """
    Fetches the last 30 days of malicious URLs from URLhaus (abuse.ch).
    """
    logger.info("Fetching malicious URLs from URLhaus...")
    url = "https://urlhaus.abuse.ch/downloads/json_recent/"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            iocs = []
            for url_entry in data.get("urls", []):
                iocs.append({
                    "type": "url",
                    "value": url_entry.get("url"),
                    "source": "URLhaus",
                    "tags": url_entry.get("tags", [])
                })
            return iocs
    except Exception as e:
        logger.error(f"Failed to fetch URLhaus feed: {e}")
        return []

async def fetch_abuse_ch_ips():
    """
    Fetches the Feodo Tracker IP blocklist.
    """
    logger.info("Fetching C2 IPs from Feodo Tracker...")
    url = "https://feodotracker.abuse.ch/downloads/ipblocklist.txt"
    iocs = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            lines = response.text.splitlines()
            for line in lines:
                if not line.startswith("#") and line.strip():
                    iocs.append({
                        "type": "ip", 
                        "value": line.strip(), 
                        "source": "FeodoTracker (abuse.ch)"
                    })
    except Exception as e:
        logger.error(f"Failed to fetch FeodoTracker feed: {e}")
    return iocs

async def fetch_openphish_feed():
    """
    Fetches the latest phishing URLs from OpenPhish community feed.
    """
    logger.info("Fetching phishing feeds from OpenPhish...")
    url = "https://openphish.com/feed.txt"
    iocs = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            for line in response.text.splitlines():
                if line.strip():
                    iocs.append({
                        "type": "url",
                        "value": line.strip(),
                        "source": "OpenPhish"
                    })
    except Exception as e:
        logger.error(f"Failed to fetch OpenPhish feed: {e}")
    return iocs

def update_feeds(output_file: str):
    """
    Orchestrates the periodic update of global threat intelligence feeds.
    """
    while True:
        logger.info("GLOBAL FEED UPDATE SEQUENCE INITIATED.")
        
        loop = asyncio.get_event_loop()
        tasks = [
            fetch_urlhaus_recent(),
            fetch_abuse_ch_ips(),
            fetch_openphish_feed()
        ]
        results = loop.run_until_complete(asyncio.gather(*tasks))
        
        all_iocs = [ioc for sublist in results for ioc in sublist]
        
        # Deduplication
        unique_iocs = list({f"{ioc['type']}:{ioc['value']}": ioc for ioc in all_iocs}.values())

        try:
            with open(output_file, "w") as f:
                json.dump({
                    "iocs": unique_iocs, 
                    "last_updated": datetime.datetime.now().isoformat(),
                    "total_count": len(unique_iocs)
                }, f, indent=4)
            logger.info(f"Threat Intelligence synchronized. {len(unique_iocs)} active indicators stored.")
        except Exception as e:
            logger.error(f"Critical persistence error for TI feeds: {e}")

        # Update every 6 hours to respect API rate limits
        time.sleep(21600)

import datetime
if __name__ == "__main__":
    update_feeds("global_threat_intel.json")
