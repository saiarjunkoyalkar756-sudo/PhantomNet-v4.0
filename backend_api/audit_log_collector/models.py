from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import datetime
import json

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    event_id = Column(String, nullable=True, index=True) # e.g., Windows Event ID, Syslog event type
    actor_id = Column(String, nullable=True, index=True) # User or process that initiated the action
    action = Column(String, nullable=False, index=True) # e.g., "login", "file_access", "configuration_change"
    resource = Column(String, nullable=True, index=True) # Resource acted upon (e.g., "filename", "user_account", "system_config")
    status = Column(String, nullable=True) # "success", "failure"
    source_ip = Column(String, nullable=True)
    host_identifier = Column(String, nullable=True, index=True) # Host where the audit event occurred
    raw_log_data = Column(Text, nullable=False) # The original raw audit log string
    
    # Structured metadata from the audit event
    metadata_json = Column(Text, nullable=True)

    ingested_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', actor='{self.actor_id}', timestamp='{self.timestamp}')>"
