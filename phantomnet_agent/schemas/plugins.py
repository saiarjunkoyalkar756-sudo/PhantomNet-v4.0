from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PluginManifest(BaseModel):
    name: str
    version: str
    description: str
    phantomnet_agent_version: str = "0.0.1" # Version of the agent it's compatible with
    entry: str # "module_name:function_name" or "module_name:ClassName"
    permissions: List[str] = Field(default_factory=list) # e.g., ["network:scan", "filesystem:read"]
    config_schema: Optional[Dict[str, Any]] = None # Optional Pydantic schema for plugin-specific config
