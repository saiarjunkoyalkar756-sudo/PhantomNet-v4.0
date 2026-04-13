from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from .models import RawLogEvent
import datetime
import json

def create_raw_log_event(db: Session, raw_log_data: str, source_type: str,
                         host_identifier: Optional[str] = None,
                         timestamp: Optional[datetime.datetime] = None,
                         initial_metadata: Optional[Dict[str, Any]] = None) -> RawLogEvent:
    db_log_event = RawLogEvent(
        raw_log_data=raw_log_data,
        source_type=source_type,
        host_identifier=host_identifier,
        timestamp=timestamp if timestamp else datetime.datetime.now(),
        initial_metadata_json=json.dumps(initial_metadata) if initial_metadata else None
    )
    db.add(db_log_event)
    db.commit()
    db.refresh(db_log_event)
    return db_log_event

def get_raw_log_event(db: Session, log_id: int) -> Optional[RawLogEvent]:
    return db.query(RawLogEvent).filter(RawLogEvent.id == log_id).first()

def get_raw_log_events(db: Session, skip: int = 0, limit: int = 100,
                       source_type: Optional[str] = None,
                       host_identifier: Optional[str] = None,
                       start_time: Optional[datetime.datetime] = None,
                       end_time: Optional[datetime.datetime] = None) -> List[RawLogEvent]:
    query = db.query(RawLogEvent)
    if source_type:
        query = query.filter(RawLogEvent.source_type == source_type)
    if host_identifier:
        query = query.filter(RawLogEvent.host_identifier == host_identifier)
    if start_time:
        query = query.filter(RawLogEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(RawLogEvent.timestamp <= end_time)
    
    return query.order_by(RawLogEvent.timestamp.desc()).offset(skip).limit(limit).all()
