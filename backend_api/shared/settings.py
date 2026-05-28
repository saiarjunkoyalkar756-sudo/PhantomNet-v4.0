# backend_api/shared/settings.py
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from loguru import logger

class Settings(BaseSettings):
    """
    Consolidated application settings using Pydantic.
    Settings are loaded from environment variables or a .env file.
    """
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Core Settings ---
    SAFE_MODE: bool = Field(
        default=True,
        description="Toggle safe mode (mocking third-party integrations)."
    )

    # --- Database Settings ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://phantomnet:changeme@localhost:5432/phantomnet",
        description="Async PostgreSQL connection URL."
    )
    OPERATIONAL_DB_URL: str = Field(
        default="sqlite:///./operational.db",
        description="Path to operational database."
    )
    POLICY_DB_URL: str = Field(
        default="sqlite:///./policy.db",
        description="Path to policy database."
    )
    TELEMETRY_DB_URL: str = Field(
        default="sqlite:///./telemetry.db",
        description="Path to telemetry database."
    )
    ALERTS_DB_URL: str = Field(
        default="sqlite:///./alerts.db",
        description="Path to alerts database."
    )
    DB_PASSWORD: str = Field(
        default="changeme",
        description="PostgreSQL Database Password."
    )

    # --- Redis Settings ---
    REDIS_HOST: str = Field(default="localhost", description="Redis hostname.")
    REDIS_PORT: int = Field(default=6379, description="Redis port.")
    REDIS_DB: int = Field(default=0, description="Redis database index.")
    REDIS_URL: Optional[str] = Field(default=None, description="Complete Redis connection URL.")

    # --- Neo4j Settings ---
    NEO4J_HOST: str = Field(default="localhost", description="Neo4j hostname.")
    NEO4J_PORT: int = Field(default=7687, description="Neo4j Bolt port.")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username.")
    NEO4J_PASSWORD: str = Field(default="changeme", description="Neo4j password.")

    # --- Kafka / Redpanda Settings ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="redpanda:29092",
        description="Comma-separated Kafka bootstrap server addresses."
    )

    # --- Security / JWT Settings ---
    JWT_SECRET_KEY: str = Field(
        default="a_very_secret_key_that_should_be_changed",
        description="Secret key for JWT generation/validation."
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Expiration time for access tokens.")

    # --- OSINT / Third Party APIs ---
    VIRUSTOTAL_API_KEY: Optional[str] = Field(default=None, description="VirusTotal enrichment key.")

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Startup validation to prevent using weak keys in production."""
        # Retrieve SAFE_MODE from validation input if possible, or fall back to OS env
        safe_mode = info.data.get("SAFE_MODE", True) if hasattr(info, "data") else True
        if not safe_mode and v == "a_very_secret_key_that_should_be_changed":
            raise ValueError("Insecure default JWT_SECRET_KEY cannot be used when SAFE_MODE is disabled.")
        if len(v) < 32 and not safe_mode:
            logger.warning("JWT_SECRET_KEY is less than 32 characters! It is recommended to use a stronger secret.")
        return v

# Instantiate the settings
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
