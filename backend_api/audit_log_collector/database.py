from __future__ import annotations

from collections.abc import Generator
import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def _configured_database_url() -> str:
    """Resolve a synchronous audit-store URL without logging credential material."""
    explicit_url = os.getenv("AUDIT_DATABASE_URL") or os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url.replace("postgresql+asyncpg://", "postgresql://").replace("sqlite+aiosqlite://", "sqlite://")

    host = os.getenv("DB_HOST")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    if host and database and username and password:
        return f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}/{quote_plus(database)}"

    database_dir = Path(__file__).resolve().parent / "data"
    database_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{database_dir / 'audit_logs.db'}"


SQLALCHEMY_DATABASE_URL = _configured_database_url()


def _create_engine() -> Engine:
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        return create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    return create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def initialize_database() -> None:
    """Create the collector-owned audit table for controlled deployments lacking a prior schema."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a short-lived synchronous session and always close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
