import json
import os
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, JSON, select, text, DateTime
from sqlalchemy.sql import func
from datetime import datetime

# --- Async Database Configuration ---
DATABASE_URL = os.getenv(
    "ASYNC_DB_URL", 
    "postgresql+asyncpg://phantomnet:phantomnet@postgres:5432/phantomnet_db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class CorrelationRule(Base):
    __tablename__ = "correlation_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String)
    logic: Mapped[dict] = mapped_column(JSON)
    action: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

async def init_db():
    """Initializes the database schema asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_all_rules() -> List[dict]:
    """Retrieves all enabled correlation rules asynchronously."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CorrelationRule).where(CorrelationRule.enabled == True)
        )
        rules = result.scalars().all()
        return [
            {
                "name": r.name,
                "description": r.description,
                "logic": r.logic,
                "action": r.action,
                "severity": r.severity,
                "enabled": r.enabled
            }
            for r in rules
        ]

async def upsert_rule(rule_data: dict):
    """Inserts or updates a correlation rule asynchronously."""
    async with AsyncSessionLocal() as session:
        stmt = select(CorrelationRule).where(CorrelationRule.name == rule_data["name"])
        result = await session.execute(stmt)
        existing_rule = result.scalar_one_or_none()

        if existing_rule:
            existing_rule.description = rule_data.get("description")
            existing_rule.logic = rule_data.get("logic")
            existing_rule.action = rule_data.get("action")
            existing_rule.severity = rule_data.get("severity")
            existing_rule.enabled = rule_data.get("enabled", True)
        else:
            new_rule = CorrelationRule(
                name=rule_data["name"],
                description=rule_data.get("description"),
                logic=rule_data.get("logic"),
                action=rule_data.get("action"),
                severity=rule_data.get("severity"),
                enabled=rule_data.get("enabled", True)
            )
            session.add(new_rule)
        
        await session.commit()
