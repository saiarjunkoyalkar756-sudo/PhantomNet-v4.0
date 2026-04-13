# shared/settings.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Consolidated application settings using Pydantic.
    Settings are loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Core settings
    SAFE_MODE: bool = True

    # Database URLs
    # In a real production environment, these should not have defaults
    # and should be set explicitly in the environment.
    OPERATIONAL_DB_URL: str = "sqlite:///./operational.db"
    POLICY_DB_URL: str = "sqlite:///./policy.db"
    TELEMETRY_DB_URL: str = "sqlite:///./telemetry.db"
    ALERTS_DB_URL: str = "sqlite:///./alerts.db"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Cassandra
    CASSANDRA_CONTACT_POINTS: list[str] = ["127.0.0.1"]
    CASSANDRA_PORT: int = 9042
    CASSANDRA_KEYSPACE: str = "telemetry"

    # JWT
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


# Instantiate the settings
settings = Settings()

# For compatibility with the old DatabaseConfig structure, we can provide this helper.
# However, new code should import `settings` directly.
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

