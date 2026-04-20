import nmap
import json
import logging
from datetime import datetime
from .database import upsert_asset
from .cve_mapper import CVEMapper

logger = logging.getLogger(__name__)


def determine_asset_type(ports_info: dict) -> str:
    """
    Determines the asset type based on open ports and services.
    Simplified logic for demonstration.
    """
    asset_type = "endpoint"
    if "tcp" in ports_info:
        tcp_ports = [p["port"] for p in ports_info["tcp"]["ports"]]
        if 80 in tcp_ports or 443 in tcp_ports:
            asset_type = "server"
        if 22 in tcp_ports or 3389 in tcp_ports:
            asset_type = "server"
        if 5432 in tcp_ports or 3306 in tcp_ports: # PostgreSQL, MySQL
            asset_type = "database_server"
    # Further logic could involve checking OS, open container ports, cloud APIs, etc.
    return asset_type

def run_scan(target: str):
    logger.info(f"Nmap scan started for target: {target}")
    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=target, arguments="-sT -O -T4") # -O for OS detection

        for host in nm.all_hosts():
            ip_address = host
            hostname = nm[host].hostname()
            os_guess = "Unknown"
            if 'osmatch' in nm[host]:
                for osmatch in nm[host]['osmatch']:
                    os_guess = osmatch['name']
                    break
            
            mac_address = None
            if 'addresses' in nm[host] and 'mac' in nm[host]['addresses']:
                mac_address = nm[host]['addresses']['mac']

            cve_mapper = CVEMapper()
            total_vulnerabilities = []
            
            ports_info = {}
            for proto in nm[host].all_protocols():
                ports_info[proto] = {"ports": []}
                lport = nm[host][proto].keys()
                for port in lport:
                    ports_info[proto]["ports"].append(
                        {
                            "port": port,
                            "state": nm[host][proto][port]["state"],
                            "name": nm[host][proto][port]["name"],
                            "product": nm[host][proto][port]["product"],
                            "version": nm[host][proto][port]["version"],
                            "extra_info": nm[host][proto][port]["extrainfo"],
                        }
                    )
                    
                    # Dynamically map the discovered application to Attack Surface Vulns
                    detected_vulns = cve_mapper.determine_vulnerabilities(
                        nm[host][proto][port]["product"], 
                        nm[host][proto][port]["version"]
                    )
                    total_vulnerabilities.extend(detected_vulns)
            
            asset_type = determine_asset_type(ports_info)

            asset_data = {
                "ip_address": ip_address,
                "hostname": hostname if hostname else None,
                "mac_address": mac_address,
                "os": os_guess,
                "asset_type": asset_type,
                "last_seen": datetime.now().isoformat(),
                "vulnerabilities": total_vulnerabilities,
                "risk_level": "CRITICAL" if any(v["severity"] == "CRITICAL" for v in total_vulnerabilities) else "LOW",
                "details": {
                    "scan_status": nm[host].state(),
                    "ports_info": ports_info,
                }
            }
            upsert_asset(asset_data)
            logger.info(f"Asset {ip_address} ({hostname}) upserted as {asset_type}.")

        logger.info(f"Nmap scan finished for target: {target}")

    except nmap.nmap.PortScannerError as e:
        logger.error(
            f"Nmap scan failed for {target}: {e}. Make sure nmap is installed and in your system's PATH."
        )
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during the scan for {target}: {e}", exc_info=True
        )
