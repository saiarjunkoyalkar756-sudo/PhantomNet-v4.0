from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class RawLogEvent(Base):
    __tablename__ = "raw_log_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    source_type = Column(String, nullable=False, index=True) # e.g., "syslog", "windows_event", "firewall_log", "agent_telemetry"
    host_identifier = Column(String, nullable=True, index=True) # e.g., hostname, IP, agent_id
    raw_log_data = Column(Text, nullable=False) # The original, raw log string
    ingested_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Optional: Initial parsing metadata, useful for correlating with normalizer later
    initial_metadata_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RawLogEvent(id={self.id}, source='{self.source_type}', host='{self.host_identifier}', timestamp='{self.timestamp}')>"
