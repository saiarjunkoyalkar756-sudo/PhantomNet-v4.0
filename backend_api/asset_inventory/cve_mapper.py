import logging
import json
import requests

logger = logging.getLogger(__name__)

class CVEMapper:
    """
    Simulates Attack Surface Mapping by querying known CVE databases 
    (or using a localized mapping table) based on Nmap product versions.
    """
    def __init__(self):
        # A localized mock database of known vulnerabilities for Attack Surface Mapping
        self.known_vulnerabilities = {
            "Apache httpd": [
                {"cve": "CVE-2021-41773", "severity": "CRITICAL", "description": "Path traversal and file disclosure in Apache HTTP Server 2.4.49"}
            ],
            "OpenSSH": [
                {"cve": "CVE-2024-6387", "severity": "HIGH", "description": "regreSSHion: unauthenticated RCE in OpenSSH glibc"}
            ],
            "nginx": [
                {"cve": "CVE-2021-23017", "severity": "HIGH", "description": "1-byte memory overwrite in resolver"}
            ],
            "Microsoft IIS httpd": [
                {"cve": "CVE-2015-1635", "severity": "CRITICAL", "description": "HTTP.sys RCE (MS15-034)"}
            ]
        }

    def determine_vulnerabilities(self, product_name: str, version: str) -> list:
        """
        Takes an identified product from Nmap and searches the Attack Surface Matrix.
        """
        if not product_name:
            return []

        vulns = []
        # Simulate local database matching
        for key, cve_list in self.known_vulnerabilities.items():
            if key.lower() in product_name.lower():
                vulns.extend(cve_list)
                
        # In a real environment, we would also hit the NVD API
        # e.g., requests.get(f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={product_name}")
        
        return vulns
