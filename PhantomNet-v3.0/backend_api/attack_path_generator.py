# backend_api/attack_path_generator.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import random
import uuid

class AttackPathNode(BaseModel):
    id: str = Field(..., description="Unique identifier for the node")
    name: str = Field(..., description="Display name of the node (e.g., Asset Name, Vulnerability Name)")
    type: str = Field(..., description="Type of node (e.g., 'asset', 'vulnerability', 'exploit', 'entry_point')")
    risk_score: Optional[int] = Field(None, ge=0, le=100, description="Risk score associated with the node")
    description: Optional[str] = Field(None, description="Detailed description of the node")
    properties: Dict[str, Any] = Field({}, description="Additional properties of the node")

class AttackPathEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the edge")
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    relationship: str = Field(..., description="Description of the relationship (e.g., 'exploits', 'has_vulnerability', 'leads_to')")
    risk_factor: Optional[float] = Field(None, ge=0, le=1.0, description="Factor contributing to overall path risk")

class AttackPathGraph(BaseModel):
    nodes: List[AttackPathNode] = []
    edges: List[AttackPathEdge] = []
    summary: Optional[str] = Field(None, description="Summary of the attack path")
    overall_risk: Optional[float] = Field(None, ge=0, le=1.0, description="Calculated overall risk of this path")

def generate_simulated_attack_path(depth: int = 3) -> AttackPathGraph:
    """
    Generates a simulated attack path graph.
    """
    nodes: List[AttackPathNode] = []
    edges: List[AttackPathEdge] = []

    # Starting node (Entry Point)
    entry_point_node = AttackPathNode(
        id="EP1",
        name="Internet Exposure",
        type="entry_point",
        risk_score=80,
        description="Publicly accessible web server via internet."
    )
    nodes.append(entry_point_node)

    current_nodes = [entry_point_node]
    for i in range(depth):
        next_nodes = []
        for c_node in current_nodes:
            # Add a vulnerability if current is an entry_point or asset
            if c_node.type in ["entry_point", "asset"]:
                vuln_id = f"VULN-{uuid.uuid4().hex[:4]}"
                vulnerability_node = AttackPathNode(
                    id=vuln_id,
                    name=f"CVE-2023-{random.randint(1000, 9999)}",
                    type="vulnerability",
                    risk_score=random.randint(50, 95),
                    description=f"Known vulnerability affecting {c_node.name}",
                    properties={"CVE_ID": vuln_id}
                )
                nodes.append(vulnerability_node)
                edges.append(AttackPathEdge(source=c_node.id, target=vulnerability_node.id, relationship="has_vulnerability"))
                next_nodes.append(vulnerability_node)

                # Add an exploit for the vulnerability
                exploit_id = f"EXP-{uuid.uuid4().hex[:4]}"
                exploit_node = AttackPathNode(
                    id=exploit_id,
                    name=f"Exploit for {vulnerability_node.name}",
                    type="exploit",
                    risk_score=random.randint(70, 99),
                    description="Automated exploit available.",
                    properties={"tool": random.choice(["Metasploit", "Custom Script"])}
                )
                nodes.append(exploit_node)
                edges.append(AttackPathEdge(source=vulnerability_node.id, target=exploit_node.id, relationship="exploited_by"))
                next_nodes.append(exploit_node)
            
            # Add a new asset that can be reached from the current node
            if c_node.type in ["exploit", "asset", "entry_point"]:
                asset_id = f"ASSET-{uuid.uuid4().hex[:4]}"
                asset_type = random.choice(["WebServer", "Database", "Internal Server", "Workstation"])
                asset_node = AttackPathNode(
                    id=asset_id,
                    name=f"{asset_type}-{random.randint(1, 100)}",
                    type="asset",
                    risk_score=random.randint(10, 80),
                    description=f"Internal {asset_type} instance.",
                    properties={"IP": f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"}
                )
                nodes.append(asset_node)
                edges.append(AttackPathEdge(source=c_node.id, target=asset_node.id, relationship=random.choice(["leads_to", "accesses", "pivot_to"])))
                next_nodes.append(asset_node)
        current_nodes = next_nodes

    # Calculate a simple overall risk and summary
    overall_risk = sum([n.risk_score for n in nodes if n.risk_score is not None]) / len(nodes) if nodes else 0
    summary = f"Simulated attack path with {len(nodes)} nodes and {len(edges)} edges. Overall estimated risk: {overall_risk:.2f}%"

    return AttackPathGraph(nodes=nodes, edges=edges, summary=summary, overall_risk=round(overall_risk/100, 2))

if __name__ == "__main__":
    print("--- Generating Simulated Attack Path ---")
    simulated_graph = generate_simulated_attack_path(depth=4)
    print(json.dumps(simulated_graph.dict(), indent=2))
    print("\nTotal Nodes:", len(simulated_graph.nodes))
    print("Total Edges:", len(simulated_graph.edges))
    print("Overall Risk:", simulated_graph.overall_risk)
