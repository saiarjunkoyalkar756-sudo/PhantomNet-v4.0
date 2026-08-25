# backend_api/shared/database.py
import os
import datetime
import uuid
import sys
from typing import Dict, Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    UniqueConstraint,
    event,
    inspect,
    text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as pgUUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.ext.compiler import compiles

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"

class UUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type, otherwise CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def __init__(self, as_uuid=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.as_uuid = as_uuid

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pgUUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            # Try parsing as standard string format first
            return uuid.UUID(str(value))
        except ValueError:
            # Fall back to parsing as integer in case SQLite stored it as integer
            return uuid.UUID(int=int(value))

from backend_api.shared.settings import settings
DATABASE_URL = settings.DATABASE_URL

# Async engine with connection pooling
if "sqlite" in DATABASE_URL:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create a synchronous engine and session factory (SessionLocal) for synchronous/legacy operations
sync_db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")
if "sqlite" in sync_db_url:
    sync_engine = create_engine(
        sync_db_url
    )
else:
    sync_engine = create_engine(
        sync_db_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

# --- Models ---

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    is_active = Column(Boolean, default=True)

DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, default=DEFAULT_TENANT_ID)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
    twofa_enforced = Column(Boolean, default=False)
    totp_secret = Column(String, nullable=True)
    webauthn_enabled = Column(Boolean, default=False)
    trust_score = Column(Float, default=100.0)
    bio_baseline = Column(JSONB, nullable=True)

class SessionToken(Base):
    __tablename__ = "session_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)
    ip = Column(String)
    user_agent = Column(String)
    device_fingerprint = Column(String, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    city = Column(String, nullable=True)
    region = Column(String, nullable=True)
    country = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    issued_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime)
    used_at = Column(DateTime, nullable=True)
    ip_request = Column(String)
    ip_use = Column(String, nullable=True)

class AttackLog(Base):
    __tablename__ = "attack_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    ip = Column(String)
    port = Column(Integer)
    data = Column(String)
    attack_type = Column(String)
    confidence_score = Column(Float)
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float)
    is_verified_threat = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)

class BlacklistedIP(Base):
    __tablename__ = "blacklisted_ips"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, index=True)
    reason = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class RecoveryCode(Base):
    __tablename__ = "recovery_codes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    code_hash = Column(String, nullable=False)
    used_at = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, nullable=False)
    alert_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    event_data = Column(JSONB)

class NormalizedEvent(Base):
    __tablename__ = "normalized_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    details = Column(JSONB)

class DetectionRecordRow(Base):
    """Durable canonical detection evidence created from normalized event delivery."""
    __tablename__ = "detection_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "event_id", "rule_id", name="uq_detection_record_event_rule"),
    )

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    rule_id = Column(String, nullable=False, index=True)
    rule_version = Column(String, nullable=False)
    correlation_id = Column(String, nullable=True, index=True)
    severity = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="detected")
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    evidence = Column(JSONB, nullable=False)
    mitre_evidence = Column(JSONB, nullable=False)
    tags = Column(JSONB, nullable=False)
    automatic_enforcement = Column(Boolean, nullable=False, default=False)


class AnalystAlertRow(Base):
    """Durable analyst workflow derived from one or more canonical detections."""
    __tablename__ = "analyst_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    detection_ids = Column(JSONB, nullable=False)
    correlation_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="new", index=True)
    first_seen = Column(DateTime(timezone=True), nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=False, index=True)
    occurrence_count = Column(Integer, nullable=False, default=1)
    suppression_key = Column(String, nullable=False, index=True)
    suppressed_by_alert_id = Column(String, nullable=True)
    mitre_evidence = Column(JSONB, nullable=False)
    evidence = Column(JSONB, nullable=False)
    case_id = Column(String, nullable=True, index=True)
    triaged_by = Column(String, nullable=True)


class InvestigationCaseRow(Base):
    """Durable analyst investigation lifecycle linked to tenant-owned alerts."""
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    alert_ids = Column(JSONB, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="new", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_by = Column(String, nullable=False)
    assigned_to = Column(String, nullable=True)
    evidence = Column(JSONB, nullable=False)
    timeline = Column(JSONB, nullable=False)


class CasePlaybookRunRow(Base):
    """Durable non-executing playbook lifecycle evidence for one investigation case."""
    __tablename__ = "case_playbook_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    case_id = Column(String, ForeignKey("investigation_cases.case_id"), nullable=False, index=True)
    playbook_id = Column(String, nullable=False)
    playbook_version = Column(String, nullable=False)
    status = Column(String, nullable=False, default="requested", index=True)
    requires_approval = Column(Boolean, nullable=False, default=True)
    requested_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    evidence = Column(JSONB, nullable=False)


class SavedHuntRow(Base):
    """A tenant-owned, structured hunt definition with no executable query text."""
    __tablename__ = "saved_hunts"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_saved_hunt_tenant_name"),)

    id = Column(Integer, primary_key=True, index=True)
    hunt_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    dataset = Column(String, nullable=False)
    filters = Column(JSONB, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, index=True)


class EndpointAssetRow(Base):
    """Current endpoint inventory state reported by a trusted agent or read-only integration."""
    __tablename__ = "endpoint_assets"
    __table_args__ = (UniqueConstraint("tenant_id", "agent_id", name="uq_endpoint_asset_tenant_agent"),)

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    hostname = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)
    os_version = Column(String, nullable=True)
    ip_addresses = Column(JSONB, nullable=False)
    software = Column(JSONB, nullable=False)
    tags = Column(JSONB, nullable=False)
    source = Column(String, nullable=False)
    last_seen = Column(DateTime(timezone=True), nullable=False, index=True)
    evidence = Column(JSONB, nullable=False)


class HostIntegrityObservationRow(Base):
    """Append-only endpoint integrity evidence; ingestion does not execute host actions."""
    __tablename__ = "host_integrity_observations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source", "source_event_id", name="uq_integrity_source_event"),
    )

    id = Column(Integer, primary_key=True, index=True)
    observation_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    asset_id = Column(String, ForeignKey("endpoint_assets.asset_id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    source_event_id = Column(String, nullable=False)
    source = Column(String, nullable=False)
    check_type = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    path = Column(String, nullable=True)
    observed_hash = Column(String, nullable=True)
    expected_hash = Column(String, nullable=True)
    evidence = Column(JSONB, nullable=False)
    automatic_enforcement = Column(Boolean, nullable=False, default=False)


class IntegratedEvidenceRow(Base):
    """Durable tenant-owned read-only evidence with explicit adapter provenance."""

    __tablename__ = "integrated_evidence"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_kind",
            "source_name",
            "source_record_id",
            "payload_fingerprint",
            name="uq_integrated_evidence_source_fingerprint",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    source_kind = Column(String, nullable=False, index=True)
    source_name = Column(String, nullable=False, index=True)
    source_record_id = Column(String, nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    collected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    tags = Column(JSONB, nullable=False)
    provenance = Column(JSONB, nullable=False)
    payload_fingerprint = Column(String(64), nullable=False, index=True)
    read_only = Column(Boolean, nullable=False, default=True)
    automatic_enforcement = Column(Boolean, nullable=False, default=False)


class WazuhForwarderRow(Base):
    """Tenant-bound read-only forwarder registration; only a token digest is stored."""
    __tablename__ = "wazuh_forwarders"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_wazuh_forwarder_tenant_name"),)

    id = Column(Integer, primary_key=True, index=True)
    forwarder_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    token_digest = Column(String, nullable=False)
    token_prefix = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active", index=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_sequence = Column(Integer, nullable=False, default=0)


class WazuhForwarderBatchRow(Base):
    """Replay-protection receipt for one ordered telemetry batch."""
    __tablename__ = "wazuh_forwarder_batches"
    __table_args__ = (
        UniqueConstraint("forwarder_id", "sequence", name="uq_wazuh_forwarder_sequence"),
        UniqueConstraint("forwarder_id", "batch_id", name="uq_wazuh_forwarder_batch"),
    )

    id = Column(Integer, primary_key=True, index=True)
    forwarder_id = Column(String, ForeignKey("wazuh_forwarders.forwarder_id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    batch_id = Column(String, nullable=False)
    sequence = Column(Integer, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False, index=True)
    alert_count = Column(Integer, nullable=False)


class WazuhResponseReceiptRow(Base):
    """Signed endpoint receipt used to prove a named Wazuh Active Response outcome."""
    __tablename__ = "wazuh_response_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nonce", name="uq_wazuh_response_receipt_tenant_nonce"),
    )

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    request_id = Column(String, ForeignKey("containment_requests.request_id"), nullable=False, index=True)
    approval_id = Column(String, ForeignKey("containment_approvals.approval_id"), nullable=False, index=True)
    asset_id = Column(String, nullable=False, index=True)
    wazuh_agent_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    network_state = Column(String, nullable=False, index=True)
    command_fingerprint = Column(String(length=64), nullable=False, index=True)
    nonce = Column(String, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), nullable=False, index=True)
    signature = Column(String, nullable=False)
    signature_key_id = Column(String, nullable=False)


class ContainmentRequestRow(Base):
    """High-impact response intent; execution is impossible until a separate approval exists."""
    __tablename__ = "containment_requests"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_containment_tenant_idempotency"),)

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False, index=True)
    asset_id = Column(String, nullable=True, index=True)
    playbook_id = Column(String, nullable=True)
    requested_by = Column(String, nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String, nullable=False, default="requested", index=True)
    idempotency_key = Column(String, nullable=False)
    parameters = Column(JSONB, nullable=False)
    requires_approval = Column(Boolean, nullable=False, default=True)
    automatic_enforcement = Column(Boolean, nullable=False, default=False)


class ContainmentApprovalRow(Base):
    __tablename__ = "containment_approvals"

    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(String, unique=True, nullable=False, index=True)
    request_id = Column(String, ForeignKey("containment_requests.request_id"), nullable=False, unique=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    decision = Column(String, nullable=False)
    decided_by = Column(String, nullable=False)
    decided_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(String, nullable=False)


class ContainmentExecutionRow(Base):
    __tablename__ = "containment_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String, unique=True, nullable=False, index=True)
    request_id = Column(String, ForeignKey("containment_requests.request_id"), nullable=False, unique=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    approval_id = Column(String, ForeignKey("containment_approvals.approval_id"), nullable=False)
    adapter = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    verification = Column(JSONB, nullable=False)
    rollback_available = Column(Boolean, nullable=False, default=False)
    rolled_back = Column(Boolean, nullable=False, default=False)
    audit_record_hash = Column(String, nullable=True)


class ContainmentAuditRecordRow(Base):
    """Per-tenant chained audit evidence for containment lifecycle events."""
    __tablename__ = "containment_audit_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    record_id = Column(String, unique=True, nullable=False, index=True)
    timestamp = Column(String, nullable=False)
    actor_id = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    previous_hash = Column(String, nullable=False)
    record_hash = Column(String, nullable=False, unique=True)
    signature = Column(String, nullable=True)
    signature_key_id = Column(String, nullable=True)


@event.listens_for(ContainmentAuditRecordRow, "before_update")
def _reject_containment_audit_update(_mapper, _connection, _target) -> None:
    raise RuntimeError("Containment audit records are immutable and cannot be updated through the application ORM.")


@event.listens_for(ContainmentAuditRecordRow, "before_delete")
def _reject_containment_audit_delete(_mapper, _connection, _target) -> None:
    raise RuntimeError("Containment audit records are immutable and cannot be deleted through the application ORM.")


class ForensicRecord(Base):
    __tablename__ = "forensic_records"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String, unique=True, nullable=False)
    tool_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    results = Column(JSONB)

class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, unique=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    previous_hash = Column(String, nullable=False)
    block_hash = Column(String, unique=True, nullable=False)
    proof = Column(Integer, nullable=False)
    merkle_root = Column(String, nullable=True)

    transactions = relationship("Transaction", back_populates="block", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
            "proof": self.proof,
            "merkle_root": self.merkle_root,
            "transactions": [tx.to_dict() for tx in self.transactions],
        }

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    data = Column(JSONB, nullable=True)
    attack_type = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    normalized_event_id = Column(Integer, ForeignKey("normalized_events.id"), nullable=True)
    forensic_record_id = Column(Integer, ForeignKey("forensic_records.id"), nullable=True)
    data_type = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    transaction_hash = Column(String, unique=True, nullable=False)

    block = relationship("Block", back_populates="transactions")
    alert = relationship("Alert")
    normalized_event = relationship("NormalizedEvent")
    forensic_record = relationship("ForensicRecord")

    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "data": self.data,
            "attack_type": self.attack_type,
            "confidence_score": self.confidence_score,
            "alert_id": self.alert_id,
            "normalized_event_id": self.normalized_event_id,
            "forensic_record_id": self.forensic_record_id,
            "data_type": self.data_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "transaction_hash": self.transaction_hash,
        }

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    public_key = Column(String, unique=True, nullable=False)
    public_key_fingerprint = Column(String, nullable=False)
    cert_serial = Column(String, nullable=False)
    role = Column(String, nullable=False)
    version = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    quarantined = Column(Boolean, default=True)
    configuration = Column(JSONB, nullable=True)
    os = Column(String, nullable=True)
    capabilities = Column(JSONB, nullable=True)
    last_reported_health = Column(JSONB, nullable=True)
    last_reported_errors = Column(JSONB, nullable=True)
    available_patches = Column(JSONB, nullable=True)
    last_patch_applied = Column(DateTime, nullable=True)
    self_healing_enabled = Column(Boolean, default=False)
    safe_mode_active = Column(Boolean, default=False)

class AgentCredential(Base):
    __tablename__ = "agent_credentials"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    public_key_pem = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    rotated_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

class RevokedCertificate(Base):
    __tablename__ = "revoked_certificates"
    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String, unique=True, index=True, nullable=False)
    revocation_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    reason = Column(String)

class PhantomChainDB(Base):
    __tablename__ = "phantom_chain"
    block_index = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    data = Column(String, nullable=False)
    previous_hash = Column(String, nullable=False)
    hash = Column(String, unique=True, nullable=False)

class PlaybookDB(Base):
    __tablename__ = "soar_playbooks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    trigger = Column(JSONB, nullable=False)
    steps = Column(JSONB, nullable=False)
    context = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class PlaybookRunDB(Base):
    __tablename__ = "soar_playbook_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    playbook_id = Column(Integer, ForeignKey("soar_playbooks.id"), nullable=False)
    playbook_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    triggered_by = Column(JSONB, nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    end_time = Column(DateTime, nullable=True)
    current_context = Column(JSONB, nullable=False)
    
    playbook = relationship("PlaybookDB", backref="runs")
    execution_logs = relationship("PlaybookExecutionLogDB", back_populates="playbook_run", cascade="all, delete-orphan")

class PlaybookExecutionLogDB(Base):
    __tablename__ = "soar_playbook_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    playbook_run_id = Column(String, ForeignKey("soar_playbook_runs.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    step_action = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)
    output = Column(JSONB, nullable=True)

    playbook_run = relationship("PlaybookRunDB", back_populates="execution_logs")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get an async database session.
    Features automatic reconnect with exponential backoff on database down.
    """
    import asyncio
    env = os.getenv("ENVIRONMENT", "development").lower()
    max_attempts = 1 if env == "testing" else 5
    backoff = 0.5
    session = None
    for attempt in range(max_attempts):
        try:
            session = AsyncSessionLocal()
            await session.execute(text("SELECT 1"))
            break
        except Exception:
            if session:
                await session.close()
            if attempt == 4:
                raise
            await asyncio.sleep(backoff)
            backoff *= 2
            
    async with session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            from fastapi import HTTPException
            if isinstance(e, HTTPException):
                raise
            await session.rollback()
            raise
        finally:
            await session.close()


def create_db_and_tables(engine_obj=None):
    """
    Creates all tables in the database.
    Supports both synchronous and asynchronous engines.
    """
    if engine_obj is None:
        engine_obj = sync_engine
        
    from sqlalchemy.ext.asyncio import AsyncEngine
    if isinstance(engine_obj, AsyncEngine):
        import asyncio
        async def _create_async():
            async with engine_obj.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_create_async())
            else:
                loop.run_until_complete(_create_async())
        except Exception:
            pass
    else:
        Base.metadata.create_all(bind=engine_obj)


# Test database engine and session factory for testing backward compatibility
test_db_url = "sqlite:///./test.db"
test_engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class IngestionDeadLetterRow(Base):
    """Durable broker failure evidence keyed by one source delivery; replay is always explicit."""

    __tablename__ = "ingestion_dead_letters"
    __table_args__ = (
        UniqueConstraint("topic", "partition", "offset", name="uq_ingestion_dead_letter_delivery"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dead_letter_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True, index=True)
    event_id = Column(String, nullable=True, index=True)
    topic = Column(String, nullable=False)
    partition = Column(Integer, nullable=False)
    offset = Column(Integer, nullable=False)
    message_hash = Column(String, nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    error_code = Column(String, nullable=False, index=True)
    error_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open", index=True)
    attempt_count = Column(Integer, nullable=False, default=1)
    first_failed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_failed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    replayed_at = Column(DateTime(timezone=True), nullable=True)
    replayed_by = Column(String, nullable=True)


class GovernedCorrelationRuleRow(Base):
    """Tenant-owned deterministic correlation rule; no response action is persisted here."""

    __tablename__ = "governed_correlation_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_governed_correlation_rule_tenant_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    version = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    event_types = Column(JSONB, nullable=False)
    predicates = Column(JSONB, nullable=False)
    severity = Column(String, nullable=False, index=True)
    mitre_techniques = Column(JSONB, nullable=False)
    mitre_tactics = Column(JSONB, nullable=False)
    correlation_key_fields = Column(JSONB, nullable=False)
    threshold = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    suppression_window_seconds = Column(Integer, nullable=False, default=900)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, index=True)


class GovernedCorrelationRuleRevisionRow(Base):
    """Immutable governed-correlation snapshot retained for analyst review and reproducible tests."""

    __tablename__ = "governed_correlation_rule_revisions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rule_id", "version", name="uq_governed_correlation_rule_revision_version"),
    )

    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    rule_id = Column(String, ForeignKey("governed_correlation_rules.rule_id"), nullable=False, index=True)
    version = Column(String, nullable=False)
    definition_fingerprint = Column(String(64), nullable=False, index=True)
    definition = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)


class CorrelationMatchEvidenceRow(Base):
    """One idempotent event-to-rule match used for bounded correlation threshold evidence."""

    __tablename__ = "correlation_match_evidence"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rule_id", "event_id", name="uq_correlation_match_event"),
    )

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    rule_id = Column(String, ForeignKey("governed_correlation_rules.rule_id"), nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    correlation_key = Column(String, nullable=False, index=True)
    matched_predicates = Column(JSONB, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    detection_id = Column(String, nullable=True, index=True)


class ResponseAutomationPolicyRow(Base):
    """Policy that creates approval-required containment requests; it never executes an adapter."""

    __tablename__ = "response_automation_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_response_automation_policy_tenant_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    trigger_rule_ids = Column(JSONB, nullable=False)
    minimum_severity = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target = Column(String, nullable=False)
    asset_id = Column(String, nullable=True)
    parameters = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class AutonomousDefensePolicyRow(Base):
    """Tenant-owned authority policy for evidence-grounded autonomous defense decisions."""

    __tablename__ = "autonomous_defense_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_autonomous_defense_policy_tenant_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    trigger_rule_ids = Column(JSONB, nullable=False)
    minimum_severity = Column(String, nullable=False)
    decision_mode = Column(String, nullable=False, index=True)
    minimum_confidence = Column(Float, nullable=False)
    minimum_evidence_count = Column(Integer, nullable=False)
    required_evidence_kinds = Column(JSONB, nullable=False)
    cooldown_seconds = Column(Integer, nullable=False)
    max_decisions_per_hour = Column(Integer, nullable=False)
    containment_action = Column(String, nullable=True)
    target = Column(String, nullable=True)
    asset_id = Column(String, nullable=True)
    parameters = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class AutonomousDefenseDecisionRow(Base):
    """Immutable evidence-grounded decision record; no row represents adapter execution."""

    __tablename__ = "autonomous_defense_decisions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "policy_id", "detection_id", "decision_hash", name="uq_autonomous_defense_decision"),
    )

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    policy_id = Column(String, ForeignKey("autonomous_defense_policies.policy_id"), nullable=False, index=True)
    detection_id = Column(String, nullable=False, index=True)
    rule_id = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    decision_mode = Column(String, nullable=False, index=True)
    outcome = Column(String, nullable=False, index=True)
    evidence_ids = Column(JSONB, nullable=False)
    evidence_kinds = Column(JSONB, nullable=False)
    reasons = Column(JSONB, nullable=False)
    containment_request_id = Column(String, nullable=True, index=True)
    requires_human_approval = Column(Boolean, nullable=False, default=True)
    decision_hash = Column(String, nullable=False, index=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, index=True)


@event.listens_for(AutonomousDefenseDecisionRow, "before_update")
def _reject_autonomous_decision_update(_mapper, _connection, _target) -> None:
    raise RuntimeError("Autonomous defense decisions are immutable and cannot be updated through the application ORM.")


@event.listens_for(AutonomousDefenseDecisionRow, "before_delete")
def _reject_autonomous_decision_delete(_mapper, _connection, _target) -> None:
    raise RuntimeError("Autonomous defense decisions are immutable and cannot be deleted through the application ORM.")


class DefensiveDatasetSourceRow(Base):
    """Operator-approved provenance for a sanitized defensive dataset source."""

    __tablename__ = "defensive_dataset_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "source_fingerprint", name="uq_defensive_dataset_source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False, index=True)
    source_uri = Column(String, nullable=True)
    source_fingerprint = Column(String(64), nullable=False, index=True)
    license_reference = Column(String, nullable=True)
    operator_approved = Column(Boolean, nullable=False, default=False)
    license_reviewed = Column(Boolean, nullable=False, default=False)
    sanitization_attested = Column(Boolean, nullable=False, default=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DefensiveDatasetVersionRow(Base):
    """Versioned sanitized corpus metadata without raw telemetry retention."""

    __tablename__ = "defensive_dataset_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "version", name="uq_defensive_dataset_version"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    source_id = Column(String, ForeignKey("defensive_dataset_sources.source_id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    dataset_fingerprint = Column(String(64), nullable=False, index=True)
    intended_use = Column(String, nullable=False, index=True)
    sample_count = Column(Integer, nullable=False)
    attack_sample_count = Column(Integer, nullable=False)
    benign_sample_count = Column(Integer, nullable=False)
    training_split_count = Column(Integer, nullable=False)
    validation_split_count = Column(Integer, nullable=False)
    test_split_count = Column(Integer, nullable=False)
    sanitization_attested = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DefensiveDatasetSampleRow(Base):
    """One minimized, labelled, sanitized sample in a versioned defensive corpus."""

    __tablename__ = "defensive_dataset_samples"
    __table_args__ = (
        UniqueConstraint("dataset_id", "split", "source_record_fingerprint", name="uq_defensive_dataset_sample"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    dataset_id = Column(String, ForeignKey("defensive_dataset_versions.dataset_id"), nullable=False, index=True)
    split = Column(String, nullable=False, index=True)
    label = Column(String, nullable=False, index=True)
    attack_family = Column(String, nullable=True)
    mitre_techniques = Column(JSONB, nullable=False)
    feature_payload = Column(JSONB, nullable=False)
    source_record_fingerprint = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)


class DefensiveEvaluationPolicyRow(Base):
    """Tenant-owned acceptance thresholds for advisory defensive model evaluation."""

    __tablename__ = "defensive_evaluation_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_defensive_evaluation_policy_tenant_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    minimum_precision = Column(Float, nullable=False)
    minimum_recall = Column(Float, nullable=False)
    maximum_false_positive_rate = Column(Float, nullable=False)
    minimum_attack_samples = Column(Integer, nullable=False)
    minimum_benign_samples = Column(Integer, nullable=False)
    require_test_split = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class DefensiveModelEvaluationRow(Base):
    """Immutable scored evaluation evidence for an advisory-only defensive model."""

    __tablename__ = "defensive_model_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "policy_id", "dataset_id", "model_id", "model_version", "evaluation_fingerprint",
            name="uq_defensive_model_evaluation",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    policy_id = Column(String, ForeignKey("defensive_evaluation_policies.policy_id"), nullable=False, index=True)
    dataset_id = Column(String, ForeignKey("defensive_dataset_versions.dataset_id"), nullable=False, index=True)
    dataset_version = Column(String, nullable=False)
    dataset_fingerprint = Column(String(64), nullable=False, index=True)
    model_id = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=False)
    evaluated_split = Column(String, nullable=False, index=True)
    true_positive = Column(Integer, nullable=False)
    false_positive = Column(Integer, nullable=False)
    true_negative = Column(Integer, nullable=False)
    false_negative = Column(Integer, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    false_positive_rate = Column(Float, nullable=False)
    status = Column(String, nullable=False, index=True)
    rejection_reasons = Column(JSONB, nullable=False)
    evaluation_fingerprint = Column(String(64), nullable=False, index=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    advisory_only = Column(Boolean, nullable=False, default=True)
    requires_human_approval = Column(Boolean, nullable=False, default=True)
    automatic_enforcement = Column(Boolean, nullable=False, default=False)


@event.listens_for(DefensiveModelEvaluationRow, "before_update")
def _reject_defensive_model_evaluation_update(_mapper, _connection, _target) -> None:
    raise RuntimeError("Defensive model evaluations are immutable and cannot be updated through the application ORM.")


@event.listens_for(DefensiveModelEvaluationRow, "before_delete")
def _reject_defensive_model_evaluation_delete(_mapper, _connection, _target) -> None:
    raise RuntimeError("Defensive model evaluations are immutable and cannot be deleted through the application ORM.")


class AdvisoryModelAssessmentRow(Base):
    """Immutable advisory model output; no row can represent a response or enforcement command."""

    __tablename__ = "advisory_model_assessments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "detection_id", "model_id", "model_version", "assessment_fingerprint",
            name="uq_advisory_model_assessment",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    detection_id = Column(String, nullable=False, index=True)
    model_id = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=False)
    evaluation_id = Column(String, ForeignKey("defensive_model_evaluations.evaluation_id"), nullable=False, index=True)
    classification = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    evidence_ids = Column(JSONB, nullable=False)
    reasons = Column(JSONB, nullable=False)
    recommended_mode = Column(String, nullable=False, index=True)
    assessment_fingerprint = Column(String(64), nullable=False, index=True)
    assessed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    advisory_only = Column(Boolean, nullable=False, default=True)
    requires_human_approval = Column(Boolean, nullable=False, default=True)
    automatic_enforcement = Column(Boolean, nullable=False, default=False)


@event.listens_for(AdvisoryModelAssessmentRow, "before_update")
def _reject_advisory_model_assessment_update(_mapper, _connection, _target) -> None:
    raise RuntimeError("Advisory model assessments are immutable and cannot be updated through the application ORM.")


@event.listens_for(AdvisoryModelAssessmentRow, "before_delete")
def _reject_advisory_model_assessment_delete(_mapper, _connection, _target) -> None:
    raise RuntimeError("Advisory model assessments are immutable and cannot be deleted through the application ORM.")


class TelemetryReplicationTargetRow(Base):
    """Configured telemetry-only regional stream target; no response channel metadata is stored."""

    __tablename__ = "telemetry_replication_targets"
    __table_args__ = (
        UniqueConstraint("tenant_id", "target_region", "stream_name", name="uq_telemetry_replication_target"),
    )

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    target_region = Column(String, nullable=False, index=True)
    stream_name = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class TelemetryReplicationReceiptRow(Base):
    """One idempotent delivery receipt for a canonical telemetry envelope replicated to a regional target."""

    __tablename__ = "telemetry_replication_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "target_id", "event_id", name="uq_telemetry_replication_event"),
    )

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    target_id = Column(String, ForeignKey("telemetry_replication_targets.target_id"), nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    source_region = Column(String, nullable=False)
    target_region = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)
    attempt_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String, nullable=True)


class TelemetryAgentCredentialRow(Base):
    """Tenant-bound public-key identity that may sign telemetry, never response commands."""

    __tablename__ = "telemetry_agent_credentials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "agent_id", "key_id", name="uq_telemetry_agent_credential"),
    )

    id = Column(Integer, primary_key=True, index=True)
    credential_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    key_id = Column(String, nullable=False, index=True)
    public_key_pem = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    revoked_at = Column(DateTime(timezone=True), nullable=True)


@event.listens_for(TelemetryAgentCredentialRow, "before_update")
def _restrict_telemetry_credential_update(_mapper, _connection, target) -> None:
    state = inspect(target)
    for field in ("credential_id", "tenant_id", "agent_id", "key_id", "public_key_pem", "created_at"):
        if state.attrs[field].history.has_changes():
            raise RuntimeError("Telemetry credential identity fields are immutable through the application ORM.")
    status_history = state.attrs["status"].history
    revoked_history = state.attrs["revoked_at"].history
    if not status_history.has_changes() and not revoked_history.has_changes():
        return
    previous_status = status_history.deleted[0] if status_history.deleted else None
    if previous_status != "active" or target.status != "revoked" or target.revoked_at is None:
        raise RuntimeError("Telemetry credentials may only transition once from active to revoked.")


class TelemetrySignatureNonceRow(Base):
    """Immutable accepted signed-telemetry nonce preventing cross-restart replay."""

    __tablename__ = "telemetry_signature_nonces"
    __table_args__ = (
        UniqueConstraint("tenant_id", "agent_id", "key_id", "nonce", name="uq_telemetry_signature_nonce"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nonce_record_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    key_id = Column(String, nullable=False, index=True)
    nonce = Column(String, nullable=False)
    payload_sha256 = Column(String, nullable=False)
    signed_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))


@event.listens_for(TelemetrySignatureNonceRow, "before_update")
def _reject_telemetry_nonce_update(_mapper, _connection, _target) -> None:
    raise RuntimeError("Accepted telemetry signature nonces are immutable and cannot be updated through the application ORM.")


@event.listens_for(TelemetrySignatureNonceRow, "before_delete")
def _reject_telemetry_nonce_delete(_mapper, _connection, _target) -> None:
    raise RuntimeError("Accepted telemetry signature nonces are immutable and cannot be deleted through the application ORM.")
