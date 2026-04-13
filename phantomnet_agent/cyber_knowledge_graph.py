import json
import logging
from collections import defaultdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger("phantomnet_agent.cyber_knowledge_graph")

class CKGNode:
    """Represents a node in the Cyber-Knowledge Graph."""
    def __init__(self, id: str, type: str, properties: Dict[str, Any] = None):
        self.id = id
        self.type = type
        self.properties = properties if properties is not None else {}

    def to_dict(self):
        return {"id": self.id, "type": self.type, "properties": self.properties}

class CKGEdge:
    """Represents an edge (relationship) in the Cyber-Knowledge Graph."""
    def __init__(self, source_id: str, target_id: str, type: str, properties: Dict[str, Any] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.type = type
        self.properties = properties if properties is not None else {}

    def to_dict(self):
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.type,
            "properties": self.properties,
        }

class CyberKnowledgeGraph:
    """
    Conceptual class for managing the Cyber-Knowledge Graph.
    This in-memory graph simulates interactions with a persistent graph database.
    """
    def __init__(self):
        self.logger = logging.getLogger("phantomnet_agent.cyber_knowledge_graph")
        self.nodes: Dict[str, CKGNode] = {}  # {node_id: CKGNode}
        self.edges: Dict[str, List[CKGEdge]] = defaultdict(list)  # {source_node_id: [CKGEdge]}
        self._initialize_static_knowledge()
        self.logger.info("Cyber-Knowledge Graph (CKG) initialized (conceptual, in-memory).")

    def _initialize_static_knowledge(self):
        """Populates the graph with some initial, static threat intelligence/context."""
        # Example: Known malicious IPs, common attack tools, CVEs
        self.add_node(CKGNode("malicious_ip_1", "IP", {"reputation": "bad", "country": "RU"}))
        self.add_node(CKGNode("malicious_ip_2", "IP", {"reputation": "bad", "country": "CN"}))
        self.add_node(CKGNode("Nmap", "Tool", {"category": "reconnaissance"}))
        self.add_node(CKGNode("Metasploit", "Tool", {"category": "exploitation"}))
        self.add_node(CKGNode("CVE-2021-1234", "Vulnerability", {"severity": "high"}))
        self.add_node(CKGNode("CVE-2022-5678", "Vulnerability", {"severity": "medium"}))
        self.add_node(CKGNode("APT28", "ThreatActor", {"motto": "Fancy Bear"}))
        self.add_node(CKGNode("Windows_Server_2019", "Asset", {"criticality": "high"}))
        self.add_node(CKGNode("Linux_Web_Server", "Asset", {"criticality": "medium"}))

        self.add_edge(CKGEdge("malicious_ip_1", "Nmap", "USES"))
        self.add_edge(CKGEdge("malicious_ip_1", "CVE-2021-1234", "TARGETS"))
        self.add_edge(CKGEdge("APT28", "malicious_ip_1", "OPERATES_THROUGH"))
        self.add_edge(CKGEdge("Metasploit", "CVE-2021-1234", "EXPLOITS"))
        self.add_edge(CKGEdge("Linux_Web_Server", "CVE-2021-1234", "HAS_VULNERABILITY"))
        
        self.logger.debug("Static knowledge loaded into CKG.")

    def add_node(self, node: CKGNode):
        """Adds a node to the graph."""
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self.logger.debug(f"Added node: {node.to_dict()}")
        else:
            # Update existing node if new properties are provided
            self.nodes[node.id].properties.update(node.properties)
            self.logger.debug(f"Node {node.id} already exists, properties updated.")

    def add_edge(self, edge: CKGEdge):
        """Adds an edge to the graph."""
        if edge.source_id not in self.nodes:
            self.logger.warning(f"Source node {edge.source_id} not found for edge.")
            return
        if edge.target_id not in self.nodes:
            self.logger.warning(f"Target node {edge.target_id} not found for edge.")
            return
        
        # Prevent duplicate edges (simple check, could be more robust)
        for existing_edge in self.edges[edge.source_id]:
            if existing_edge.target_id == edge.target_id and existing_edge.type == edge.type:
                self.logger.debug(f"Edge {edge.source_id} -[{edge.type}]-> {edge.target_id} already exists.")
                return

        self.edges[edge.source_id].append(edge)
        self.logger.debug(f"Added edge: {edge.to_dict()}")

    async def get_related_entities(self, entity_id: str, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves entities directly related to the given entity_id.
        Optionally filters by relationship type.
        """
        related_entities = []
        
        # Outgoing edges
        for edge in self.edges.get(entity_id, []):
            if relationship_type is None or edge.type == relationship_type:
                target_node = self.nodes.get(edge.target_id)
                if target_node:
                    related_entities.append({
                        "node": target_node.to_dict(),
                        "relationship": edge.to_dict()
                    })
        
        # Incoming edges (need to iterate all edges)
        for source_id, edges_list in self.edges.items():
            for edge in edges_list:
                if edge.target_id == entity_id and (relationship_type is None or edge.type == relationship_type):
                    source_node = self.nodes.get(edge.source_id)
                    if source_node and source_id != entity_id: # Avoid self-loops if source is same as target
                        related_entities.append({
                            "node": source_node.to_dict(),
                            "relationship": edge.to_dict()
                        })
        
        self.logger.debug(f"Found {len(related_entities)} related entities for '{entity_id}' (type: {relationship_type})")
        return related_entities

    async def enrich_event_with_graph_data(self, threat_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriches a threat event with contextual information by querying the knowledge graph.
        Adds new entities and relationships from the event to the graph if they don't exist.
        """
        enrichment_results = {"graph_enrichment_findings": []}

        event_id = threat_event.get("event_id", "N/A")
        self.logger.debug(f"Enriching event {event_id} with graph data.")

        # Extract key entities from the threat event and add/update them in the graph
        if "ip_address" in threat_event:
            ip_addr = threat_event["ip_address"]
            self.add_node(CKGNode(ip_addr, "IP", {"last_observed": threat_event.get("timestamp")}))
            
            # Check if IP is known malicious
            if self.nodes.get(ip_addr) and self.nodes[ip_addr].properties.get("reputation") == "bad":
                enrichment_results["graph_enrichment_findings"].append("Known malicious IP involved.")
                self.logger.info(f"Event {event_id}: Known malicious IP {ip_addr} identified.")
            
            # Find related entities for this IP
            for edge in self.edges.get(ip_addr, []):
                if edge.type == "USES" and self.nodes.get(edge.target_id) and self.nodes[edge.target_id].type == "Tool":
                    enrichment_results["graph_enrichment_findings"].append(f"IP {ip_addr} uses known tool: {edge.target_id}")
                if edge.type == "OPERATES_THROUGH" and self.nodes.get(edge.source_id) and self.nodes[edge.source_id].type == "ThreatActor":
                     enrichment_results["graph_enrichment_findings"].append(f"IP {ip_addr} linked to Threat Actor: {edge.source_id}")


        if "vulnerability" in threat_event: # e.g. if AI Analyzer identifies a CVE
            cve_id = threat_event["vulnerability"]
            self.add_node(CKGNode(cve_id, "Vulnerability", {"last_observed": threat_event.get("timestamp")}))
            if self.nodes.get(cve_id) and self.nodes[cve_id].properties.get("severity") == "high":
                enrichment_results["graph_enrichment_findings"].append(f"High severity vulnerability {cve_id} targeted.")
        
        # Example: Link event to asset if asset details are present
        if "target_asset" in threat_event:
            asset_id = threat_event["target_asset"]
            self.add_node(CKGNode(asset_id, "Asset", {"last_seen": threat_event.get("timestamp")}))
            if self.nodes.get(asset_id) and self.nodes[asset_id].properties.get("criticality") == "high":
                enrichment_results["graph_enrichment_findings"].append(f"Critical asset {asset_id} involved.")
        
        # Add relationships based on inferred context (if available)
        inferred_context = threat_event.get("inferred_context", [])
        if "Possible SSH brute-force attempt." in inferred_context and "ip_address" in threat_event:
            self.add_node(CKGNode("SSH_Brute_Force", "AttackType"))
            self.add_edge(CKGEdge(threat_event["ip_address"], "SSH_Brute_Force", "PERFORMS"))

        self.logger.debug(f"Event {event_id} enriched with: {enrichment_results['graph_enrichment_findings']}")
        return enrichment_results
