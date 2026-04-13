from pydantic import BaseModel, Field
import datetime
from typing import Literal

class NetworkBlockchainRecord(BaseModel):
    """
    Schema for a tamper-proof network security event recorded on the blockchain.
    """
    record_id: str = Field(..., description="Unique identifier for the record")
    timestamp: datetime.datetime = Field(..., description="Timestamp of the event")
    event_type: Literal["network_alert", "segmentation_violation", "firewall_action"] = Field(..., description="Type of network event")
    
    source_ip: Optional[str] = Field(None, description="Source IP address involved in the event")
    destination_ip: Optional[str] = Field(None, description="Destination IP address involved in the event")
    
    description: str = Field(..., description="Detailed description of the event")
    
    agent_id: str = Field(..., description="Identifier of the agent reporting the event")
    policy_id: Optional[str] = Field(None, description="Identifier of the policy that was violated or triggered the action")
    
    signature: str = Field(..., description="Digital signature to ensure integrity of the record")
