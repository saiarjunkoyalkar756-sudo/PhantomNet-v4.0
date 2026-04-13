from sqlalchemy.orm import Session
from .playbook_model import Playbook, PlaybookRun, PlaybookApproval
from typing import List, Optional, Dict, Any
import json

def get_playbook(db: Session, playbook_id: Optional[int] = None, name: Optional[str] = None):
    if playbook_id:
        return db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if name:
        return db.query(Playbook).filter(Playbook.name == name).first()
    return None

def get_playbooks(db: Session, skip: int = 0, limit: int = 100) -> List[Playbook]:
    return db.query(Playbook).offset(skip).limit(limit).all()

def create_playbook(db: Session, name: str, description: Optional[str] = None,
                    steps: List[Dict[str, Any]] = None, is_ai_generated: bool = False,
                    approved_by_human: bool = False, tags: Optional[str] = None) -> Playbook:
    db_playbook = Playbook(
        name=name,
        description=description,
        steps_json=json.dumps(steps) if steps else "[]",
        is_ai_generated=is_ai_generated,
        approved_by_human=approved_by_human,
        tags=tags
    )
    db.add(db_playbook)
    db.commit()
    db.refresh(db_playbook)
    return db_playbook

def update_playbook(db: Session, playbook_id: int, name: Optional[str] = None,
                    description: Optional[str] = None, steps: Optional[List[Dict[str, Any]]] = None,
                    status: Optional[str] = None, is_ai_generated: Optional[bool] = None,
                    approved_by_human: Optional[bool] = None, tags: Optional[str] = None) -> Optional[Playbook]:
    db_playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if db_playbook:
        if name is not None:
            db_playbook.name = name
        if description is not None:
            db_playbook.description = description
        if steps is not None:
            db_playbook.steps_json = json.dumps(steps)
        if status is not None:
            db_playbook.status = status
        if is_ai_generated is not None:
            db_playbook.is_ai_generated = is_ai_generated
        if approved_by_human is not None:
            db_playbook.approved_by_human = approved_by_human
        if tags is not None:
            db_playbook.tags = tags
        
        db_playbook.version += 1 # Increment version on update
        db.commit()
        db.refresh(db_playbook)
    return db_playbook

def delete_playbook(db: Session, playbook_id: int):
    db_playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if db_playbook:
        db.delete(db_playbook)
        db.commit()
        return True
    return False

def get_playbook_run(db: Session, run_id: int) -> Optional[PlaybookRun]:
    return db.query(PlaybookRun).filter(PlaybookRun.id == run_id).first()

def get_playbook_runs(db: Session, playbook_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[PlaybookRun]:
    if playbook_id:
        return db.query(PlaybookRun).filter(PlaybookRun.playbook_id == playbook_id).offset(skip).limit(limit).all()
    return db.query(PlaybookRun).offset(skip).limit(limit).all()

def create_playbook_run(db: Session, playbook_id: int, triggered_by: Optional[str] = None) -> PlaybookRun:
    db_playbook_run = PlaybookRun(
        playbook_id=playbook_id,
        triggered_by=triggered_by
    )
    db.add(db_playbook_run)
    db.commit()
    db.refresh(db_playbook_run)
    return db_playbook_run

def update_playbook_run(db: Session, run_id: int, status: Optional[str] = None,
                         result: Optional[Dict[str, Any]] = None, completed_at=None) -> Optional[PlaybookRun]:
    db_playbook_run = db.query(PlaybookRun).filter(PlaybookRun.id == run_id).first()
    if db_playbook_run:
        if status is not None:
            db_playbook_run.status = status
        if result is not None:
            db_playbook_run.result_json = json.dumps(result)
        if completed_at is not None:
            db_playbook_run.completed_at = completed_at
        db.commit()
        db.refresh(db_playbook_run)
    return db_playbook_run

def create_playbook_approval(db: Session, playbook_run_id: int, approver_id: str,
                             approved: bool, approval_notes: Optional[str] = None) -> PlaybookApproval:
    db_approval = PlaybookApproval(
        playbook_run_id=playbook_run_id,
        approver_id=approver_id,
        approved=approved,
        approval_notes=approval_notes
    )
    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)
    return db_approval