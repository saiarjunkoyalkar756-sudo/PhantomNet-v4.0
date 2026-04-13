# backend_api/osint_engine.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import random
import time
import asyncio
import json

class OsintResult(BaseModel):
    source: str = Field(..., description="OSINT source (e.g., Shodan, GitHub)")
    query: str = Field(..., description="The original query performed")
    found_data: List[Dict[str, Any]] = Field([], description="List of data points found")
    summary: Optional[str] = Field(None, description="Summary of findings from this source")
    timestamp: float = Field(default_factory=time.time, description="Timestamp of the query")

class OsintQuery(BaseModel):
    target: str = Field(..., description="Target for the OSINT query (e.g., IP, domain, username)")
    sources: List[str] = Field([], description="List of OSINT sources to query (e.g., 'Shodan', 'GitHub')")
    include_summary: bool = False

class OsintEngine:
    def __init__(self):
        # Placeholder for actual API keys or client instances for each service
        self.api_keys = {
            "Shodan": "SHODAN_API_KEY_PLACEHOLDER",
            "Censys": "CENSYS_API_KEY_PLACEHOLDER",
            "GitHub": "GITHUB_API_TOKEN_PLACEHOLDER",
            # ... other sources
        }
        self.available_sources = ["Shodan", "Censys", "Spyse", "Chaos", "GitHub", "GoogleDorks"]
        self.recent_results: Dict[str, List[OsintResult]] = {} # Store results by target

    def _simulate_shodan_query(self, target: str) -> List[Dict[str, Any]]:
        """Simulates querying Shodan for information about a target IP/domain."""
        if random.random() < 0.8: # 80% chance of finding something
            return [
                {"ip": target, "org": "Example Corp", "ports": random.sample([21, 22, 23, 80, 443, 8080], random.randint(1, 3)), "country": "US", "vulnerabilities": ["CVE-2023-1234"] if random.random() < 0.3 else []},
                {"ip": target, "org": "Example Corp", "ports": random.sample([80, 443], random.randint(1, 2)), "country": "US", "products": ["nginx", "apache"]},
            ]
        return []

    def _simulate_censys_query(self, target: str) -> List[Dict[str, Any]]:
        """Simulates querying Censys for information."""
        if random.random() < 0.7:
            return [
                {"ip": target, "protocols": random.sample(["443/https", "80/http"], random.randint(1,2)), "last_updated": time.time()},
                {"domain": target, "certs": ["cert1", "cert2"]},
            ]
        return []
    
    def _simulate_spyse_query(self, target: str) -> List[Dict[str, Any]]:
        """Simulates querying Spyse for information."""
        if random.random() < 0.6:
            return [{"domain": target, "subdomains": [f"sub{i}.{target}" for i in range(random.randint(1,3))]}]
        return []

    def _simulate_chaos_query(self, target: str) -> List[Dict[str, Any]]:
        """Simulates querying Chaos for subdomains."""
        if random.random() < 0.5:
            return [{"domain": target, "subdomains": [f"test{i}.{target}" for i in range(random.randint(1,2))]}]
        return []

    def _simulate_github_secret_scan(self, target_org_or_user: str) -> List[Dict[str, Any]]:
        """Simulates scanning GitHub for exposed secrets."""
        if random.random() < 0.2:
            return [{"repo": f"{target_org_or_user}/some-repo", "secret_type": "AWS Key", "location": "file.py:10"}, {"repo": f"{target_org_or_user}/another-repo", "secret_type": "API Key", "location": "config.js:5"}]
        return []

    def _simulate_google_dork_automation(self, target: str) -> List[Dict[str, Any]]:
        """Simulates running automated Google Dorks."""
        if random.random() < 0.4:
            return [{"dork": f"site:{target} intitle:admin", "found_urls": [f"http://{target}/admin"]}, {"dork": f"site:{target} filetype:pdf", "found_urls": [f"http://{target}/docs/report.pdf"]}]
        return []

    async def execute_osint_query(self, query: OsintQuery) -> List[OsintResult]:
        """
        Executes OSINT queries against specified sources and aggregates results.
        """
        results: List[OsintResult] = []
        target = query.target

        for source in query.sources:
            if source not in self.available_sources:
                results.append(OsintResult(source=source, query=target, found_data=[], summary=f"Unknown OSINT source: {source}"))
                continue

            print(f"[{__name__}] Executing OSINT query for '{target}' using '{source}'...")
            found_data = []
            
            if source == "Shodan":
                found_data = self._simulate_shodan_query(target)
            elif source == "Censys":
                found_data = self._simulate_censys_query(target)
            elif source == "Spyse":
                found_data = self._simulate_spyse_query(target)
            elif source == "Chaos":
                found_data = self._simulate_chaos_query(target)
            elif source == "GitHub":
                found_data = self._simulate_github_secret_scan(target)
            elif source == "GoogleDorks":
                found_data = self._simulate_google_dork_automation(target)

            summary_text = f"Found {len(found_data)} items from {source} for {target}." if found_data else f"No data found from {source} for {target}."
            
            results.append(OsintResult(
                source=source,
                query=target,
                found_data=found_data,
                summary=summary_text if query.include_summary else None
            ))
            await asyncio.sleep(random.uniform(0.5, 2.0)) # Simulate API call delay
        
        self.recent_results[target] = results # Store the latest results for this target
        return results

    def get_recent_osint_results(self, target: str) -> Optional[List[OsintResult]]:
        """Retrieves the most recent OSINT results for a given target."""
        return self.recent_results.get(target)


if __name__ == "__main__":
    engine = OsintEngine()

    print("--- Testing OSINT Query ---")
    osint_query = OsintQuery(
        target="example.com",
        sources=["Shodan", "GitHub", "GoogleDorks", "Censys", "UnknownSource"],
        include_summary=True
    )
    
    async def run_osint_test():
        results = await engine.execute_osint_query(osint_query)
        print(json.dumps([r.dict() for r in results], indent=2))
        
        print("\n--- Retrieving Recent Results ---")
        recent = engine.get_recent_osint_results("example.com")
        print(json.dumps([r.dict() for r in recent], indent=2) if recent else "No recent results.")

    asyncio.run(run_osint_test())
