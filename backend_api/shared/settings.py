"""Environment-backed runtime settings for PhantomNet services."""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Consolidated configuration loaded from environment variables or a local .env file.

    Credentials intentionally have no embedded fallback values. Production and staging
    startup validation requires all critical secrets to be supplied through the environment.
    """

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SAFE_MODE: bool = Field(default=True, description="Disable real integrations by default.")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://phantomnet@localhost:5432/phantomnet",
        description="Async PostgreSQL connection URL; credentials must be supplied externally.",
    )
    OPERATIONAL_DB_URL: str = Field(default="sqlite:///./operational.db")
    POLICY_DB_URL: str = Field(default="sqlite:///./policy.db")
    TELEMETRY_DB_URL: str = Field(default="sqlite:///./telemetry.db")
    ALERTS_DB_URL: str = Field(default="sqlite:///./alerts.db")
    DB_PASSWORD: Optional[str] = Field(default=None, repr=False)

    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: Optional[str] = Field(default=None, repr=False)

    NEO4J_HOST: str = Field(default="localhost")
    NEO4J_PORT: int = Field(default=7687)
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: Optional[str] = Field(default=None, repr=False)

    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="redpanda:29092")

    JWT_SECRET_KEY: Optional[str] = Field(default=None, repr=False)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    VIRUSTOTAL_API_KEY: Optional[str] = Field(default=None, repr=False)

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: Optional[str], info) -> Optional[str]:
        safe_mode = info.data.get("SAFE_MODE", True) if hasattr(info, "data") else True
        if not value:
            if not safe_mode:
                raise ValueError("JWT_SECRET_KEY must be supplied when SAFE_MODE is disabled.")
            return value
        if not safe_mode and len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters when SAFE_MODE is disabled.")
        if safe_mode and len(value) < 32:
            logger.warning("JWT_SECRET_KEY is shorter than 32 characters; this is acceptable only in SAFE_MODE.")
        return value


settings = Settings()


class DatabaseConfig:
    DATABASE_URLS = {
        "operational": settings.OPERATIONAL_DB_URL,
        "policy": settings.POLICY_DB_URL,
        "telemetry": settings.TELEMETRY_DB_URL,
        "alerts": settings.ALERTS_DB_URL,
    }

    @staticmethod
    def get_database_url(db_type: str) -> str:
        url = DatabaseConfig.DATABASE_URLS.get(db_type)
        if not url:
            raise ValueError(f"Unknown database type: {db_type}")
        return url
