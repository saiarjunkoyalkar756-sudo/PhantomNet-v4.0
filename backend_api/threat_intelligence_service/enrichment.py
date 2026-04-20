# backend_api/threat_intelligence_service/enrichment.py

import asyncio
import os
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta

from shared.logger_config import logger
from .models import UTMResult, IndicatorBase, ThreatScore, GeoLocation, PortInfo, DomainWhois, FileInfo, CloudResourceInfo
from .cache import threat_intel_cache, CACHE_TTL_SECONDS

# Import API Clients
from .clients.virustotal_client import VirusTotalClient
from .clients.alienvault_otx_client import AlienvaultOTXClient
from .clients.abuseipdb_client import AbuseIPDBClient
from .clients.shodan_client import ShodanClient
from .clients.censys_client import CensysClient
from .clients.google_cloud_security_client import GoogleCloudSecurityClient
from .clients.misp_client import MISPClient

logger = logger

class ThreatIntelligenceEnricher:
    """
    Orchestrates calls to various Threat Intelligence and Cloud Security APIs,
    normalizes responses into the Unified Threat Model (UTM), and manages caching.
    """
    def __init__(self):
        self.clients = {
            "virustotal": VirusTotalClient(),
            "alienvault_otx": AlienvaultOTXClient(),
            "abuseipdb": AbuseIPDBClient(),
            "shodan": ShodanClient(),
            "censys": CensysClient(),
            "google_cloud_security": GoogleCloudSecurityClient(), # Conceptual
            "misp": MISPClient(),
        }
        self.cache = threat_intel_cache
        logger.info("ThreatIntelligenceEnricher initialized with all clients.")

    async def _normalize_virustotal_report(self, indicator: IndicatorBase, vt_data: Dict[str, Any]) -> UTMResult:
        """Normalizes VirusTotal API response into UTMResult."""
        utm_result = UTMResult(indicator=indicator)
        utm_result.raw_responses["virustotal"] = vt_data

        attributes = vt_data.get("attributes", {})
        if not attributes: return utm_result

        # General threat verdict
        last_analysis_stats = attributes.get("last_analysis_stats", {})
        malicious_count = last_analysis_stats.get("malicious", 0)
        undetected_count = last_analysis_stats.get("undetected", 0)
        total_count = sum(last_analysis_stats.values())

        if malicious_count > 0:
            utm_result.is_malicious = True
            utm_result.overall_threat_score = min(100, (malicious_count / total_count) * 100) if total_count > 0 else 0

        # Threat Score
        vt_score = ThreatScore(
            provider="virustotal",
            score=utm_result.overall_threat_score,
            severity="high" if utm_result.is_malicious else "low",
            description=f"{malicious_count} detections out of {total_count} security engines."
        )
        utm_result.threat_scores.append(vt_score)

        if indicator.type == "ip":
            # IP specific info
            utm_result.asn = attributes.get("asn")
            utm_result.isp = attributes.get("as_owner")
            utm_result.geolocation = GeoLocation(
                country_code=attributes.get("country"),
                city=attributes.get("city_info"), # This might need parsing
                latitude=attributes.get("latitude"),
                longitude=attributes.get("longitude")
            )
            for port in attributes.get("last_https_certificate", {}).get("parsed", {}).get("extensions", {}).get("extended_key_usage", []):
                if port.startswith("TLS Web Server Authentication"):
                    utm_result.open_ports.append(PortInfo(port=443, protocol="tcp", service="https"))
            # Other open ports not easily available in general IP report

        elif indicator.type == "domain":
            # Domain specific info
            for ip in attributes.get("last_dns_records", []):
                if ip.get("type") == "A":
                    utm_result.resolutions.append(ip.get("value"))
            for subdomain_rel in vt_data.get("relationships", {}).get("subdomains", {}).get("data", []):
                utm_result.subdomains.append(subdomain_rel.get("id"))

        elif indicator.type == "hash":
            # File specific info
            utm_result.file_info = FileInfo(
                md5=attributes.get("md5"),
                sha1=attributes.get("sha1"),
                sha256=attributes.get("sha256"),
                file_name=attributes.get("meaningful_name"),
                file_size=attributes.get("size"),
                file_type=attributes.get("type_description"),
                upload_date=datetime.fromtimestamp(attributes.get("first_submission_date", 0)).isoformat()
            )

        elif indicator.type == "url":
            # URL specific info
            utm_result.final_url = attributes.get("last_final_url")
            utm_result.redirects_to = attributes.get("last_http_response_headers", {}).get("Location")
        
        return utm_result

    async def _normalize_alienvault_otx_report(self, indicator: IndicatorBase, otx_data: Dict[str, Any]) -> UTMResult:
        """Normalizes Alienvault OTX API response into UTMResult."""
        utm_result = UTMResult(indicator=indicator)
        utm_result.raw_responses["alienvault_otx"] = otx_data
        
        general = otx_data.get("general", {})
        if not general: return utm_result
        
        pulse_info = general.get("pulse_info", {})
        if pulse_info and pulse_info.get("count", 0) > 0:
            utm_result.is_malicious = True
            # OTX doesn't give a score, but presence in pulses is an indicator
            utm_result.overall_threat_score = 70 # Arbitrary score for malicious pulse presence
            
            otx_score = ThreatScore(
                provider="alienvault_otx",
                score=utm_result.overall_threat_score,
                severity="high",
                description=f"{pulse_info.get('count')} pulses found. {pulse_info.get('related_indicator_count')} related indicators."
            )
            utm_result.threat_scores.append(otx_score)
            
            # Add general context from OTX pulses
            for pulse in pulse_info.get("pulses", []):
                if "AlienVault OTX Pulse: " not in utm_result.indicator.description: # Avoid duplication
                    utm_result.indicator.description = (utm_result.indicator.description or "") + f" AlienVault OTX Pulse: {pulse.get('name')}."

        if indicator.type == "ip":
            # IP specific info
            utm_result.asn = general.get("asn")
            utm_result.isp = general.get("as_owner")
            utm_result.geolocation = GeoLocation(
                country_code=general.get("country_name"),
                city=general.get("city"),
            )
            # OTX general report for IP doesn't directly give open ports, it gives malware detections for ports
        
        elif indicator.type == "domain":
            # Domain specific info
            # OTX domain general doesn't directly give subdomains or resolutions without more specific API calls.
            pass # Currently no specific normalization

        elif indicator.type == "hash":
            # File specific info
            utm_result.file_info = FileInfo(
                md5=general.get("md5"),
                sha1=general.get("sha1"),
                sha256=general.get("sha256"),
            )
        
        elif indicator.type == "url":
            pass # No specific URL enrichment other than general pulse info
            
        return utm_result

    async def _normalize_abuseipdb_report(self, indicator: IndicatorBase, abuseipdb_data: Dict[str, Any]) -> UTMResult:
        """Normalizes AbuseIPDB API response into UTMResult."""
        utm_result = UTMResult(indicator=indicator)
        utm_result.raw_responses["abuseipdb"] = abuseipdb_data
        
        data = abuseipdb_data.get("data", {})
        if not data: return utm_result
        
        if data.get("abuseConfidenceScore", 0) > 0:
            utm_result.is_malicious = True
            utm_result.overall_threat_score = data.get("abuseConfidenceScore")
            
            abuse_score = ThreatScore(
                provider="abuseipdb",
                score=data.get("abuseConfidenceScore"),
                severity="high" if data.get("abuseConfidenceScore", 0) > 50 else "medium",
                description=f"Confidence score: {data.get('abuseConfidenceScore')}%. Total reports: {data.get('totalReports')}"
            )
            utm_result.threat_scores.append(abuse_score)
            
        if indicator.type == "ip":
            utm_result.isp = data.get("isp")
            utm_result.asn = data.get("asn")
            utm_result.geolocation = GeoLocation(
                country_code=data.get("countryCode"),
                country_name=data.get("countryName"),
                usage_type=data.get("usageType"),
            )
            # AbuseIPDB provides domain for IP, but not common ports or vulns

        return utm_result

    async def _normalize_shodan_report(self, indicator: IndicatorBase, shodan_data: Dict[str, Any]) -> UTMResult:
        """Normalizes Shodan API response into UTMResult."""
        utm_result = UTMResult(indicator=indicator)
        utm_result.raw_responses["shodan"] = shodan_data

        if not shodan_data: return utm_result

        # General info from Shodan
        utm_result.asn = shodan_data.get("asn")
        utm_result.isp = shodan_data.get("isp")
        utm_result.organization = shodan_data.get("org")
        utm_result.geolocation = GeoLocation(
            country_code=shodan_data.get("country_code"),
            country_name=shodan_data.get("country_name"),
            city=shodan_data.get("city"),
            latitude=shodan_data.get("latitude"),
            longitude=shodan_data.get("longitude"),
        )

        for port_data in shodan_data.get("ports", []):
            utm_result.open_ports.append(PortInfo(
                port=port_data,
                protocol="tcp", # Shodan defaults to TCP for host ports unless specified
                service=shodan_data.get("data", [{}])[0].get("product"), # Best effort service mapping
            ))
            # More detailed port info is in 'data' list

        # Shodan also provides some vulnerabilities
        if shodan_data.get("vulns"):
            utm_result.vulnerabilities.extend(shodan_data["vulns"])
            utm_result.is_malicious = True # If vulns are present, consider it potentially malicious
            utm_result.overall_threat_score = max(utm_result.overall_threat_score or 0, 60) # Arbitrary score

        shodan_score = ThreatScore(
            provider="shodan",
            score=utm_result.overall_threat_score,
            severity="medium" if utm_result.overall_threat_score else "low",
            description=f"Open ports: {len(shodan_data.get('ports', []))}. Vulnerabilities: {len(shodan_data.get('vulns', []))}"
        )
        utm_result.threat_scores.append(shodan_score)

        return utm_result

    async def _normalize_censys_report(self, indicator: IndicatorBase, censys_data: Dict[str, Any]) -> UTMResult:
        """Normalizes Censys API response into UTMResult."""
        utm_result = UTMResult(indicator=indicator)
        utm_result.raw_responses["censys"] = censys_data

        result = censys_data.get("result", {})
        if not result: return utm_result

        # General info for IP
        utm_result.asn = result.get("autonomous_system", {}).get("asn")
        utm_result.isp = result.get("autonomous_system", {}).get("organization_name")
        utm_result.organization = result.get("autonomous_system", {}).get("organization_name")
        utm_result.geolocation = GeoLocation(
            country_code=result.get("location", {}).get("country_code"),
            country_name=result.get("location", {}).get("country"),
            city=result.get("location", {}).get("city"),
            latitude=result.get("location", {}).get("latitude"),
            longitude=result.get("location", {}).get("longitude"),
        )

        # Open ports
        for service in result.get("services", []):
            utm_result.open_ports.append(PortInfo(
                port=service.get("port"),
                protocol=service.get("transport_protocol"),
                service=service.get("service_name"),
                status="open"
            ))
        
        # Censys doesn't provide a direct threat score but rich host info implies it's a target for analysis
        censys_score = ThreatScore(
            provider="censys",
            score=50 if result else 0, # Arbitrary score if data exists
            severity="medium" if result else "info",
            description=f"Services found: {len(result.get('services', []))}"
        )
        utm_result.threat_scores.append(censys_score)

        if indicator.type == "domain":
            # For domain, Censys usually provides info via associated certificates or hosts.
            # This normalization is for the certificate search.
            if "hits" in result: # Assuming result is from search_certificates
                for hit in result["hits"]:
                    # Can extract associated domains from certs
                    for dom in hit.get("parsed", {}).get("names", []):
                        if dom not in utm_result.subdomains:
                            utm_result.subdomains.append(dom)
            
        return utm_result

    async def _normalize_google_cloud_security_report(self, indicator: IndicatorBase, gc_data: Dict[str, Any]) -> UTMResult:
        """Normalizes Google Cloud Security API response into UTMResult."""
        utm_result = UTMResult(indicator=indicator)
        utm_result.raw_responses["google_cloud_security"] = gc_data

        if not gc_data: return utm_result
        
        resource_info = gc_data.get("resource", {})
        # This is a highly simplified conceptual normalization.
        # Real SCC/Cloud Asset Inventory data is much more complex.
        
        utm_result.cloud_resource = CloudResourceInfo(
            provider="Google Cloud",
            resource_type=resource_info.get("type", "unknown"),
            region=resource_info.get("location"),
            project_id=resource_info.get("projectDisplayName"),
            status="active", # Conceptual
            exposed_to_internet=gc_data.get("exposed_to_internet", False),
            misconfigurations=gc_data.get("misconfigurations", [])
        )
        if utm_result.cloud_resource.exposed_to_internet or utm_result.cloud_resource.misconfigurations:
            utm_result.is_malicious = True
            utm_result.overall_threat_score = max(utm_result.overall_threat_score or 0, 75)
            
        gc_score = ThreatScore(
            provider="google_cloud_security",
            score=utm_result.overall_threat_score,
            severity="high" if utm_result.is_malicious else "low",
            description=f"Cloud resource security posture: {len(utm_result.cloud_resource.misconfigurations or [])} misconfigurations. Internet exposed: {utm_result.cloud_resource.exposed_to_internet}"
        )
        utm_result.threat_scores.append(gc_score)

        return utm_result


    async def _call_client(self, client_name: str, client_method: Any, indicator_value: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Helper to call a client method and handle its exceptions for gather."""
        try:
            response = await client_method(indicator_value)
            return client_name, response
        except Exception as e:
            logger.error(f"Client {client_name} method failed for {indicator_value}: {e}")
            return client_name, {"error": str(e)}

    async def enrich_indicator(self, indicator_value: str, indicator_type: str, use_cache: bool = True) -> UTMResult:
        """
        Enriches a single threat indicator using all available TI/Cloud Security APIs.
        Manages caching and normalization.
        """
        indicator = IndicatorBase(value=indicator_value, type=indicator_type)
        cache_key = f"ti:{indicator_type}:{indicator_value}"
        
        # 1. Try cache first
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return UTMResult(**cached_result) # Re-instantiate Pydantic model

        # 2. Call APIs concurrently
        tasks_with_names = [] # Store tuples of (client_name, coroutine)
        
        # VirusTotal
        if indicator_type == "ip":
            tasks_with_names.append(("virustotal", self.clients["virustotal"].get_ip_report(indicator_value)))
        elif indicator_type == "domain":
            tasks_with_names.append(("virustotal", self.clients["virustotal"].get_domain_report(indicator_value)))
        elif indicator_type == "hash":
            tasks_with_names.append(("virustotal", self.clients["virustotal"].get_file_report(indicator_value)))
        elif indicator_type == "url":
            tasks_with_names.append(("virustotal", self.clients["virustotal"].get_url_report(indicator_value)))

        # Alienvault OTX
        if indicator_type in ["ip", "domain", "hash", "url"]:
            if indicator_type == "ip":
                tasks_with_names.append(("alienvault_otx", self.clients["alienvault_otx"].get_ip_reputation(indicator_value)))
            elif indicator_type == "domain":
                tasks_with_names.append(("alienvault_otx", self.clients["alienvault_otx"].get_domain_reputation(indicator_value)))
            elif indicator_type == "hash":
                tasks_with_names.append(("alienvault_otx", self.clients["alienvault_otx"].get_hash_reputation(indicator_value)))
            elif indicator_type == "url":
                tasks_with_names.append(("alienvault_otx", self.clients["alienvault_otx"].get_url_reputation(indicator_value)))

        # AbuseIPDB (IP only)
        if indicator_type == "ip":
            tasks_with_names.append(("abuseipdb", self.clients["abuseipdb"].check_ip(indicator_value)))

        # Shodan (IP only, domain search too but separate)
        if indicator_type == "ip":
            tasks_with_names.append(("shodan", self.clients["shodan"].get_ip_info(indicator_value)))

        # Censys (IP, Domain/Certificates)
        if indicator_type == "ip":
            tasks_with_names.append(("censys", self.clients["censys"].get_host_info(indicator_value)))
        elif indicator_type == "domain":
            tasks_with_names.append(("censys", self.clients["censys"].get_domain_info(indicator_value)))

        # Google Cloud Security (Cloud Resource ID only, conceptual)
        if indicator_type == "cloud_id":
            tasks_with_names.append(("google_cloud_security", self.clients["google_cloud_security"].get_resource_security_posture(indicator_value)))

        # MISP Integration
        tasks_with_names.append(("misp", self.clients["misp"].search_indicator(indicator_value)))

        # Execute all API calls concurrently
        # Extract coroutines for asyncio.gather
        coroutines = [task[1] for task in tasks_with_names]
        raw_responses_from_clients = await asyncio.gather(*coroutines, return_exceptions=True)

        # 3. Normalize responses and build UTMResult
        final_utm_result = UTMResult(indicator=indicator)
        malicious_agreements = 0
        all_threat_tags = set()
        confidence_levels = []
        reputation_scores = []

        for i, response in enumerate(raw_responses_from_clients):
            client_name = tasks_with_names[i][0] # Get client name from our stored tuple

            if isinstance(response, Exception):
                logger.error(f"Error during client call {client_name} for {indicator_value}: {response}")
                # Offline mode fallback: if client call fails, can return cached data or specific "offline" status
                final_utm_result.raw_responses[client_name] = {"error": str(response), "status": "offline_fallback_activated"}
                continue
            
            if response is None or (isinstance(response, dict) and response.get("error")):
                final_utm_result.raw_responses[client_name] = {"message": "No information found or client error."}
                continue
            
            # Normalize based on client
            normalized = UTMResult(indicator=indicator) # Initialize for each normalization pass
            if client_name == "virustotal":
                normalized = await self._normalize_virustotal_report(indicator, response)
            elif client_name == "alienvault_otx":
                normalized = await self._normalize_alienvault_otx_report(indicator, response)
            elif client_name == "abuseipdb":
                normalized = await self._normalize_abuseipdb_report(indicator, response)
            elif client_name == "shodan":
                normalized = await self._normalize_shodan_report(indicator, response)
            elif client_name == "censys":
                normalized = await self._normalize_censys_report(indicator, response)
            elif client_name == "google_cloud_security":
                normalized = await self._normalize_google_cloud_security_report(indicator, response)
            elif client_name == "misp":
                # Basic MISP normalization
                normalized = UTMResult(indicator=indicator)
                normalized.raw_responses["misp"] = response
                if response and response.get("Attribute"):
                    normalized.is_malicious = True
                    normalized.reputation_score = 90
                    normalized.threat_tags.append("misp_hit")
            
            # Merge results into final_utm_result
            final_utm_result.threat_scores.extend(normalized.threat_scores)
            final_utm_result.raw_responses.update(normalized.raw_responses)
            
            if normalized.reputation_score is not None and normalized.reputation_score > 50:
                malicious_agreements += 1
            if normalized.reputation_score is not None:
                reputation_scores.append(normalized.reputation_score)
            if normalized.confidence_level:
                confidence_levels.append(normalized.confidence_level)
            all_threat_tags.update(normalized.threat_tags)
            
            # Merge specific enrichment fields - this gets complex quickly,
            # for a true merge, each field needs careful handling.
            # For simplicity, if one client provides an enrichment, we take it.
            final_utm_result.asn = final_utm_result.asn or normalized.asn
            final_utm_result.isp = final_utm_result.isp or normalized.isp
            final_utm_result.organization = final_utm_result.organization or normalized.organization
            final_utm_result.geolocation = final_utm_result.geolocation or normalized.geolocation
            final_utm_result.open_ports.extend(normalized.open_ports)
            final_utm_result.vulnerabilities.extend(normalized.vulnerabilities)
            final_utm_result.resolutions.extend(normalized.resolutions)
            final_utm_result.subdomains.extend(normalized.subdomains)
            final_utm_result.whois = final_utm_result.whois or normalized.whois
            final_utm_result.file_info = final_utm_result.file_info or normalized.file_info
            final_utm_result.final_url = final_utm_result.final_url or normalized.final_url
            final_utm_result.redirects_to = final_utm_result.redirects_to or normalized.redirects_to
            final_utm_result.cloud_resource = final_utm_result.cloud_resource or normalized.cloud_resource
            
        # --- Correlation Logic ---
        # Overall malicious status
        if malicious_agreements >= 2:
            final_utm_result.is_malicious = True
            final_utm_result.reputation_score = min(100, (max(reputation_scores) if reputation_scores else 70) + (malicious_agreements * 10))
            final_utm_result.threat_tags.append("correlated_malicious")
            final_utm_result.confidence_level = "high"
        elif malicious_agreements == 1:
            final_utm_result.is_malicious = True
            final_utm_result.reputation_score = max(reputation_scores) if reputation_scores else 60
            final_utm_result.confidence_level = "medium"
        else:
            final_utm_result.is_malicious = False
            final_utm_result.reputation_score = sum(reputation_scores) // len(reputation_scores) if reputation_scores else 0
            # Determine overall confidence based on individual levels
            if "high" in confidence_levels: final_utm_result.confidence_level = "high"
            elif "medium" in confidence_levels: final_utm_result.confidence_level = "medium"
            else: final_utm_result.confidence_level = "low"
        
        final_utm_result.threat_tags.extend(list(all_threat_tags)) # Add all collected tags

        # 4. Cache the result
        if use_cache:
            self.cache.set(cache_key, final_utm_result.model_dump(), ttl=CACHE_TTL_SECONDS)

        return final_utm_result
    
    async def _call_client(self, client_name: str, client_method: Any, indicator_value: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Helper to call a client method and handle its exceptions for gather."""
        try:
            response = await client_method(indicator_value)
            return client_name, response
        except Exception as e:
            logger.error(f"Client {client_name} method failed for {indicator_value}: {e}")
            return client_name, {"error": str(e)}

