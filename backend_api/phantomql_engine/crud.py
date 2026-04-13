from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from .models import NormalizedEvent
from ..log_normalizer.event_schema import NormalizedLogEvent as NormalizedLogEventSchema # To create from schema
import datetime
import json

def create_normalized_event(db: Session, event: NormalizedLogEventSchema) -> NormalizedEvent:
    db_event = NormalizedEvent(
        event_id=event.event_id,
        timestamp=event.timestamp,
        event_type=event.event_type,
        severity=event.severity,
        message=event.message,
        source_type=event.source_type,
        source_host=event.source_host,
        source_ip=event.source_ip,
        source_port=event.source_port,
        destination_host=event.destination_host,
        destination_ip=event.destination_ip,
        destination_port=event.destination_port,
        user=event.user,
        process_name=event.process_name,
        process_id=event.process_id,
        file_path=event.file_path,
        file_hash=event.file_hash,
        protocol=event.protocol,
        action=event.action,
        original_raw_log=event.original_raw_log,
        metadata_json=json.dumps(event.metadata) if event.metadata else None,
        normalized_at=event.normalized_at
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def get_normalized_event(db: Session, event_id: str) -> Optional[NormalizedEvent]:
    return db.query(NormalizedEvent).filter(NormalizedEvent.event_id == event_id).first()

def get_normalized_events(db: Session, skip: int = 0, limit: int = 100,
                          event_type: Optional[str] = None,
                          severity: Optional[str] = None,
                          source_host: Optional[str] = None,
                          source_ip: Optional[str] = None,
                          destination_ip: Optional[str] = None,
                          user: Optional[str] = None,
                          start_time: Optional[datetime.datetime] = None,
                          end_time: Optional[datetime.datetime] = None,
                          search_query: Optional[str] = None) -> List[NormalizedEvent]:
    query = db.query(NormalizedEvent)
    
    if event_type:
        query = query.filter(NormalizedEvent.event_type == event_type)
    if severity:
        query = query.filter(NormalizedEvent.severity == severity)
    if source_host:
        query = query.filter(NormalizedEvent.source_host == source_host)
    if source_ip:
        query = query.filter(NormalizedEvent.source_ip == source_ip)
    if destination_ip:
        query = query.filter(NormalizedEvent.destination_ip == destination_ip)
    if user:
        query = query.filter(NormalizedEvent.user == user)
    if start_time:
        query = query.filter(NormalizedEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(NormalizedEvent.timestamp <= end_time)
    if search_query:
        # Simple text search across message, raw_log, metadata
        query = query.filter(
            (NormalizedEvent.message.contains(search_query)) |
            (NormalizedEvent.original_raw_log.contains(search_query)) |
            (NormalizedEvent.metadata_json.contains(search_query))
        )
            
    return query.order_by(NormalizedEvent.timestamp.desc()).offset(skip).limit(limit).all()

def count_events_by_severity(db: Session, start_time: Optional[datetime.datetime] = None, end_time: Optional[datetime.datetime] = None) -> Dict[str, int]:
    query = db.query(NormalizedEvent.severity, func.count(NormalizedEvent.id))
    if start_time:
        query = query.filter(NormalizedEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(NormalizedEvent.timestamp <= end_time)
    query = query.group_by(NormalizedEvent.severity)
    
    return {severity: count for severity, count in query.all()}

def count_events_by_event_type(db: Session, start_time: Optional[datetime.datetime] = None, end_time: Optional[datetime.datetime] = None) -> Dict[str, int]:
    query = db.query(NormalizedEvent.event_type, func.count(NormalizedEvent.id))
    if start_time:
        query = query.filter(NormalizedEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(NormalizedEvent.timestamp <= end_time)
    query = query.group_by(NormalizedEvent.event_type)
    
    return {event_type: count for event_type, count in query.all()}
