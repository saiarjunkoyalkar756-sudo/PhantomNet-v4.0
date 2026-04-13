# backend_api/asset_management.py
import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import random
import uuid


# --- Pydantic Models for Asset Inventory ---
class Port(BaseModel):
    number: int = Field(..., description="Port number (e.g., 22, 80, 443)")
    protocol: str = Field(..., description="Protocol (e.g., tcp, udp)")
    service: Optional[str] = Field(
        None, description="Service running on the port (e.g., ssh, http)"
    )
    version: Optional[str] = Field(None, description="Version of the service")
    state: str = Field(
        "open", description="State of the port (e.g., open, closed, filtered)"
    )


class Vulnerability(BaseModel):
    cve_id: str = Field(..., description="CVE ID (e.g., CVE-2023-1234)")
    description: str = Field(..., description="Description of the vulnerability")
    severity: str = Field(
        ..., description="Severity (e.g., Critical, High, Medium, Low)"
    )
    cvss_score: Optional[float] = Field(None, description="CVSS score")


class Host(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique Host ID"
    )
    ip_address: str = Field(..., description="IP Address of the host")
    hostname: Optional[str] = Field(None, description="Hostname of the host")
    os: Optional[str] = Field(None, description="Operating System detected")
    mac_address: Optional[str] = Field(None, description="MAC Address")
    open_ports: List[Port] = Field([], description="List of open ports and services")
    vulnerabilities: List[Vulnerability] = Field(
        [], description="List of detected vulnerabilities"
    )
    last_seen: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="microseconds"
        ),
        description="Last seen timestamp",
    )
    risk_score: Optional[float] = Field(
        None, description="Calculated risk score for the host"
    )


class AssetRiskScore(BaseModel):
    asset_id: str = Field(..., description="ID of the asset (Host)")
    risk_score: float = Field(
        ..., ge=0, le=100.0, description="Overall risk score (0-100)"
    )
    explanation: Optional[str] = Field(
        None, description="Explanation for the risk score"
    )
    critical_vulnerabilities_count: int = Field(
        0, description="Number of critical vulnerabilities"
    )
    exposed_services_count: int = Field(
        0, description="Number of exposed services (open ports)"
    )


# --- Simulated Discovery Functions ---
def simulate_host_discovery() -> List[Host]:
    """
    Simulates discovering hosts on a network.
    Returns a list of Host objects with mock data.
    """
    hosts: List[Host] = []

    # Simulate first host
    host1_ports = [
        Port(
            number=22,
            protocol="tcp",
            service="ssh",
            version="OpenSSH 8.9",
            state="open",
        ),
        Port(
            number=80,
            protocol="tcp",
            service="http",
            version="Apache 2.4.52",
            state="open",
        ),
        Port(
            number=443,
            protocol="tcp",
            service="https",
            version="Apache 2.4.52",
            state="open",
        ),
    ]
    host1_vulnerabilities = [
        Vulnerability(
            cve_id="CVE-2023-4567",
            description="SSH vulnerability",
            severity="High",
            cvss_score=8.5,
        ),
        Vulnerability(
            cve_id="CVE-2023-1234",
            description="Apache RCE",
            severity="Critical",
            cvss_score=9.8,
        ),
    ]
    hosts.append(
        Host(
            ip_address="192.168.1.10",
            hostname="webserver-prod",
            os="Ubuntu 22.04 LTS",
            mac_address="00:1A:2B:3C:4D:5E",
            open_ports=host1_ports,
            vulnerabilities=host1_vulnerabilities,
        )
    )

    # Simulate second host
    host2_ports = [
        Port(
            number=3389,
            protocol="tcp",
            service="ms-wbt-server",
            version="Microsoft RDP",
            state="open",
        )
    ]
    host2_vulnerabilities = [
        Vulnerability(
            cve_id="CVE-2022-7890",
            description="RDP authentication bypass",
            severity="Critical",
            cvss_score=9.1,
        )
    ]
    hosts.append(
        Host(
            ip_address="192.168.1.20",
            hostname="rdp-jumpbox",
            os="Windows Server 2019",
            mac_address="00:11:22:33:44:55",
            open_ports=host2_ports,
            vulnerabilities=host2_vulnerabilities,
        )
    )

    # Simulate third host (less critical)
    host3_ports = [
        Port(
            number=53,
            protocol="udp",
            service="domain",
            version="BIND 9.16",
            state="open",
        )
    ]
    host3_vulnerabilities = []
    hosts.append(
        Host(
            ip_address="192.168.1.30",
            hostname="dns-server",
            os="CentOS 7",
            mac_address="AA:BB:CC:DD:EE:FF",
            open_ports=host3_ports,
            vulnerabilities=host3_vulnerabilities,
        )
    )

    return hosts


# --- Risk Scoring Logic ---
def calculate_asset_risk_score(host: Host) -> AssetRiskScore:
    """
    Calculates a simple risk score for a given host based on its properties.
    """
    score = 0.0
    explanation_parts: List[str] = []
    critical_vulnerabilities = 0
    exposed_services = len(host.open_ports)

    # Base risk for any discovered asset
    score += 10
    explanation_parts.append("Base risk for discovered asset.")

    # Risk based on open ports
    if host.open_ports:
        score += len(host.open_ports) * 2
        explanation_parts.append(
            f"{len(host.open_ports)} open ports contribute to risk."
        )

    # Risk based on vulnerabilities
    for vul in host.vulnerabilities:
        if vul.severity.lower() == "critical":
            score += 40
            critical_vulnerabilities += 1
            explanation_parts.append(f"Critical vulnerability ({vul.cve_id}) detected.")
        elif vul.severity.lower() == "high":
            score += 20
            explanation_parts.append(f"High vulnerability ({vul.cve_id}) detected.")
        elif vul.severity.lower() == "medium":
            score += 10
            explanation_parts.append(f"Medium vulnerability ({vul.cve_id}) detected.")

    # Cap score at 100
    score = min(score, 100.0)

    return AssetRiskScore(
        asset_id=host.id,
        risk_score=round(score, 2),
        explanation=" ".join(explanation_parts),
        critical_vulnerabilities_count=critical_vulnerabilities,
        exposed_services_count=exposed_services,
    )


# --- Example Usage ---
async def main():
    print("--- Simulating Asset Inventory ---")

    discovered_hosts = simulate_host_discovery()
    print(f"Discovered {len(discovered_hosts)} hosts.")

    print("\n--- Calculating Asset Risk Scores ---")
    for host in discovered_hosts:
        risk_score = calculate_asset_risk_score(host)
        host.risk_score = risk_score.risk_score  # Update host object with its score
        print(f"\nHost: {host.hostname} ({host.ip_address})")
        print(f"  OS: {host.os}")
        print(f"  Open Ports: {', '.join([str(p.number) for p in host.open_ports])}")
        print(f"  Vulnerabilities: {len(host.vulnerabilities)}")
        print(
            f"  Calculated Risk: {risk_score.risk_score} (Critical Vulns: {risk_score.critical_vulnerabilities_count})"
        )
        print(f"  Explanation: {risk_score.explanation}")


if __name__ == "__main__":
    import asyncio

    # Import datetime and timezone for Host.last_seen default_factory
    import datetime
    from datetime import timezone

    asyncio.run(main())
