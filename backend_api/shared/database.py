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
    text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

# Load settings
# Assuming settings.py is updated to include DATABASE_URL
# If not, we'll read it directly from env for now
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://phantomnet:changeme@localhost:5432/phantomnet")

# Async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False # Set to True for debugging SQL queries
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

# --- Models ---

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
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
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    used_at = Column(DateTime, nullable=True)
    ip_request = Column(String)
    ip_use = Column(String, nullable=True)

class AttackLog(Base):
    __tablename__ = "attack_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
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
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

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
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_data = Column(JSONB)

class NormalizedEvent(Base):
    __tablename__ = "normalized_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    details = Column(JSONB)

class ForensicRecord(Base):
    __tablename__ = "forensic_records"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String, unique=True, nullable=False)
    tool_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    results = Column(JSONB)

class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
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
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
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
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    rotated_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

class RevokedCertificate(Base):
    __tablename__ = "revoked_certificates"
    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String, unique=True, index=True, nullable=False)
    revocation_date = Column(DateTime, default=datetime.datetime.utcnow)
    reason = Column(String)

class CognitiveMemoryDB(Base):
    __tablename__ = "cognitive_memory"
    id = Column(Integer, primary_key=True, index=True)
    threat_data = Column(String, unique=True, nullable=False)
    episode_data = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PlaybookRunDB(Base):
    __tablename__ = "soar_playbook_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    playbook_id = Column(Integer, ForeignKey("soar_playbooks.id"), nullable=False)
    playbook_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    triggered_by = Column(JSONB, nullable=False)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    current_context = Column(JSONB, nullable=False)
    
    playbook = relationship("PlaybookDB", backref="runs")
    execution_logs = relationship("PlaybookExecutionLogDB", back_populates="playbook_run", cascade="all, delete-orphan")

class PlaybookExecutionLogDB(Base):
    __tablename__ = "soar_playbook_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    playbook_run_id = Column(String, ForeignKey("soar_playbook_runs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    step_action = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)
    output = Column(JSONB, nullable=True)

    playbook_run = relationship("PlaybookRunDB", back_populates="execution_logs")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get an async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
