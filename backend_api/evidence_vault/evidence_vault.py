import uuid
import datetime
import json
from typing import Dict, Any, List, Optional

class EvidenceVault:
    """
    Manages the secure storage and retrieval of forensic evidence.
    """
    def __init__(self):
        self.evidence_store: Dict[str, Dict[str, Any]] = {}
        print("EvidenceVault initialized.")

    async def store_evidence(self, data: str, source: str, tags: List[str], filename: Optional[str] = None) -> str:
        """
        Stores a piece of evidence in the vault.
        """
        evidence_id = f"evidence-{uuid.uuid4().hex}"
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        evidence_record = {
            "id": evidence_id,
            "timestamp": timestamp,
            "source": source,
            "tags": tags,
            "filename": filename,
            "data": data, # In a real system, this might be a path to a secure storage or a hash of the data.
        }
        self.evidence_store[evidence_id] = evidence_record
        print(f"Evidence {evidence_id} stored from source {source}.")
        return evidence_id

    async def retrieve_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a piece of evidence from the vault.
        """
        return self.evidence_store.get(evidence_id)

    async def search_evidence(self, query: str, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Searches for evidence based on a query and optional tags.
        """
        results = []
        for record in self.evidence_store.values():
            match_query = query.lower() in json.dumps(record).lower()
            match_tags = True
            if tags:
                match_tags = any(tag.lower() in record["tags"] for tag in tags)
            
            if match_query and match_tags:
                results.append(record)
        return results

evidence_vault = EvidenceVault()
