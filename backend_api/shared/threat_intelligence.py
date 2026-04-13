from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
import httpx
import asyncio
import os
import json
import io
import zipfile


# --- Pydantic Models for IOCs ---
class URL_IOC(BaseModel):
    url: str = Field(..., description="Malicious URL")
    url_status: str = Field(
        ..., description="Status of the URL (e.g., online, offline)"
    )
    tags: List[str] = Field([], description="Tags associated with the URL")
    threat_type: Optional[str] = Field(
        None, description="Type of threat (e.g., malware_distribution)"
    )
    date_added: Optional[str] = Field(None, description="Date the URL was added")
    source: str = Field("URLhaus", description="Source of the IOC")


class IP_IOC(BaseModel):
    ip_address: str = Field(..., description="Malicious IP Address")
    tags: List[str] = Field([], description="Tags associated with the IP")
    threat_type: Optional[str] = Field(None, description="Type of threat")
    source: str = Field(..., description="Source of the IOC")


class Domain_IOC(BaseModel):
    domain: str = Field(..., description="Malicious Domain")
    tags: List[str] = Field([], description="Tags associated with the Domain")
    threat_type: Optional[str] = Field(None, description="Type of threat")
    source: str = Field(..., description="Source of the IOC")


class Hash_IOC(BaseModel):
    hash_value: str = Field(..., description="Malicious File Hash (MD5, SHA1, SHA256)")
    hash_type: str = Field(..., description="Type of hash (e.g., MD5)")
    tags: List[str] = Field([], description="Tags associated with the Hash")
    threat_type: Optional[str] = Field(None, description="Type of threat")
    source: str = Field(..., description="Source of the IOC")


# --- Threat Intelligence Feed Integrations ---

URLHAUS_API_URL = "https://urlhaus.abuse.ch/downloads/json/"


async def fetch_urlhaus_iocs() -> List[URL_IOC]:
    """
    Fetches the latest malicious URLs from URLhaus.
    Returns a list of URL_IOC objects.
    """
    print("Fetching URLhaus IOCs...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(URLHAUS_API_URL)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

            print(f"URLhaus Response Headers: {response.headers}")

            # Check if the content is zipped
            if response.headers.get("content-type") == "application/zip":
                # Decompress the ZIP file
                with zipfile.ZipFile(io.BytesIO(response.content), "r") as z:
                    # Assuming there's only one file in the zip, or the main JSON file
                    # is the first one. Adjust if the zip structure is different.
                    json_filename = z.namelist()[0]
                    with z.open(json_filename) as json_file:
                        json_content = json_file.read().decode("utf-8")
                        raw_data = json.loads(json_content)
            else:
                raw_data = response.json()  # Use response.json() here

            url_iocs = []
            # Try to parse as a direct list of entries
            if isinstance(raw_data, list):
                data_entries = raw_data
            # If not direct list, try 'data' key
            elif (
                isinstance(raw_data, dict)
                and "data" in raw_data
                and isinstance(raw_data["data"], list)
            ):
                data_entries = raw_data["data"]
            else:
                print(
                    "Warning: Unexpected URLhaus JSON structure. Expected a direct list or a dictionary with a 'data' key."
                )
                return []  # Return empty list if structure is not as expected

            for entry in data_entries:
                if isinstance(entry, dict) and entry.get("url"):
                    url_iocs.append(
                        URL_IOC(
                            url=entry["url"],
                            url_status=entry.get("url_status", "unknown"),
                            tags=entry.get("tags", []),
                            threat_type=entry.get("threat", None),
                            date_added=entry.get("date_added", None),
                            source="URLhaus",
                        )
                    )

            print(f"Successfully fetched {len(url_iocs)} URLhaus IOCs.")
            return url_iocs

    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}: {exc}")
        return []
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}"
        )
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from URLhaus.")
        return []


# --- Auto-enrichment Functions ---
def enrich_event_with_iocs(
    event: Dict[str, Any],
    url_iocs: List[URL_IOC] = [],
    ip_iocs: List[IP_IOC] = [],
    domain_iocs: List[Domain_IOC] = [],
    hash_iocs: List[Hash_IOC] = [],
) -> Dict[str, Any]:
    """
    Enriches an event dictionary with threat intelligence IOCs.
    """
    enriched_event = event.copy()
    if "threat_intelligence" not in enriched_event:
        enriched_event["threat_intelligence"] = []

    event_values = {str(v) for v in event.values()}

    # URL matching
    for ioc in url_iocs:
        if ioc.url in event_values:
            enriched_event["threat_intelligence"].append(
                {
                    "type": "URL_IOC",
                    "match": ioc.url,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    # IP matching
    for ioc in ip_iocs:
        if ioc.ip_address in event_values:
            enriched_event["threat_intelligence"].append(
                {
                    "type": "IP_IOC",
                    "match": ioc.ip_address,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    # Domain matching
    for ioc in domain_iocs:
        if ioc.domain in event_values:
            enriched_event["threat_intelligence"].append(
                {
                    "type": "Domain_IOC",
                    "match": ioc.domain,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    # Hash matching
    for ioc in hash_iocs:
        if ioc.hash_value in event_values:
            enriched_event["threat_intelligence"].append(
                {
                    "type": "Hash_IOC",
                    "match": ioc.hash_value,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    return enriched_event


def enrich_agent_with_iocs(
    agent: Dict[str, Any],
    url_iocs: List[URL_IOC] = [],
    ip_iocs: List[IP_IOC] = [],
    domain_iocs: List[Domain_IOC] = [],
    hash_iocs: List[Hash_IOC] = [],
) -> Dict[str, Any]:
    """
    Enriches an agent's context dictionary with threat intelligence IOCs.
    """
    enriched_agent = agent.copy()
    if "threat_intelligence" not in enriched_agent:
        enriched_agent["threat_intelligence"] = []

    agent_values = {str(v) for v in agent.values()}

    # URL matching
    for ioc in url_iocs:
        if ioc.url in agent_values:
            enriched_agent["threat_intelligence"].append(
                {
                    "type": "URL_IOC",
                    "match": ioc.url,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    # IP matching
    for ioc in ip_iocs:
        if ioc.ip_address in agent_values:
            enriched_agent["threat_intelligence"].append(
                {
                    "type": "IP_IOC",
                    "match": ioc.ip_address,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    # Domain matching
    for ioc in domain_iocs:
        if ioc.domain in agent_values:
            enriched_agent["threat_intelligence"].append(
                {
                    "type": "Domain_IOC",
                    "match": ioc.domain,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    # Hash matching
    for ioc in hash_iocs:
        if ioc.hash_value in agent_values:
            enriched_agent["threat_intelligence"].append(
                {
                    "type": "Hash_IOC",
                    "match": ioc.hash_value,
                    "threat_type": ioc.threat_type,
                    "source": ioc.source,
                    "tags": ioc.tags,
                }
            )

    return enriched_agent


# --- Example Usage ---
async def main():
    print("--- Fetching Threat Intelligence ---")

    url_iocs = await fetch_urlhaus_iocs()
    if url_iocs:
        print(f"\nFirst 5 URLhaus IOCs:")
        for ioc in url_iocs[:5]:
            print(
                f"  URL: {ioc.url}, Status: {ioc.url_status}, Threat: {ioc.threat_type}"
            )
    else:
        print("No URLhaus IOCs fetched.")

    # Create some sample IOCs for demonstration
    ip_iocs = [IP_IOC(ip_address="198.51.100.10", threat_type="C2", source="Internal")]
    domain_iocs = [
        Domain_IOC(domain="malicious-domain.com", threat_type="malware", source="Internal")
    ]
    hash_iocs = [
        Hash_IOC(
            hash_value="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
            hash_type="sha256",
            threat_type="ransomware",
            source="Internal",
        )
    ]

    # Demonstrate auto-enrichment
    print("\n--- Demonstrating Auto-Enrichment ---")

    sample_event = {
        "event_id": "EVT-001",
        "message": "User clicked suspicious link to http://malicious.com/payload.exe",
        "url": "http://malicious.com/payload.exe",
        "source_ip": "198.51.100.10",
        "domain": "malicious-domain.com",
        "file_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        "timestamp": "2025-12-01T10:00:00Z",
    }

    enriched_event = enrich_event_with_iocs(
        sample_event, url_iocs, ip_iocs, domain_iocs, hash_iocs
    )
    print("\nEnriched Event:")
    print(json.dumps(enriched_event, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
