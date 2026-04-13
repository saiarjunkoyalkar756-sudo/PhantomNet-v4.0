from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import json

Base = declarative_base()

class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), default=func.now(), nullable=False)
    status = Column(String, default="draft", nullable=False)  # e.g., draft, active, archived
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    approved_by_human = Column(Boolean, default=False, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    tags = Column(String, nullable=True) # Comma-separated tags

    # Playbook steps will be stored as JSON for flexibility
    # This can be a list of dictionaries, where each dictionary represents a step
    # Example: [{"action": "isolate_host", "parameters": {"host_id": "123"}}, {"action": "create_ticket", "parameters": {"severity": "high"}}]
    steps_json = Column(Text, nullable=False, default="[]")

    # Relationship to Playbook Runs (if we implement a separate run tracking)
    # runs = relationship("PlaybookRun", back_populates="playbook")

    def __repr__(self):
        return f"<Playbook(id={self.id}, name='{self.name}', status='{self.status}')>"

    @property
    def steps(self):
        return json.loads(self.steps_json)

    @steps.setter
    def steps(self, value):
        self.steps_json = json.dumps(value)

class PlaybookRun(Base):
    __tablename__ = "playbook_runs"

    id = Column(Integer, primary_key=True, index=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"), nullable=False)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="running", nullable=False) # e.g., running, completed, failed, awaiting_approval
    triggered_by = Column(String, nullable=True) # e.g., "system", "user_id_123"
    result_json = Column(Text, nullable=True) # Stores results of the run as JSON

    playbook = relationship("Playbook", backref="runs")

    def __repr__(self):
        return f"<PlaybookRun(id={self.id}, playbook_id={self.playbook_id}, status='{self.status}')>"

    @property
    def result(self):
        return json.loads(self.result_json) if self.result_json else None

    @result.setter
    def result(self, value):
        self.result_json = json.dumps(value)

# Optional: Add a model for Playbook Approval if human-in-the-loop requires explicit tracking
class PlaybookApproval(Base):
    __tablename__ = "playbook_approvals"

    id = Column(Integer, primary_key=True, index=True)
    playbook_run_id = Column(Integer, ForeignKey("playbook_runs.id"), nullable=False)
    approver_id = Column(String, nullable=False) # User ID of the approver
    approved = Column(Boolean, nullable=False)
    approval_notes = Column(Text, nullable=True)
    approved_at = Column(DateTime, server_default=func.now(), nullable=False)

    playbook_run = relationship("PlaybookRun", backref="approvals")

    def __repr__(self):
        return f"<PlaybookApproval(id={self.id}, run_id={self.playbook_run_id}, approved={self.approved})>"