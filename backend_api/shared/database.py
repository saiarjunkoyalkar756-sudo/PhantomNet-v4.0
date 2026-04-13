# shared/database.py
import os # Import os
import sqlalchemy # Import sqlalchemy
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.orm import sessionmaker, relationship
import datetime
from typing import Dict, Any, Generator
from sqlalchemy.dialects.postgresql import JSON # Import JSON for JSONB type
from sqlalchemy.exc import OperationalError # Import OperationalError
import uuid
from uuid import UUID, uuid4 # Import uuid for uuid4() default
import sys # Import sys

# All models are defined here for now. In a mature microservices architecture,
# these models would be moved into the respective services that own them.
# For example, the User and SessionToken models would live in the iam_service.

from backend_api.shared.settings import DatabaseConfig  # Import the new DatabaseConfig

# Dictionary to hold SQLAlchemy engines for different database types
engines: Dict[str, Any] = {}
# Dictionary to hold sessionmakers for different database types
session_makers: Dict[str, Any] = {}

DB_SAFE_MODE = False # Global flag for database safe mode

def get_engine(db_type: str):
    """
    Returns a SQLAlchemy engine for the given database type.
    Engines are cached to avoid recreating them on every call.
    Handles connection failures and sets DB_SAFE_MODE.
    """
    global DB_SAFE_MODE
    if db_type not in engines:
        DATABASE_URL = DatabaseConfig.get_database_url(db_type)
        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args={"check_same_thread": False}
        
        try:
            engine = create_engine(DATABASE_URL, connect_args=connect_args)
            # Test connection immediately
            with engine.connect() as connection:
                connection.execute(sqlalchemy.text("SELECT 1")) # Use sqlalchemy.text
            engines[db_type] = engine
        except OperationalError as e:
            print(f"CRITICAL ERROR: Could not connect to database '{db_type}' at {DATABASE_URL}. Error: {e}", file=sys.stderr)
            DB_SAFE_MODE = True
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                print("Exiting in production environment due to critical database connection failure.", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"Continuing in {os.getenv('ENVIRONMENT', 'development')} environment, but database '{db_type}' will be in SAFE MODE. Functionality may be limited.", file=sys.stderr)
                # Return a dummy engine or handle gracefully if SAFE_MODE means reduced functionality
                # For now, we'll let subsequent calls fail but avoid app exit in dev
                engines[db_type] = None # Mark engine as unavailable
        except Exception as e:
            print(f"UNEXPECTED ERROR: during database connection to '{db_type}'. Error: {e}", file=sys.stderr)
            DB_SAFE_MODE = True
            if os.getenv("ENVIRONMENT", "development").lower() == "production":
                print("Exiting in production environment due to unexpected database connection error.", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"Continuing in {os.getenv('ENVIRONMENT', 'development')} environment, but database '{db_type}' will be in SAFE MODE. Functionality may be limited.", file=sys.stderr)
                engines[db_type] = None
    return engines.get(db_type)

def get_session_local(db_type: str):
    """
    Returns a sessionmaker for the given database type.
    """
    global DB_SAFE_MODE
    engine = get_engine(db_type)
    if engine is None:
        # If engine failed to initialize, return a dummy sessionmaker that always raises an error
        print(f"WARNING: Database '{db_type}' is in SAFE MODE. Session creation will fail.", file=sys.stderr)
        DB_SAFE_MODE = True
        class DummySessionLocal:
            def __call__(self):
                raise OperationalError("Database is in SAFE MODE. Connection not established.", params={}, orig=None)
        return DummySessionLocal() # Return an instance that raises error
    if db_type not in session_makers:
        session_makers[db_type] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_makers[db_type]

Base = declarative_base()

# Import all models here so that Base has them registered
from backend_api.microsegmentation_service.models import *
from backend_api.vulnerability_management_service.models import *
from backend_api.soar_playbook_engine.playbook_model import *
from backend_api.phantomql_engine.models import *
from backend_api.siem_ingest_service.models import *
from backend_api.forensics_engine.models import *
from backend_api.compliance_service.models import *
from backend_api.audit_log_collector.models import *


# Create a default SessionLocal for the 'operational' database,
# as expected by the existing middleware in the gateway.
SessionLocal = get_session_local("operational")
from sqlalchemy import text # Import text for raw SQL execution

# New Tenant Model for Multi-tenancy
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

# Models required by the existing API Gateway
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False) # New tenant_id
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
    twofa_enforced = Column(Boolean, default=False)
    totp_secret = Column(String, nullable=True)
    webauthn_enabled = Column(Boolean, default=False)
    trust_score = Column(Float, default=100.0)


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
    device_fingerprint = Column(String, nullable=True) # New column
    anomaly_score = Column(Float, nullable=True) # New column
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


# New Models for Blockchain Auditing
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, nullable=False)
    alert_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    event_data = Column(String)  # Stored as JSON string


class NormalizedEvent(Base):
    __tablename__ = "normalized_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    source = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    details = Column(String)  # Stored as JSON string


class ForensicRecord(Base):
    __tablename__ = "forensic_records"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String, unique=True, nullable=False)
    tool_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    results = Column(String)  # Stored as JSON string


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, unique=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    previous_hash = Column(String, nullable=False)
    block_hash = Column(String, unique=True, nullable=False)  # Renamed from 'hash'
    proof = Column(Integer, nullable=False)
    merkle_root = Column(String, nullable=True)

    transactions = relationship(
        "Transaction", back_populates="block", cascade="all, delete-orphan"
    )  # New relationship

    def to_dict(self):
        return {
            "id": self.id,
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,  # Changed from "hash"
            "proof": self.proof,
            "merkle_root": self.merkle_root,
            "transactions": [
                tx.to_dict() for tx in self.transactions
            ],  # Include transactions
        }


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"))  # Link to Block
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    data = Column(String, nullable=True)  # General data field, could still be used
    attack_type = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)  # Added

    # New foreign keys to link to audited data
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    normalized_event_id = Column(
        Integer, ForeignKey("normalized_events.id"), nullable=True
    )
    forensic_record_id = Column(
        Integer, ForeignKey("forensic_records.id"), nullable=True
    )
    data_type = Column(
        String, nullable=True
    )  # e.g., "attack_log", "alert", "normalized_event", "forensic_record"

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
            "timestamp": self.timestamp,
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
    configuration = Column(String, nullable=True) # New: Stores agent-specific configuration as JSON
    os = Column(String, nullable=True) # Operating system of the agent
    capabilities = Column(JSON, nullable=True) # Capabilities of the agent, stored as JSONB
    last_reported_health = Column(JSON, nullable=True) # Last reported health snapshot of the agent
    last_reported_errors = Column(JSON, nullable=True) # Last reported errors and remediation attempts
    available_patches = Column(JSON, nullable=True) # Patches available or applied
    last_patch_applied = Column(DateTime, nullable=True) # Timestamp of the last successful patch application
    self_healing_enabled = Column(Boolean, default=False) # Is self-healing enabled on this agent
    safe_mode_active = Column(Boolean, default=False) # Is the agent operating in SAFE_MODE


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


# My new tables
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

# New Models for SOAR Engine
class PlaybookDB(Base):
    __tablename__ = "soar_playbooks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    trigger = Column(JSON, nullable=False) # Store trigger as JSON
    steps = Column(JSON, nullable=False) # Store steps as JSON (list of PlaybookStep)
    context = Column(JSON, nullable=True) # Store initial context as JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PlaybookRunDB(Base):
    __tablename__ = "soar_playbook_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, nullable=False) # Use UUID as string
    playbook_id = Column(Integer, ForeignKey("soar_playbooks.id"), nullable=False)
    playbook_name = Column(String, nullable=False)
    status = Column(String, nullable=False) # e.g., "pending", "running", "completed", "failed"
    triggered_by = Column(JSON, nullable=False) # Store incident context as JSON
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    current_context = Column(JSON, nullable=False) # Store current execution context as JSON
    
    playbook = relationship("PlaybookDB", backref="runs")
    execution_logs = relationship("PlaybookExecutionLogDB", back_populates="playbook_run", cascade="all, delete-orphan", order_by="PlaybookExecutionLogDB.timestamp")

class PlaybookExecutionLogDB(Base):
    __tablename__ = "soar_playbook_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    playbook_run_id = Column(String, ForeignKey("soar_playbook_runs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    step_action = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(JSON, nullable=True) # Store details as JSON
    output = Column(JSON, nullable=True) # Store output as JSONB

    playbook_run = relationship("PlaybookRunDB", back_populates="execution_logs")




def get_db(db_type: str = "operational") -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session for a specific database type.
    Defaults to the 'operational' database.
    """
    SessionLocal = get_session_local(db_type)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# For testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
