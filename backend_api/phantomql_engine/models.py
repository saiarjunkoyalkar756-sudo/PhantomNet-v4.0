from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import datetime
import json

Base = declarative_base()

class NormalizedEvent(Base):
    __tablename__ = "normalized_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    source_type = Column(String, nullable=False, index=True)
    source_host = Column(String, nullable=True, index=True)
    source_ip = Column(String, nullable=True, index=True)
    source_port = Column(Integer, nullable=True)
    
    destination_host = Column(String, nullable=True, index=True)
    destination_ip = Column(String, nullable=True, index=True)
    destination_port = Column(Integer, nullable=True)
    
    user = Column(String, nullable=True, index=True)
    process_name = Column(String, nullable=True, index=True)
    process_id = Column(Integer, nullable=True)
    
    file_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    
    protocol = Column(String, nullable=True)
    action = Column(String, nullable=True)

    original_raw_log = Column(Text, nullable=False)
    
    # Store metadata as JSON
    metadata_json = Column(Text, nullable=True)

    normalized_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<NormalizedEvent(id={self.id}, event_type='{self.event_type}', severity='{self.severity}', timestamp='{self.timestamp}')>"
