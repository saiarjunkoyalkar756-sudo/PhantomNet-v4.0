# backend_api/test_threat_intelligence.py
import pytest
import httpx
import json
from unittest.mock import AsyncMock, patch
from .threat_intelligence import (
    fetch_urlhaus_iocs,
    enrich_event_with_iocs,
    enrich_agent_with_iocs,
    URL_IOC,
    IP_IOC,
    Domain_IOC,
    Hash_IOC,
)

# Sample JSON content that URLhaus might return (inside a ZIP file)
# This mimics the structure we expect after decompression
SAMPLE_URLHAUS_JSON = """
[
    {
        "id": "12345",
        "url": "http://malicious.com/payload.exe",
        "url_status": "online",
        "threat": "malware_distribution",
        "tags": ["executable", "exe"],
        "date_added": "2025-01-01 12:00:00 UTC",
        "reporter": "test_reporter"
    },
    {
        "id": "67890",
        "url": "http://phishing.net/login",
        "url_status": "online",
        "threat": "phishing",
        "tags": ["phishing", "credential_theft"],
        "date_added": "2025-01-02 13:00:00 UTC",
        "reporter": "test_reporter"
    }
]
"""


@pytest.mark.asyncio
async def test_fetch_urlhaus_iocs_success():
    # Mock httpx.AsyncClient.get to return a successful response with zipped content
    mock_response = AsyncMock()
    mock_response.raise_for_status.return_value = None
    mock_response.headers = {"content-type": "application/zip"}

    # Simulate a ZIP file containing SAMPLE_URLHAUS_JSON
    import io
    import zipfile

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("urlhaus.json", SAMPLE_URLHAUS_JSON)
    zip_buffer.seek(0)
    mock_response.content = zip_buffer.read()

    with patch(
        "httpx.AsyncClient.get", AsyncMock(return_value=mock_response)
    ) as mock_get:
        iocs = await fetch_urlhaus_iocs()
        mock_get.assert_called_once_with("https://urlhaus.abuse.ch/downloads/json/")
        assert isinstance(iocs, list)
        assert len(iocs) == 2
        assert all(isinstance(ioc, URL_IOC) for ioc in iocs)
        assert iocs[0].url == "http://malicious.com/payload.exe"
        assert iocs[1].threat_type == "phishing"


@pytest.mark.asyncio
async def test_fetch_urlhaus_iocs_http_error():
    # Mock httpx.AsyncClient.get to raise an HTTPStatusError
    mock_response = AsyncMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request",
        request=httpx.Request("GET", "http://test.com"),
        response=httpx.Response(400),
    )
    mock_response.headers = {
        "content-type": "application/json"
    }  # Even if it's an error, headers are there

    with patch(
        "httpx.AsyncClient.get", AsyncMock(return_value=mock_response)
    ) as mock_get:
        iocs = await fetch_urlhaus_iocs()
        assert iocs == []
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_urlhaus_iocs_json_decode_error():
    # Mock httpx.AsyncClient.get to return invalid JSON
    mock_response = AsyncMock()
    mock_response.raise_for_status.return_value = None
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.side_effect = json.JSONDecodeError(
        "Invalid JSON", doc="<invalid>", pos=0
    )
    mock_response.content = b"invalid json data"  # Provide raw content for the mock

    with patch(
        "httpx.AsyncClient.get", AsyncMock(return_value=mock_response)
    ) as mock_get:
        iocs = await fetch_urlhaus_iocs()
        assert iocs == []
        mock_get.assert_called_once()


# --- Auto-enrichment Tests ---
def test_enrich_event_with_iocs():
    # Sample IOCs for testing
    url_iocs = [URL_IOC(url="http://malicious.com/payload.exe", url_status="online", threat_type="malware")]
    ip_iocs = [IP_IOC(ip_address="198.51.100.10", threat_type="C2", source="Internal")]
    domain_iocs = [Domain_IOC(domain="malicious-domain.com", threat_type="malware", source="Internal")]
    hash_iocs = [Hash_IOC(hash_value="a1b2c3d4e5f6", hash_type="sha256", threat_type="ransomware", source="Internal")]

    # Sample event that should match some of the IOCs
    sample_event = {
        "event_id": "EVT-001",
        "message": "File with hash a1b2c3d4e5f6 downloaded from http://malicious.com/payload.exe",
        "url": "http://malicious.com/payload.exe",
        "source_ip": "198.51.100.10",
        "domain": "another-domain.com",
        "file_hash": "a1b2c3d4e5f6",
    }

    enriched_event = enrich_event_with_iocs(
        sample_event, url_iocs, ip_iocs, domain_iocs, hash_iocs
    )

    assert "threat_intelligence" in enriched_event
    assert len(enriched_event["threat_intelligence"]) == 3
    
    matches = {ti["type"] for ti in enriched_event["threat_intelligence"]}
    assert "URL_IOC" in matches
    assert "IP_IOC" in matches
    assert "Hash_IOC" in matches
    assert "Domain_IOC" not in matches


def test_enrich_agent_with_iocs():
    # Sample IOCs for testing
    url_iocs = [URL_IOC(url="http://phishing.net/login", url_status="online", threat_type="phishing")]
    ip_iocs = [IP_IOC(ip_address="10.0.0.5", threat_type="C2", source="Internal")]

    # Sample agent context that should match
    sample_agent = {
        "agent_id": "AGT-001",
        "last_url_accessed": "http://phishing.net/login",
        "last_seen_ip": "10.0.0.5",
    }

    enriched_agent = enrich_agent_with_iocs(
        sample_agent, url_iocs, ip_iocs
    )

    assert "threat_intelligence" in enriched_agent
    assert len(enriched_agent["threat_intelligence"]) == 2
    
    matches = {ti["type"] for ti in enriched_agent["threat_intelligence"]}
    assert "URL_IOC" in matches
    assert "IP_IOC" in matches
