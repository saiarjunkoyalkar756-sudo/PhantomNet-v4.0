# backend_api/threat_intelligence_service/models.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class IndicatorBase(BaseModel):
    """Base model for a threat indicator."""
    value: str = Field(..., description="The value of the indicator (IP, domain, hash, URL, Cloud Resource ID).")
    type: str = Field(..., description="The type of the indicator (e.g., 'ip', 'domain', 'hash', 'url', 'cloud_id').")

class ThreatScore(BaseModel):
    """Represents a threat score from a single source."""
    provider: str = Field(..., description="The threat intelligence provider.")
    score: Optional[int] = Field(None, description="The threat score (e.g., 0-100).")
    severity: Optional[str] = Field(None, description="Categorized severity (e.g., 'low', 'medium', 'high', 'critical').")
    description: Optional[str] = Field(None, description="Brief description or reason for the score.")

class GeoLocation(BaseModel):
    """Geographical information for an IP address."""
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    asn: Optional[str] = None
    isp: Optional[str] = None

class PortInfo(BaseModel):
    """Information about an open port."""
    port: int
    protocol: str
    service: Optional[str] = None
    version: Optional[str] = None
    status: Optional[str] = None # e.g., "open", "filtered"

class DomainWhois(BaseModel):
    """WHOIS information for a domain."""
    registrar: Optional[str] = None
    creation_date: Optional[str] = None
    expiration_date: Optional[str] = None
    updated_date: Optional[str] = None
    registrant_name: Optional[str] = None
    registrant_email: Optional[str] = None

class FileInfo(BaseModel):
    """Information about a file hash."""
    md5: Optional[str] = None
    sha1: Optional[str] = None
    sha256: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    upload_date: Optional[str] = None
    # Add more relevant file metadata as needed

class CloudResourceInfo(BaseModel):
    """Information about a cloud resource."""
    provider: str
    resource_type: str
    region: Optional[str] = None
    project_id: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    exposed_to_internet: Optional[bool] = None
    misconfigurations: Optional[List[str]] = None

class UTMResult(BaseModel):
    """Unified Threat Model Result for an indicator."""
    indicator: IndicatorBase
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    
    # Unified Schema fields
    reputation_score: Optional[int] = Field(None, description="Aggregated reputation score (0-100).")
    threat_tags: List[str] = Field(default_factory=list, description="List of threat tags from all sources.")
    confidence_level: Optional[str] = Field(None, description="Overall confidence level (e.g., 'low', 'medium', 'high').")
    
    # Raw scores and responses from individual providers
    threat_scores: List[ThreatScore] = Field(default_factory=list)
    raw_responses: Dict[str, Any] = Field(default_factory=dict, description="Raw responses from each provider.")

    # Enrichment data - specific to indicator type
    # IP Enrichment
    asn: Optional[str] = None
    isp: Optional[str] = None
    organization: Optional[str] = None
    geolocation: Optional[GeoLocation] = None
    open_ports: List[PortInfo] = Field(default_factory=list)
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list) # e.g., Shodan vulns
    
    # Domain Enrichment
    resolutions: List[str] = Field(default_factory=list) # Resolved IPs
    subdomains: List[str] = Field(default_factory=list)
    whois: Optional[DomainWhois] = None
    
    # Hash Enrichment
    file_info: Optional[FileInfo] = None
    
    # URL Enrichment
    redirects_to: Optional[str] = None
    final_url: Optional[str] = None
    
    # Cloud Resource ID Enrichment
    cloud_resource: Optional[CloudResourceInfo] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
