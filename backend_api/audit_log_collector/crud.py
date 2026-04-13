from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from .models import AuditLog
import datetime
import json

def create_audit_log(db: Session, raw_log_data: str, action: str,
                     timestamp: Optional[datetime.datetime] = None,
                     event_id: Optional[str] = None,
                     actor_id: Optional[str] = None,
                     resource: Optional[str] = None,
                     status: Optional[str] = None,
                     source_ip: Optional[str] = None,
                     host_identifier: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> AuditLog:
    db_audit_log = AuditLog(
        timestamp=timestamp if timestamp else datetime.datetime.now(),
        event_id=event_id,
        actor_id=actor_id,
        action=action,
        resource=resource,
        status=status,
        source_ip=source_ip,
        host_identifier=host_identifier,
        raw_log_data=raw_log_data,
        metadata_json=json.dumps(metadata) if metadata else None
    )
    db.add(db_audit_log)
    db.commit()
    db.refresh(db_audit_log)
    return db_audit_log

def get_audit_log(db: Session, log_id: int) -> Optional[AuditLog]:
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100,
                   start_time: Optional[datetime.datetime] = None,
                   end_time: Optional[datetime.datetime] = None,
                   actor_id: Optional[str] = None,
                   action: Optional[str] = None,
                   resource: Optional[str] = None,
                   host_identifier: Optional[str] = None,
                   status_filter: Optional[str] = None) -> List[AuditLog]:
    query = db.query(AuditLog)
    
    if start_time:
        query = query.filter(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.filter(AuditLog.timestamp <= end_time)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource:
        query = query.filter(AuditLog.resource == resource)
    if host_identifier:
        query = query.filter(AuditLog.host_identifier == host_identifier)
    if status_filter:
        query = query.filter(AuditLog.status == status_filter)
            
    return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
