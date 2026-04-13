from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

class NetworkBlockchainRecord(BaseModel):
    """Schema for network-related records to be stored on the blockchain."""
    record_id: str = Field(..., description="Unique identifier for this blockchain record.")
    agent_id: str = Field(..., description="Unique identifier of the PhantomNet agent involved.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the record was created (UTC).")
    event_type: str = Field(..., description="Type of network event leading to this record (e.g., 'network_alert', 'segmentation_violation', 'firewall_action').")
    event_id: Optional[str] = Field(None, description="Optional: ID of the original network event, if applicable.")
    severity: Optional[str] = Field(None, description="Severity of the event (e.g., 'low', 'medium', 'high', 'critical').")
    action_taken: Optional[str] = Field(None, description="Description of the action taken (e.g., 'IP blocked', 'host isolated', 'alert generated').")
    action_details: Optional[Any] = Field(None, description="Detailed parameters of the action taken (e.g., firewall rule, isolation policy).")
    relevant_ips: Optional[list[str]] = Field(None, description="List of IP addresses relevant to this event.")
    # Add fields to store hashes of related data for tamper-proofing
    network_event_hash: Optional[str] = Field(None, description="SHA256 hash of the original NetworkEvent data.")
    previous_record_hash: Optional[str] = Field(None, description="Hash of the previous related blockchain record, for chaining.")
    # Consider adding a digital signature from the agent/backend that created the record
    signature: Optional[str] = Field(None, description="Digital signature of the record content for authenticity.")
    public_key: Optional[str] = Field(None, description="Public key used for the signature.")

