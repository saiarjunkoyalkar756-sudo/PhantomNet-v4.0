# backend_api/test_asset_management.py
import pytest
import datetime
from typing import List
from .asset_management import (
    Host,
    Port,
    Vulnerability,
    AssetRiskScore,
    simulate_host_discovery,
    calculate_asset_risk_score,
)


def test_simulate_host_discovery():
    """
    Test that simulate_host_discovery returns a list of valid Host objects.
    """
    hosts = simulate_host_discovery()
    assert isinstance(hosts, list)
    assert len(hosts) > 0
    for host in hosts:
        assert isinstance(host, Host)
        assert host.id is not None
        assert host.ip_address is not None
        assert isinstance(host.open_ports, list)
        assert isinstance(host.vulnerabilities, list)
        assert host.last_seen is not None


def test_calculate_asset_risk_score_critical_vulnerability():
    """
    Test risk score calculation for a host with a critical vulnerability.
    """
    host = Host(
        ip_address="1.1.1.1",
        hostname="test-critical",
        os="Linux",
        open_ports=[Port(number=22, protocol="tcp")],
        vulnerabilities=[
            Vulnerability(
                cve_id="CVE-CRITICAL",
                description="Critical Vuln",
                severity="Critical",
                cvss_score=9.9,
            )
        ],
    )
    risk_score = calculate_asset_risk_score(host)
    assert isinstance(risk_score, AssetRiskScore)
    assert risk_score.risk_score > 40  # Base risk (10) + Critical Vuln (40) = 50
    assert risk_score.critical_vulnerabilities_count == 1
    assert "Critical vulnerability (CVE-CRITICAL) detected." in risk_score.explanation


def test_calculate_asset_risk_score_high_ports_no_vulns():
    """
    Test risk score calculation for a host with many open ports but no vulnerabilities.
    """
    host = Host(
        ip_address="2.2.2.2",
        hostname="test-ports",
        os="Windows",
        open_ports=[
            Port(number=21, protocol="tcp"),
            Port(number=23, protocol="tcp"),
            Port(number=80, protocol="tcp"),
            Port(number=443, protocol="tcp"),
            Port(number=3389, protocol="tcp"),
        ],
        vulnerabilities=[],
    )
    risk_score = calculate_asset_risk_score(host)
    assert isinstance(risk_score, AssetRiskScore)
    assert risk_score.risk_score == (10 + 5 * 2)  # Base risk (10) + 5 ports (10) = 20
    assert risk_score.critical_vulnerabilities_count == 0
    assert risk_score.exposed_services_count == 5


def test_calculate_asset_risk_score_no_vulns_no_ports():
    """
    Test risk score calculation for a host with no vulnerabilities and no open ports.
    """
    host = Host(
        ip_address="3.3.3.3",
        hostname="test-clean",
        os="macOS",
        open_ports=[],
        vulnerabilities=[],
    )
    risk_score = calculate_asset_risk_score(host)
    assert isinstance(risk_score, AssetRiskScore)
    assert risk_score.risk_score == 10.0  # Only base risk
    assert risk_score.critical_vulnerabilities_count == 0
    assert risk_score.exposed_services_count == 0


def test_calculate_asset_risk_score_max_score():
    """
    Test that the risk score does not exceed 100.
    """
    host = Host(
        ip_address="4.4.4.4",
        hostname="test-max",
        os="Linux",
        open_ports=[Port(number=p, protocol="tcp") for p in range(1, 50)],  # 49 ports
        vulnerabilities=[
            Vulnerability(
                cve_id="CVE-CRITICAL-1",
                description="Critical Vuln 1",
                severity="Critical",
                cvss_score=10.0,
            ),
            Vulnerability(
                cve_id="CVE-CRITICAL-2",
                description="Critical Vuln 2",
                severity="Critical",
                cvss_score=10.0,
            ),
        ],
    )
    risk_score = calculate_asset_risk_score(host)
    assert isinstance(risk_score, AssetRiskScore)
    assert risk_score.risk_score == 100.0  # Should be capped at 100
    assert risk_score.critical_vulnerabilities_count == 2
