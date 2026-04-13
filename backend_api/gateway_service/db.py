from sqlmodel import create_engine, SQLModel, Field, Session
from typing import Optional, List
from datetime import datetime
import os
from uuid import UUID # Import UUID

# --- Configuration ---
DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'phantomnet_db')
DB_USER = os.environ.get('DB_USER', 'phantomnet')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

# Changed to SQLite for local development/testing without PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./alerts.db")

engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

# --- Data Model ---
class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True, nullable=False) # New tenant_id field (stored as string for SQLite compatibility)
    alert_id: str = Field(index=True, unique=True, nullable=False)
    rule_id: str
    rule_name: Optional[str] = None
    agent_id: str = Field(index=True, nullable=False)
    triggered_at: datetime
    severity: Optional[str] = None
    details: Optional[str] = None
    received_at: Optional[datetime] = None
    __table_args__ = {'extend_existing': True}

# --- Database Session Management ---
def get_session():
    with Session(engine) as session:
        yield session
