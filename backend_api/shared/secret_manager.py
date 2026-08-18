"""Environment-backed secret retrieval and startup validation."""

from __future__ import annotations

import os
import secrets

from loguru import logger


CRITICAL_SECRET_KEYS = ("JWT_SECRET_KEY", "DB_PASSWORD", "NEO4J_PASSWORD")
INSECURE_SECRET_VALUES = {
    "changeme",
    "changeme123",
    "a_very_secret_key_that_should_be_changed",
}
STRICT_ENVIRONMENTS = {"production", "staging"}


def _environment() -> str:
    return os.getenv("ENVIRONMENT", "development").strip().lower()


def _is_strict_environment() -> bool:
    return _environment() in STRICT_ENVIRONMENTS


def get_secret(key: str, generate_if_missing: bool = False) -> str:
    """Retrieve a secret from the environment.

    Development and test environments may receive a process-local random secret when a
    caller explicitly or implicitly allows generation. Production and staging fail closed.
    """
    value = os.getenv(key)
    if value:
        return value

    if _environment() in {"development", "testing"}:
        generate_if_missing = True
    if generate_if_missing and not _is_strict_environment():
        generated_secret = secrets.token_hex(32)
        os.environ[key] = generated_secret
        logger.warning("Generated a temporary development secret; configure it explicitly before deployment", key=key)
        return generated_secret

    logger.critical("Required environment secret is missing", key=key)
    raise ValueError(f"Required secret '{key}' is not set. The application cannot start without it.")


def generate_strong_secret(length_bytes: int = 32) -> str:
    """Generate a cryptographically secure hexadecimal secret for operator provisioning."""
    return secrets.token_hex(length_bytes)


def validate_secrets() -> None:
    """Validate critical secret presence and strength without emitting their values."""
    is_strict = _is_strict_environment()
    for key in CRITICAL_SECRET_KEYS:
        value = os.getenv(key)
        if not value:
            if is_strict:
                logger.critical("Required environment secret is missing", key=key)
                raise ValueError(f"Required environment secret '{key}' is missing.")
            os.environ[key] = generate_strong_secret()
            logger.warning("Generated a temporary development secret; configure it explicitly before deployment", key=key)
            continue

        if value.lower() in INSECURE_SECRET_VALUES or "changeme" in value.lower():
            message = f"Secret '{key}' uses a known insecure default."
            if is_strict:
                logger.critical("Security audit failed due to insecure configured secret", key=key)
                raise ValueError(message)
            logger.warning("Insecure configured secret detected in non-production environment", key=key)
            continue

        if key in {"DB_PASSWORD", "NEO4J_PASSWORD"} and len(value) < 8:
            message = f"Password '{key}' must be at least 8 characters."
            if is_strict:
                raise ValueError(message)
            logger.warning("Short development password detected", key=key)
        elif key == "JWT_SECRET_KEY" and len(value) < 32:
            message = "JWT_SECRET_KEY must be at least 32 characters."
            if is_strict:
                raise ValueError(message)
            logger.warning("Short development JWT secret detected", key=key)

    logger.info("Startup secret validation completed")
