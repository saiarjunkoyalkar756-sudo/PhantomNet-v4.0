"""Canonical contracts shared across PhantomNet telemetry and detection components."""

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


CONTRACT_VERSION = "1.0.0"


class EventEnvelope(BaseModel):
    """A versioned, tenant-scoped event record with immutable correlation metadata."""

    schema_version: str = CONTRACT_VERSION
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    source: str
    event_type: str
    severity: Literal["informational", "low", "medium", "high", "critical"] = "informational"
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def payload_fingerprint(self) -> str:
        """Produce a deterministic fingerprint without asserting tamper-proof storage."""
        canonical = repr(sorted(self.payload.items())).encode("utf-8")
        return sha256(canonical).hexdigest()


class DetectionRule(BaseModel):
    """A governed, versioned detection definition with testable expected outcomes."""

    rule_id: str
    version: str
    name: str
    description: str
    enabled: bool = True
    event_types: List[str] = Field(default_factory=list)
    severity: Literal["informational", "low", "medium", "high", "critical"] = "medium"
    threshold: int = Field(default=1, ge=1)
    window_seconds: int = Field(default=300, ge=1)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    mitre_techniques: List[str] = Field(default_factory=list)
    expected_outcome: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if value.count(".") < 1:
            raise ValueError("rule version must be a dotted version string")
        return value


class DetectionRecord(BaseModel):
    """A versioned, tenant-scoped detection result produced from a canonical event."""

    schema_version: str = CONTRACT_VERSION
    detection_id: str = Field(default_factory=lambda: str(uuid4()))
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rule_id: str
    rule_version: str
    event_id: str
    tenant_id: str
    correlation_id: Optional[str] = None
    severity: Literal["informational", "low", "medium", "high", "critical"]
    title: str
    status: Literal["detected", "suppressed"] = "detected"
    evidence: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    automatic_enforcement: bool = False

    @field_validator("detected_at")
    @classmethod
    def require_timezone_aware_detected_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
