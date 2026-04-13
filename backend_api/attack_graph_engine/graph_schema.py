from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid

class GraphNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the node.")
    node_type: str = Field(..., example="asset", description="Type of the node (e.g., 'asset', 'user', 'vulnerability', 'attack_technique').")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs describing the node (e.g., {'name': 'server-prod-01', 'os': 'Linux'}).")

class GraphEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the edge.")
    source_node_id: str = Field(..., description="ID of the source node.")
    target_node_id: str = Field(..., description="ID of the target node.")
    edge_type: str = Field(..., example="has_vulnerability", description="Type of the relationship (e.g., 'connects_to', 'has_vulnerability', 'exploits').")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Key-value pairs describing the edge (e.g., {'port': 22, 'protocol': 'ssh'}).")

class GraphUpdate(BaseModel):
    nodes_to_add: List[GraphNode] = Field(default_factory=list)
    edges_to_add: List[GraphEdge] = Field(default_factory=list)
    nodes_to_remove: List[str] = Field(default_factory=list) # List of node IDs
    edges_to_remove: List[str] = Field(default_factory=list) # List of edge IDs

class AttackGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
