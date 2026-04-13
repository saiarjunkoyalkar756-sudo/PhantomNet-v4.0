# backend_api/asset_inventory_service/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field


class Asset(BaseModel):
    """
    Represents a single asset in the organizational inventory.
    """

    asset_id: str = Field(
        ...,
        description="The unique identifier for the asset (e.g., hostname, serial number, or service name).",
    )
    asset_type: str = Field(
        ...,
        description="The type of the asset (e.g., 'endpoint', 'service', 'database', 'network_device').",
    )
    owner: str = Field(
        ...,
        description="The business unit or department that owns the asset.",
    )
    criticality: int = Field(
        ...,
        ge=1,
        le=10,
        description="The business criticality score of the asset, from 1 (low) to 10 (critical).",
    )

    class Config:
        from_attributes = True
