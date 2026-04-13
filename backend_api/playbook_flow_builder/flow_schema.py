from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import datetime

class Node(BaseModel):
    id: str = Field(..., description="Unique identifier for the node.")
    type: str = Field(..., description="Type of the node (e.g., 'start', 'action', 'condition', 'end', 'approval').")
    data: Dict[str, Any] = Field(default_factory=dict, description="Custom data associated with the node (e.g., action details, condition logic).")
    position: Optional[Dict[str, float]] = Field(None, description="Visual position of the node for frontend rendering {x, y}.")

class Edge(BaseModel):
    id: str = Field(..., description="Unique identifier for the edge.")
    source: str = Field(..., description="ID of the source node.")
    target: str = Field(..., description="ID of the target node.")
    sourceHandle: Optional[str] = Field(None, description="Optional: Identifier for the source handle on the source node.")
    targetHandle: Optional[str] = Field(None, description="Optional: Identifier for the target handle on the target node.")
    label: Optional[str] = Field(None, description="Optional: Label for the edge (e.g., 'true', 'false').")
    animated: bool = Field(False, description="Whether the edge should be animated in the UI.")

class PlaybookFlow(BaseModel):
    name: str = Field(..., description="Name of the playbook flow.")
    description: Optional[str] = Field(None, description="Description of the playbook flow.")
    nodes: List[Node] = Field(..., description="List of nodes in the playbook flow.")
    edges: List[Edge] = Field(..., description="List of edges connecting nodes in the playbook flow.")
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    # Example of how steps could be defined within `data` for an 'action' node:
    # {
    #     "type": "action",
    #     "data": {
    #         "action_type": "isolate_host",
    #         "parameters": {
    #             "host_id_key": "input.host_id" # dynamic value from input or previous step
    #         }
    #     }
    # }
    
    # Example of how conditions could be defined within `data` for a 'condition' node:
    # {
    #     "type": "condition",
    #     "data": {
    #         "condition_logic": "status == 'malicious'",
    #         "true_path_id": "node_id_if_true",
    #         "false_path_id": "node_id_if_false"
    #     }
    # }