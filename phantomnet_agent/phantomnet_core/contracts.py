"""Canonical contracts shared across PhantomNet telemetry, detection, and analyst workflows."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


CONTRACT_VERSION = "1.0.0"
MITRE_TECHNIQUE_PATTERN = re.compile(r"^T\d{4}(?:\.\d{3})?$")


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


class MitreEvidence(BaseModel):
    """A bounded, analyst-readable ATT&CK mapping produced by a governed rule."""

    technique_id: str
    tactic: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    evidence_fields: List[str] = Field(default_factory=list)

    @field_validator("technique_id")
    @classmethod
    def validate_technique_id(cls, value: str) -> str:
        normalized = value.upper()
        if not MITRE_TECHNIQUE_PATTERN.fullmatch(normalized):
            raise ValueError("MITRE technique_id must use T#### or T####.### format")
        return normalized


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
    mitre_tactics: List[str] = Field(default_factory=list)
    expected_outcome: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        if value.count(".") < 1:
            raise ValueError("rule version must be a dotted version string")
        return value

    @field_validator("mitre_techniques")
    @classmethod
    def validate_mitre_techniques(cls, values: List[str]) -> List[str]:
        normalized = [value.upper() for value in values]
        invalid = [value for value in normalized if not MITRE_TECHNIQUE_PATTERN.fullmatch(value)]
        if invalid:
            raise ValueError("MITRE techniques must use T#### or T####.### format")
        return normalized


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
    mitre_evidence: List[MitreEvidence] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    automatic_enforcement: bool = False

    @field_validator("detected_at")
    @classmethod
    def require_timezone_aware_detected_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class AlertRecord(BaseModel):
    """Tenant-scoped analyst workflow state derived from one or more governed detections."""

    schema_version: str = CONTRACT_VERSION
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    detection_ids: List[str] = Field(min_length=1)
    correlation_id: Optional[str] = None
    title: str
    severity: Literal["informational", "low", "medium", "high", "critical"]
    status: Literal["new", "triaged", "in_progress", "resolved", "closed", "suppressed"] = "new"
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    occurrence_count: int = Field(default=1, ge=1)
    suppression_key: str
    suppressed_by_alert_id: Optional[str] = None
    mitre_evidence: List[MitreEvidence] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    case_id: Optional[str] = None
    triaged_by: Optional[str] = None

    @field_validator("first_seen", "last_seen")
    @classmethod
    def require_timezone_aware_alert_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
