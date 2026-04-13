from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class PacketMetadata(BaseModel):
    timestamp: datetime.datetime = Field(..., description="Timestamp of the packet capture")
    source_ip: str = Field(..., description="Source IP address")
    destination_ip: str = Field(..., description="Destination IP address")
    source_port: int = Field(..., description="Source port")
    destination_port: int = Field(..., description="Destination port")
    protocol: str = Field(..., description="Protocol (e.g., TCP, UDP, ICMP)")
    size: int = Field(..., description="Packet size in bytes")

class DnsQuery(BaseModel):
    timestamp: datetime.datetime = Field(..., description="Timestamp of the DNS query")
    client_ip: str = Field(..., description="IP of the client that made the request")
    domain_name: str = Field(..., description="Domain name being queried")
    record_type: str = Field(..., description="DNS record type (e.g., A, AAAA, CNAME)")
    entropy: Optional[float] = Field(None, description="Shannon entropy of the domain name")
    is_blacklisted: bool = Field(False, description="Whether the domain is on a known blacklist")

class SuspiciousConnection(BaseModel):
    timestamp: datetime.datetime = Field(..., description="Timestamp of the detected suspicious connection")
    source_ip: str = Field(..., description="Source IP address")
    destination_ip: str = Field(..., description="Destination IP address")
    destination_port: int = Field(..., description="Destination port")
    pattern: str = Field(..., description="Detected pattern (e.g., 'rare_port', 'beaconing', 'c2')")
    confidence: float = Field(..., description="Confidence score of the detection")

class NetworkConnection(BaseModel):
    source_ip: str
    destination_ip: str
    destination_port: int
    protocol: str

class NetworkGraph(BaseModel):
    timestamp: datetime.datetime = Field(..., description="Timestamp of the graph generation")
    connections: List[NetworkConnection] = Field(..., description="List of active network connections")

class NetworkEvents(BaseModel):
    packets: List[PacketMetadata] = Field(default_factory=list)
    dns_queries: List[DnsQuery] = Field(default_factory=list)
    suspicious_connections: List[SuspiciousConnection] = Field(default_factory=list)
    network_graph: Optional[NetworkGraph] = None
