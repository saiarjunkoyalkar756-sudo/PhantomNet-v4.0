# schemas/config_schema.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Any, List, Optional

class BusConfig(BaseModel):
    type: str
    kafka: Optional[Dict[str, Any]] = None
    redis: Optional[Dict[str, Any]] = None
    http: Optional[Dict[str, Any]] = None

class CollectorConfig(BaseModel, extra='allow'):
    enabled: bool = True
    interval_seconds: Optional[int] = None
    paths: Optional[List[str]] = None # For file collector
    files: Optional[List[str]] = None # For log collector

class PluginsConfig(BaseModel):
    enabled: bool = True
    paths: List[str] = []
    allowed_permissions: List[str] = []

class SecurityConfig(BaseModel):
    tls: Optional[Dict[str, Any]] = None
    verify_config_signature: bool = False

class AgentConfig(BaseModel):
    id: str = Field(default_factory=lambda: "agent-autogen")
    mode: str = "full"
    backend_env: str = "dev"
    log_level: str = "INFO"
    manager_url: Optional[HttpUrl] = None
    bus: BusConfig
    collectors: Dict[str, CollectorConfig] = {}
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    heartbeat_interval: int = 30
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    # New fields for cross-platform and safety controls
    platform_override: Optional[str] = None # For testing or forcing a platform
    enable_ebpf: Optional[bool] = None # Explicitly enable/disable eBPF features
    enable_pcap: Optional[bool] = None # Explicitly enable/disable pcap features
    force_admin_warn: Optional[bool] = None # Force warning if not running as admin
    safe_mode: bool = False # Overall safe mode (replaces safe_ai_mode)


# Top-level configuration for the entire agent
class PhantomNetAgentConfig(BaseModel):
    agent: AgentConfig
